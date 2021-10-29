import h5py
from mpi4py import MPI
import numpy as np
import logging
import psana
import yaml
from scipy.optimize import curve_fit
from argparse import ArgumentParser
import json
import os
import sys
import time
from bokeh.plotting import figure, show, output_file
from bokeh.models import Span, Legend, LegendItem, ColorBar, LinearColorMapper
from bokeh.io import output_notebook
import panel as pn
import matplotlib.pyplot as plt
from pathlib import Path

fpath=os.path.dirname(os.path.abspath(__file__))
fpathup = '/'.join(fpath.split('/')[:-1])
sys.path.append(fpathup)
print(fpathup)
from utils import get_r_masks, get_evr_w_codes 

# Need to go to stdout for arp/sbatch
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

JT_LOC = str(Path(__file__).resolve().parent.parent)
SD_LOC = '/reg/d/psdm/'
FFB_LOC = '/cds/data/drpsrcf/'

#def get_r_masks(shape, bins=100):
#    """Function to generate radial masks for pixels to include in azav"""
#    center = (shape[1] / 2, shape[0] / 2)
#    x, y = np.meshgrid(np.arange(shape[1]) - center[0], \
#        np.arange(shape[0]) - center[1])
#    r = np.sqrt(x**2 + y**2)
#    max_r = np.max(r)
#    min_r = np.min(r)
#    bin_size = (max_r - min_r) / bins
#    radii = np.arange(1, max_r, bin_size)
#    masks = []
#    for i in radii:
#        mask = (np.greater(r, i - bin_size) & np.less(r, i + bin_size))
#        masks.append(mask)
#
#    return masks

def gaussian(x, a, mean, std, m, b):
    """
    Equation for gaussian with linear component

    Parameters
    ----------
    x : float
        X-coordinate.

    a : float
        Amplitude of Gaussian.

    mean : float
        Mean of Gaussian.

    std : float
        Standard deviation of Gaussian.

    m : float
        Slope of linear baseline.

    b : float
        Y-intercept of linear baseline.

    Returns
    -------
    y : float
        The y-coordinate for the given x-coordinate as defined by the
        parameters given for the Gaussian on a slope with offset.
    """
    return (a * np.exp(-((x - mean) / 2 / std) ** 2)) + (m * x + b)

def fit_line(ave_azav, fit_points=5):
    """
    Fit the line from edges of array
    
    Parameters
    ----------
    ave_azav: ndarray
        The average azimuthal average from calibration data 1D array of floats.

    fit_points: int (Default: 5)
        Number of points at each end of average azimuthal average to fit.

    Returns
    -------
    m: float
        slope of the fit
    
    b: float
        y intercept of fit
    """
    azav_len = len(ave_azav)
    x0 = fit_points / 2
    x1 = azav_len - (fit_points / 2)
    y0 = np.mean(ave_azav[:fit_points])
    y1 = np.mean(ave_azav[azav_len - fit_points:])
    m, b = np.polyfit((x0, x1), (y0, y1), 1)

    return m, b

def peak_lr(array_data, threshold=0.1, bins=50):
    """Find max of normal distribution from histogram, 
    search right and left until population falls below threshold, 
    will run into problems with bimodal distribution.  This is naive,
    look at KDE

    Parameters
    ----------
    array_data: array like
        1D array data to cut on
    
    threshold: float
        percent of max population to throw out.  Upper/lower

    bins: int
        Number of bins to generate for histogram we cut on

    Returns
    -------
    hist: np.histogram
        Histogram from array_data and bins

    i0_low: float
        lower i0 value of cut on histogram

    i0_high: float
        upper i0 value of cut on histogram

    i0_med: float
        median i0 value
    """
    hist_all, edges_all = np.histogram(array_data, bins=bins)
    # avoid cases where there are a lot of 0 intensity shots (peak at 0)
    hist = hist_all[1:]
    edges = edges_all[1:]

    # Find peak information
    peak_val = hist.max()
    peak_idx = np.where(hist == peak_val)[0][0]
    i0_med = edges[peak_idx]

    #search right
    right = np.argmax(hist[peak_idx:] < threshold * peak_val)
    right += peak_idx
    i0_high = edges[right]

    # search left
    left_array = hist[:peak_idx]
    left = peak_idx - np.argmax(left_array[::-1] < threshold * peak_val)
    # ugly way to capture cases where the i0 does not drop to the threshold value on the left
    if left==peak_idx:
        print('New threshold: i0_med/2')
        threshold = peak_val/2
        left = peak_idx - np.argmax(left_array[::-1] < threshold)
    i0_low = edges[left]

    return hist_all, edges_all, i0_low, i0_high, i0_med

def calc_azav_peak(ave_azav):
    """
    Get the peak from the gaussian fit with linear offset, if this
    fails, just use the max value.  This could also use KDE.

    Parameters
    ----------
    ave_azav: ndarray
        radially binned average azimuthal intensity from used curves

    Returns
    -------
    peak: int
        index of the bin with the peak intensity
    """
    azav_len = len(ave_azav)
    # Fit the gaussian with line offset, fails for skewed gaussian
    m, b = fit_line(ave_azav)
    x = np.arange(azav_len)
    mean = np.sum(x * ave_azav) / np.sum(ave_azav)
    std = np.sqrt(np.sum((x - mean) ** 2 / azav_len))

    # Try to get the peak from fit
    try:
        # Guass/w line args
        p0 = [max(ave_azav), mean, std, m, b]
        popt, _ = curve_fit(gaussian, x, ave_azav, p0=p0)
        peak = int(round(popt[1]))
    except Exception as e:
        logger.info('Failed to fit Gaussian, using peak')
        peak = np.argmax(ave_azav)

    return peak

def get_integrated_intensity(ave_azav, peak_bin, delta_bin=3):
    """
    Get the average integrated intensity.  Sum the bin values from
    the peak bin to delta bin on each side.

    Parameters
    ----------
    ave_azav: ndarray
        radially binned average azimuthal intensity from used curves

    peak_bin: int
        peak radial bin

    delta_bin: int
        number of bins on each side of peak to include in sum

    Returns
    -------
    integrated_intensity: float
        the calculated integrated intensity
    """
    low = peak_bin - delta_bin
    high = peak_bin + delta_bin
    integrated_intensity = ave_azav[low: high].sum(axis=0)

    return integrated_intensity

def fit_limits(i0_data, peak_vals, i_low, i_high, bins=100):
    """
    Get the line fit and standard deviation of the plot of i0 
    vs int_intensities.  This will give information about
    distribution of integrated intensities for given i0 values
    
    Parameters
    ----------
    i0_data: ndarray
        Values of incoming intensities used in calibration

    peak_vals: ndarray
        Values of the integrated intensities corrspeconding to i0 values

    """
    m, b = np.polyfit(i0_data, peak_vals, 1)
    x = np.linspace(i_low, i_high, bins)
    sigma = np.std(peak_vals)
    y = x * m + b

    return x, y, m, b, sigma

          ###### Bokeh Figures #######

def peak_fig(signal, hist, edges, med, low, high):
    """General histogram plotter with peak location and 
    left/right limits plotted"""
    fig = figure(
        title='Used Intensity Distribution for {0}. \
            Low/Hi: {1}/{2}'.format(signal, low, high),
        x_axis_label='Intensity Values',
        y_axis_label='Counts'
    )
    fig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:])
    left_line = Span(location=low, dimension='height', \
        line_color='black')
    right_line = Span(location=high, dimension='height', \
        line_color='black')
    peak_line = Span(location=med, dimension='height', \
        line_color='red')
    fig.renderers.extend([left_line, right_line, peak_line])

    return fig

def azav_fig(ave_azav, peak, intensity, delta_bin):
    """Generate the azav fig for html file"""
    x_vals = np.arange(len(ave_azav))
    fig = figure(
        title='Average Azimuthal Binned Array: Center - {0}, \
            min/max - {1}/{2}, intensity - {3}'.format(peak, \
            peak-delta_bin, peak+delta_bin, round(intensity, 2)),
        x_axis_label='Bins',
        y_axis_label='Intensity',
    )

    peak_line = Span(location=peak, dimension='height', \
        line_color='green', line_width=2)
    lower_line = Span(location=peak-delta_bin, dimension='height', \
        line_color='black')
    upper_line = Span(location=peak+delta_bin, dimension='height', \
        line_color='black')
    ave_azav_curve = fig.scatter(x_vals, ave_azav)
    fig.renderers.extend([peak_line, lower_line, upper_line])

    azav_legend = Legend(items=[
        LegendItem(label='Azimuthal Average', renderers=[ave_azav_curve])
    ])
    fig.add_layout(azav_legend)

    return fig

def intensity_hist(intensity_hist, edges):
    fig = figure(
            title='Intensity Histogram'
    )
    fig.quad(top=intensity_hist, bottom=0, left=edges[:-1], right=edges[1:])

    return fig

def intensity_vs_peak_fig(intensity, peak_vals, x, y, slope, intercept, sigma):
    """Simple plot of intensity vs peak value"""
    fig = figure(
        title='Peak value vs Intensity. Slope = {0}, Intercept = {1}'.\
            format(round(slope, 2), round(intercept, 2)),
        x_axis_label='Intensity Monitor Value',
        y_axis_label='Peak Values'
    )
    fig.x_range.range_padding = fig.y_range.range_padding = 0
    h, y_edge, x_edge = np.histogram2d(peak_vals, intensity, bins=100)
    fig.image(image=[h], x=x_edge[0], y=y_edge[0], dh=y_edge[-1]-y_edge[0], \
        dw=x_edge[-1]-x_edge[0], palette="Spectral11")
    color_mapper = LinearColorMapper(palette="Spectral11", low=h.min(), high=h.max())
    color_bar = ColorBar(color_mapper=color_mapper, location=(0,0))
    fig.xaxis.bounds = [i0_low, i0_high]
    fig.add_layout(color_bar, 'right')
    fig.line(x, y, color='red')
    fig.line(x, y - 1 * sigma, color='orange')
    fig.line(x, y + 1 * sigma, color='orange')
    return fig

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--cfg', type=str, \
        default=(''.join([JT_LOC, 'jt_configs/xcs_config.yml'])))
    parser.add_argument('--run', type=int, default=None)
    args = parser.parse_args()

    # Start spinning up processes
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # All useful information should come from the config file
    # This will be source of truth for starting point for each hutch for now
    # Can definitely be cleaned up/use environment variables for arp exp/run
    with open(args.cfg) as f:
        yml_dict = yaml.load(f, Loader=yaml.FullLoader)
        det_map = yml_dict['det_map']
        ipm_name = yml_dict['ipm']['name']
        ipm_det = yml_dict['ipm']['det']
        jet_cam_name = yml_dict['jet_cam']['name']
        jet_cam_axis = yml_dict['jet_cam']['axis']
        hutch = yml_dict['hutch']
        exp = os.environ.get('EXPERIMENT', yml_dict['experiment'])
        run = os.environ.get('RUN_NUM', args.run)
        if run=='None':
            run = yml_dict['run']
        cal_params = yml_dict['cal_params']
        ffb = yml_dict['ffb']
        event_code = yml_dict['event_code']

    # Get Events for each worker
    num_events = int(cal_params['events'] / size)

    # Setup MPI data source
    ds_name = ''.join(['exp=', exp, ':run=', run, ':smd'])
    if ffb:
        ds_name += ':dir=/cds/data/drpsrcf/{}/{}/xtc'.format(hutch, exp)
    try:
        print('Make datasource with {}'.format(ds_name))
        ds = psana.MPIDataSource(ds_name)
    except Exception as e:
        logger.warning('Could not use MPI Data Source: {}'.format(e))
        sys.exit()

    # Setup smd saver
    jt_file = 'run{}_jt_cal.h5'.format(run)
    if ffb:
        jt_file_path = ''.join([FFB_LOC, hutch, '/', exp, '/scratch/', jt_file])
    else:
        jt_file_path = ''.join([SD_LOC, hutch, '/', exp, '/scratch/', jt_file])
    if rank == 0:
        logger.info('Will save small data to {}'.format(jt_file_path))
    smd = ds.small_data(jt_file_path, gather_interval=100)

    # Get the detectors from the config
    try:
        detector = psana.Detector(det_map['name'])
        ipm = psana.Detector(ipm_name)
        jet_cam = psana.Detector(jet_cam_name)
        evr = get_evr_w_codes(psana.DetNames())
        masks = get_r_masks(det_map['shape'], cal_params['azav_bins'])
    except Exception as e:
        logger.warning('Unable to create psana detectors: {}'.format(e))
        sys.exit()

    if rank == 0:
        logger.info('Gathering small data for exp: {}, run: {}, events: {}'.format(exp, run, cal_params['events']))
        logger.info('Detectors Available: {}'.format(psana.DetNames()))

    # Iterate through and pull out small data
    for evt_idx, evt in enumerate(ds.events()):
        if evt_idx%50==0:
            print('Event: {}'.format(evt_idx))
        try:
            if event_code not in evr.eventCodes(evt):
                    continue
            # Get image and azav
            calib = detector.calib(evt)
            det_image = detector.image(evt, calib)
            azav = np.array([np.mean(det_image[mask]) for mask in masks])
            
            # Get i0 Data this is different for differe ipm detectors
            # Be nice not to waste cycles on getattr at some point
            i0_data = getattr(ipm.get(evt), ipm_det)()
            
            # Get jet projection and location
            if not plt.get_backend()=='agg':
                if evt_idx == 5:
                    plt.imshow(jet_cam.image(evt))
                    plt.show()
                    plt.plot(jet_cam.image(evt).sum(axis=jet_cam_axis))
                    plt.show()
            jet_proj = jet_cam.image(evt).sum(axis=jet_cam_axis)
            max_jet_val = np.amax(jet_proj)
            max_jet_idx = np.where(jet_proj==max_jet_val)[0][0]
            smd.event(azav=azav, i0=i0_data, jet_peak=max_jet_val, jet_loc=max_jet_idx)
        except Exception as e:
            logger.info('Unable to process event {}: {}'.format(evt_idx, e))

        if evt_idx == num_events:
            break
    
    smd.save()
    if rank == 0:
        while not os.path.exists(jt_file_path):
            time.sleep(0.1)
        logger.info('Saved Small Data, Processing...')

        f = h5py.File(jt_file_path, 'r')
        i0_data = np.array(f['i0'])
        azav_data = np.array(f['azav'])
        jet_loc = np.array(f['jet_loc'])
        jet_peak = np.array(f['jet_peak'])
    
        # Find I0 distribution and filter out unused values
        i0_data = np.array(i0_data)
        i0_hist, edges, i0_low, i0_high, i0_med = peak_lr(i0_data)
        i0_idxs = np.where((i0_data > i0_low) & (i0_data < i0_high))
        i0_data_use = i0_data[i0_idxs]
   
        jet_loc_use = jet_loc[i0_idxs]
        jet_loc_mean = np.mean(jet_loc_use)
        jet_loc_std = np.std(jet_loc_use)
        jet_peak_use = jet_peak[i0_idxs]
        jet_peak_mean = np.mean(jet_peak_use)
        jet_peak_std = np.std(jet_peak_use)
 
        # Generate figure for i0 params
        p = peak_fig('{}'.format(ipm_name), i0_hist, edges, i0_med, i0_low, i0_high)

        # Get the azav value we'll use
        azav_use = [azav_data[idx] for idx in i0_idxs[0]]
        ave_azav = np.array((np.sum(azav_use, axis=0)) / len(azav_use))
        # Find the peak bin from average azav values
        peak_bin = calc_azav_peak(ave_azav)

        # Get the integrated intensity and generate fig
        integrated_intensity = get_integrated_intensity(ave_azav, peak_bin, cal_params['delta_bin'])
        int_hist, int_edges, int_low, int_high, int_med = peak_lr(integrated_intensity)
        p1 = azav_fig(ave_azav, peak_bin, integrated_intensity, cal_params['delta_bin'])

        # Go back through indices and find peak values for all the intensities
        low_bin = peak_bin - cal_params['delta_bin']
        high_bin = peak_bin + cal_params['delta_bin']
        peak_vals = [azav[low_bin:high_bin].sum(axis=0) for azav in azav_use]
        # Now fit I0 vs diffraction intensities
        x, y, slope, intercept, sigma = fit_limits(i0_data_use, peak_vals, i0_low, i0_high)
        p2 = intensity_vs_peak_fig(i0_data_use, peak_vals, x, y, slope, intercept, sigma)

        # Ratio information
        ratios = peak_vals / i0_data_use
        mean_ratio = np.mean(ratios)
        med_ratio = np.median(ratios)
        std_ratio = np.std(ratios)

        # Accumulate results
        results = {
            'i0_low': i0_low,
            'i0_high': i0_high,
            'i0_median': i0_med,
            'int_low': int_low,
            'int_high': int_high,
            'int_median': int_med,
            'peak_bin': peak_bin,
            'delta_bin': cal_params['delta_bin'],
            'mean_ratio': mean_ratio,
            'med_ratio': med_ratio,
            'std_ratio': std_ratio,
            'jet_location_mean': jet_loc_mean,
            'jet_location_std': jet_loc_std,
            'jet_peak_mean': jet_peak_mean,
            'jet_peak_std': jet_peak_std
        }

        logger.info('Results: {}'.format(results))

        # Set report directory
        results_dir = ''.join([SD_LOC, hutch, '/', exp, '/stats/summary/jt_cal_run_', run])

        # Get calib dir for meta data saving
        calib_dir = ''.join([SD_LOC, hutch, '/', exp, '/calib/jt_results/'])

        if not os.path.isdir(results_dir):
            logger.info('Creating Path {}'.format(results_dir))
            os.makedirs(results_dir)

        if not os.path.isdir(calib_dir):
            logger.info('Creating Path {}'.format(calib_dir))
            os.makedirs(calib_dir)

        # Write metadata to file
        res_file = ''.join([calib_dir, '/jt_cal_', run, '_results'])
        with open(res_file, 'w') as f:
            results = {k: str(v) for k, v in results.items()}
            json.dump(results, f)
        logger.info('Saved calibration to {}'.format(res_file))
        
        # try to also save calib results to exp directory in hutch opr home 
        # (only works if ran as hutchopr)
        hopr_dir = '/cds/home/opr/{}opr/experiments/{}/jt_calib'.format(hutch, exp)
        try:
            if not os.path.exists(hopr_dir):
                os.mkdir(hopr_dir)
            res_file = ''.join([hopr_dir, '/jt_cal_', run, '_results'])
            with open(res_file, 'w') as f:
                results = {k: str(v) for k, v in results.items()}
                json.dump(results, f)
            logger.info('Saved calibration to {}'.format(res_file))
        except Exception as e:
            logger.warning('Unable to write to {}opr experiment directory: {}'.format(hutch, e))

        # Accumulate plots and write report
        gspec = pn.GridSpec(sizing_mode='stretch_both', name='JT Cal Results: Run {}'.format(run))
        gspec[0:3, 0:3] = p
        gspec[4:6, 0:3] = p1
        gspec[7:12, 0:3] = p2
        tabs = pn.Tabs(gspec)

        report_file = ''.join([results_dir, '/report.html'])
        logger.info('Saving report to {}'.format(report_file))
        tabs.save(report_file)

        logger.info('finished with jet tracking calibration')
