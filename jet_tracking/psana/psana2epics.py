import sys
import time
import argparse

import numpy as np
import pandas as pd
from epics import PV
from scipy.signal import periodogram, peak_widths


time0 = time.time()


def initArgs():
    """Initialize argparse arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--calc_streak", action="store_true", default=False,
                        help='Calculate streak')
    parser.add_argument("--calc_period", action="store_true", default=False,
                        help='Calculate periodogram')
    parser.add_argument("--plot", action="store_true", default=False,
                        help='Plot normalized spectrum')
    parser.add_argument("--nevents", type=int, default=10,
                        help='Number of events to average')
    parser.add_argument("--exp", type=str, default='cxilr6716',
                        help='Experiment')
    parser.add_argument("--run", type=int,
                        help='Run')
    parser.add_argument("--instrument", type=str, default='cxi',
                        help='Instrument')
    parser.add_argument("--pvbase", type=str, default='CXI:SC1:DIFFRACT',
                        help='pvbase')
    parser.add_argument("--alias", type=str, default='DscCsPad',
                        help='detector alias')
    return parser.parse_args()


def DataSource(exp=None, run=None, **kwargs):
    """
    Wrapper for loading PyDataSource DataSource
    """
    import PyDataSource
    if exp and run:
        print('Loading DataSource for {:} run {:}'.format(exp, run))
        ds = PyDataSource.DataSource(exp=exp, run=int(run))
    elif exp:
        print('Loading DataSource for shared memory with expiment {:}'
              ''.format(exp))
        ds = PyDataSource.DataSource(exp=exp)
    else:
        print('Loading DataSource for shared memory')
        ds = PyDataSource.DataSource()

    print(ds.configData.show_info())
    print('')
    print('Load time: {:} sec'.format(time.time() - time0))
    return ds


def output_cspad_sum(ds=None, alias='DscCsPad',
                     pvbase='CXI:SC1:DIFFRACT', calc_period=True, calc_streak=False,
                     psd_events=None, psd_rate=None, psd_resolution=None, **kwargs):
    """Outputs cspad sum and certain statistics as PVs

    Parameters
    ----------
    ds : DataSource, optional
        DataSource object, if not specified, loads it using kwargs
    alias : str, optional
        Name for CsPad data
    pvbase : str, optional
        Base for PV names
    calc_period : bool, optional
        Determines the execution of frequency analysis
    psd_events : int, optional
        Number of events for frequency analysis, default is 240
    psd_rate : int or float, optional
        Event rate [Hz], default is 120
    psd_resolution : int, optional
        Resolution setting will perform rolling mean [Hz]
    """

    # Configure epics PVs
    print('Initializing epics PVs')
    cspad_sum_pv = PV(':'.join([pvbase, 'TOTAL_ADU']))
    streak_fraction_pv = PV(':'.join([pvbase, 'STREAK_FRACTION']))
    stats_mean_pv = PV(':'.join([pvbase, 'STATS_MEAN']))
    stats_std_pv = PV(':'.join([pvbase, 'STATS_STD']))
    stats_min_pv = PV(':'.join([pvbase, 'STATS_MIN']))
    stats_max_pv = PV(':'.join([pvbase, 'STATS_MAX']))
    psd_frequency_pv = PV(':'.join([pvbase, 'PSD_FREQUENCY']))
    psd_amplitude_pv = PV(':'.join([pvbase, 'PSD_AMPLITUDE']))
    psd_rate_pv = PV(':'.join([pvbase, 'PSD_RATE']))
    psd_events_pv = PV(':'.join([pvbase, 'PSD_EVENTS']))
    psd_resolution_pv = PV(':'.join([pvbase, 'PSD_RESOLUTION']))
    psd_freq_min_pv = PV(':'.join([pvbase, 'PSD_FREQ_MIN']))
    psd_freq_wf_pv = PV(':'.join([pvbase, 'PSD_FREQ_WF']))
    psd_amp_wf_pv = PV(':'.join([pvbase, 'PSD_AMP_WF']))
    # psd_amp_array_pv = PV(':'.join([pvbase,'PSD_AMP_ARRAY']))

    if psd_rate:
        psd_rate_pv.put(psd_rate)

    psd_rate = psd_rate_pv.get()
    if psd_rate > 360 or psd_rate < 10:
        psd_rate = 120.
        psd_rate_pv.put(psd_rate)

    if psd_events:
        psd_events_pv.put(psd_events)

    psd_events = psd_events_pv.get()
    if psd_events > 1200 or psd_events < 60:
        psd_events = psd_rate * 2.
        psd_events_pv.put(psd_events)

    if psd_resolution:
        psd_resolution_pv.put(psd_resolution)

    psd_resolution = psd_resolution_pv.get()
    if psd_resolution > 5 or psd_resolution < 0.1:
        psd_resolution = psd_rate / float(psd_events)
        psd_resolution_pv.put(psd_resolution)

    nroll = int(psd_resolution * psd_events / float(psd_rate))

    psd_freq_min = psd_freq_min_pv.get()
    if psd_freq_min > 40 or psd_freq_min < 2:
        psd_freq_min = 5.
        psd_freq_min_pv.put(psd_freq_min)

    if0 = int(psd_freq_min / float(psd_rate) * psd_events)

    psd_freq_wf = np.arange(psd_events / 2. + 1.) * \
        float(psd_rate) / float(psd_events)
    psd_freq_wf_pv.put(psd_freq_wf)

    print('Events = {}'.format(psd_events))

    print('... done')

    if not ds:
        ds = DataSource(**kwargs)
    print('... done')

    detector = ds._detectors[alias]

    detector.next()
    detector.add.property(asic)
    detector.add.property(streak_present)
    try:
        no_streak = []
        iloop = 0
        icheck = 0
        streaks = 0
        time0 = time.time()
        time_last = time0
        sums = []
        # aPxx = []
        # atime = []
        while True:
            cspad_sum = detector.corr.sum()
            sums.append(cspad_sum)
            cspad_sum_pv.put(cspad_sum)
            if calc_streak:
                streak = detector.streak_present
                streaks += streak
                if not streak:
                    no_streak.append(iloop)

            iloop += 1
            icheck += 1
            if not iloop % psd_events:
                sums = np.asarray(sums)
                det_avg = sums.mean()
                det_std = sums.std()
                det_max = sums.max()
                det_min = sums.min()
                stats_mean_pv.put(det_avg)
                stats_max_pv.put(det_max)
                stats_min_pv.put(det_min)
                stats_std_pv.put(det_std)

                if calc_period:
                    # f should be same as psd_freq_wf
                    f, Pxx = periodogram(sums, psd_rate)
                    if nroll > 1:
                        Pxx = pd.DataFrame(Pxx).rolling(
                            nroll).mean().values[nroll:, 0]
                        f = f[nroll:]
                    psd_frequency = f[Pxx[if0:].argmax() + if0]
                    psd_amplitude = Pxx[if0:].max() / 4 * psd_rate / psd_events
                    psd_frequency_pv.put(psd_frequency)
                    psd_amplitude_pv.put(psd_amplitude)
                    psd_amp_wf_pv.put(Pxx)
                    time_next = time.time()
                    evtrate = icheck / (time_next - time_last)
                    icheck = 0
                    time_last = time_next
                    print('{:8.1f} Hz - {:8.1f} {:12} {:12} {:12}'
                          ''.format(evtrate, psd_frequency, psd_amplitude,
                                    det_avg, det_std))
#
#                   Need to makd sure right shape before outputting array
#                   aPxx.append(Pxx)
#                   psd_amp_array_pv.put(np.asarray(aPxx))

                if calc_streak:
                    streak_fraction = streaks / psd_events
                    streak_fraction_pv.put(streak_fraction)

                sums = []
                # aPxx = []
                # atime = []
                streaks = 0
                no_streak = []

            # Change to evt.next() in future and count damage
            detector.next()

    except KeyboardInterrupt:
        return
    except Exception as e:
        print(e)


def output_cspad_streak(ds=None, alias='DscCsPad',
                        pvbase='CXI:SC1:DIFFRACT', nevents=10, **kwargs):
    """
    Output cspad jet streak information
    """

    beam_x_pv = PV(':'.join([pvbase, 'X0']))
    beam_y_pv = PV(':'.join([pvbase, 'Y0']))
    streak_angle_pv = PV(':'.join([pvbase, 'STREAK_PHI']))
    streak_intensity_pv = PV(':'.join([pvbase, 'STREAK_INTENSITY']))
    streak_width_pv = PV(':'.join([pvbase, 'STREAK_WIDTH']))
    if not ds:
        ds = DataSource(**kwargs)

# Now set in epics -- update as needed from epics.
#    beam_x_pv.put(2094.9301668334006) # run 104
#    beam_y_pv.put(-1796.5697333657126)

    detector = ds._detectors[alias]
    detector.next()

    detector.add.property(asic)
    cy, cx = get_center(detector, beam_x_pv, beam_y_pv)
    j_map_1, j_map_2 = find_proj_mapping(cy, cx)
    detector.add.parameter(proj_map_1=j_map_1, proj_map_2=j_map_2)
    detector.add.property(streak_angle_raw)
    detector.add.property(streak_present)
    try:
        iloop = 0
        time0 = time.time()
        while True:
            streak_angle = detector.streak_angle_raw[0]
            streak_intensity = detector.streak_angle_raw[1]
            streak_width = detector.streak_angle_raw[2]
            streak_angle_pv.put(streak_angle)
            streak_intensity_pv.put(streak_intensity)
            streak_width_pv.put(streak_width)
            if not (iloop + 1) % nevents and detector.streak_present:
                evt_rate = iloop / (time.time() - time0)
                print('{:15} {:6.1f} Hz {:5.1f} {:5.1f} {:5.3f} {}'
                      ''.format(iloop, evt_rate, streak_angle,
                                streak_intensity, streak_width,
                                int(detector.streak_present)))
            iloop += 1
            detector.next()

    except KeyboardInterrupt:
        return


def streak_present(self):
    im1 = self.asic[0]
    im2 = self.asic[2]
    return streak_present_im(im1) and streak_present_im(im2)


def streak_present_im(im):
    '''im is 2D np-array'''
    s = im[-10:].sum(axis=0)
    s -= s.mean()
    s /= np.roll(s, 10 - s.argmax())[20:].std()
    return s.max() > 5


def get_center(self, x0_pv, y0_pv):
    center = (y0_pv.get(), x0_pv.get())
    cy, cx = get_center_coords(self, center)
    cy -= 185
    return cy, cx


def to_pad_coord(det, point, i):
    '''Point: (y,x)'''

    pad = [1, 9, 17, 25][i]
    origin = np.asarray(
        (det.calibData.coords_x[pad, 0, 0], det.calibData.coords_y[pad, 0, 0]))
    unit_y = ((det.calibData.coords_x[pad, 1, 0] - det.calibData.coords_x[pad, 0, 0]),
              (det.calibData.coords_y[pad, 1, 0] - det.calibData.coords_y[pad, 0, 0]))
    unit_x = ((det.calibData.coords_x[pad, 0, 1] - det.calibData.coords_x[pad, 0, 0]),
              (det.calibData.coords_y[pad, 0, 1] - det.calibData.coords_y[pad, 0, 0]))
    matrix = np.asarray([[unit_y[0], unit_x[0]], [unit_y[1], unit_x[1]]])
    pos = np.linalg.solve(matrix, np.asarray(point) - origin)
    return pos


def get_center_coords(det, center):
    cy = np.zeros(4)
    cx = np.zeros(4)
    for i in range(4):
        pos = to_pad_coord(det, center, i)
        cy[i], cx[i] = pos[0], pos[1]
    return cy, cx


def find_proj_mapping(cy, cx):
    sq = 0

    j_index_1 = np.zeros((100, 80), dtype=np.int64)
    j_index_2 = np.zeros((100, 80), dtype=np.int64)
    for a in range(-40, 40):
        ang = np.radians(float(a) / 2)
        for i in range(100):
            j = int(np.tan(ang) * (100 - i + cy[sq]) + cx[sq]) % 100
            j_index_1[i, a + 40] = j
            j = int(np.tan(ang) *
                    (100 - i + cy[(sq + 2) % 4]) + cx[(sq + 2) % 4]) % 100
            j_index_2[i, a + 40] = j
    return j_index_1, j_index_2


def asic(self, attr='corr'):
    """
    Select inner asics
    """
    return getattr(self, attr)[[1, 9, 17, 25], :, 0:194]


def streak_angle_raw(self):
    """
    Jet streak calculation
    Returns: jet angle, jet intensity (as standard deviations from the mean),
    jet width

    """
    sq = 0

    asic = self.asic
    im1 = asic[sq][-100:, :100]
    im2 = asic[(sq + 2) % 4][-100:, :100]
    proj1 = np.zeros((100, 80))
    proj2 = np.zeros((100, 80))
    for a in range(-40, 40):
        for i in range(im1.shape[0]):
            proj1[i, a + 40] = im1[i, self.proj_map_1[i, a + 40]]
            proj2[i, a + 40] = im2[i, self.proj_map_2[i, a + 40]]
    s = proj1.sum(axis=0) + proj2.sum(axis=0)
    s -= s.mean()
    s /= np.roll(s, 10 - s.argmax())[20:].std()
    peak = s[1:-1].argmax() + 1
    try:
        peakwidth = peak_widths(s, [peak])[0][0]
    except Exception as e:
        peakwidth = 5
    return (np.pi * (peak - 40) / 360.0, s.max(), peakwidth)


if __name__ == "__main__":
    args = initArgs()
    print('Initializing args: {}'.format(args))
    sys.exit(output_cspad_sum(alias=args.alias, pvbase=args.pvbase,
                              exp=args.exp, run=args.run,
                              calc_period=args.calc_period,
                              calc_streak=args.calc_streak,
                              nevents=args.nevents, plot=args.plot))
