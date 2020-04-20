from ophyd.areadetector.plugins import ImagePlugin, ROIPlugin, StatsPlugin
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal

from pcdsdevices.areadetector.detectors import PCDSAreaDetector
from pcdsdevices.component import UnrelatedComponent as UCpt


class Offaxis(PCDSAreaDetector):
    """
    Area detector for Offaxis camera in CXI.

    Parameters
    ----------
    port_names : str dict
        A dictionary containing the access port names for the plugins.

    prefix : str
        Prefix for the PV name of the camera.

    name : str
        Name of the camera.

    Attributes
    ----------
    ROI : ROIPlugin
        ROI on original rate image.

    ROI_stats : StatsPlugin
        Stats on ROI of original rate image.
    """

    ROI = UCpt(ROIPlugin)
    ROI_stats = UCpt(StatsPlugin)
    ROI_image = UCpt(ImagePlugin)

    # TODO: Figure out good default ROI_port
    def __init__(self, prefix, *, name, ROI_port=0, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)

        self.ROI_stats.nd_array_port.put(ROI_port)
        self.ROI_image.nd_array_port.put(ROI_port)
        self.ROI.enable.put('Enabled')
        self.ROI_stats.enable.put('Enabled')
        self.ROI_image.enable.put('Enabled')


class Questar(PCDSAreaDetector):
    """
    Area detector for Inline Questar Camera in CXI.

    Parameters
    ----------
    port_names : str dict
        A dictionary containing the access port names for the plugins.

    prefix : str
        Prefix for the PV name of the camera.

    name : str
        Name of the camera.

    Attributes
    ----------
    ROI : ROIPlugin
        ROI on original rate image.

    ROI_stats : StatsPlugin
        Stats on ROI of original rate image.
    """

    ROI = UCpt(ROIPlugin)
    ROI_stats = UCpt(StatsPlugin)
    ROI_image = UCpt(ImagePlugin)

    def __init__(self, prefix, *, name, ROI_port=0, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)

        self.ROI_stats.nd_array_port.put(ROI_port)
        self.ROI_image.nd_array_port.put(ROI_port)
        self.ROI.enable.put('Enabled')
        self.ROI_stats.enable.put('Enabled')
        self.ROI_image.enable.put('Enabled')


class Parameters(Device):
    """Contains EPICS PVs used for jet tracking."""
    cam_x = Cpt(EpicsSignal, ':CAM_X',
                doc='x-coordinate of camera position in mm')
    cam_y = Cpt(EpicsSignal, ':CAM_Y',
                doc='y-coordinate of camera position in mm')
    pxsize = Cpt(EpicsSignal, ':PXSIZE',
                 doc='size of pixel in mm')
    cam_roll = Cpt(EpicsSignal, ':CAM_ROLL',
                   doc='rotation of camera about z axis in radians')
    beam_x = Cpt(EpicsSignal, ':BEAM_X',
                 doc='x-coordinate of x-ray beam in mm (usually 0)')
    beam_y = Cpt(EpicsSignal, ':BEAM_Y',
                 doc='y-coordinate of x-ray beam in mm (usually 0)')
    beam_x_px = Cpt(EpicsSignal, ':BEAM_X_PX',
                    doc='x-coordinate of x-ray beam in camera image in pixels')
    beam_y_px = Cpt(EpicsSignal, ':BEAM_Y_PX',
                    doc='y-coordinate of x-ray beam in camera image in pixels')
    nozzle_x = Cpt(EpicsSignal, ':NOZZLE_X',
                   doc='x-coordinate of nozzle in mm')
    nozzle_y = Cpt(EpicsSignal, ':NOZZLE_Y',
                   doc='y-coordinate of nozzle in mm')
    nozzle_xwidth = Cpt(EpicsSignal, ':NOZZLE_XWIDTH',
                        doc='width of nozzle in mm')
    jet_x = Cpt(EpicsSignal, ':JET_X',
                doc='distance from sample jet to x-ray beam in mm')
    jet_roll = Cpt(EpicsSignal, ':JET_ROLL',
                   doc='rotation of sample jet about z axis in radians')
    state = Cpt(EpicsSignal, ':STATE',
                doc='dictionary of strings')
    jet_counter = Cpt(EpicsSignal, ':JET_Counter',
                      doc='Jet counter')
    jet_reprate = Cpt(EpicsSignal, ':JET_RepRate',
                      doc='Jet repetition rate')
    nozzle_counter = Cpt(EpicsSignal, ':NOZZLE_Counter',
                         doc='Nozzle counter')
    nozzle_reprate = Cpt(EpicsSignal, ':NOZZLE_RepRate',
                         doc='Nozzle repetition rate')
    mean = Cpt(EpicsSignal, ':ROI_mean',
               doc='mean of calibration ROI image with jet')
    std = Cpt(EpicsSignal, ':ROI_std',
              doc='standard devation of calibration ROI image with jet')
    radius = Cpt(EpicsSignal, ':RADIUS',
                 doc='radius of calibration diffraction ring')
    intensity = Cpt(EpicsSignal, ':INTENSITY',
                    doc='intensity of calibration diffraction ring')
    thresh_hi = Cpt(EpicsSignal, ':THRESH_hi',
                    doc='upper threshold for CSPAD ring intensity')
    thresh_lo = Cpt(EpicsSignal, ':THRESH_lo',
                    doc='lower threshold for CSPAD ring intensity')
    thresh_w8 = Cpt(EpicsSignal, ':THRESH_w8',
                    doc='threshold for wave8')
    thresh_cam = Cpt(EpicsSignal, ':THRESH_cam',
                     doc='threshold for camera-based jet tracking')
    bypass_cam = Cpt(EpicsSignal, ':BYPASS_cam',
                     doc='bypass camera during jet tracking')
    frames_cam = Cpt(EpicsSignal, ':FRAMES_cam',
                     doc='number of frames for integration for camera')
    frames_cspad = Cpt(EpicsSignal, ':FRAMES_cspad',
                       doc='number of frames for integration for cspad')


class OffaxisParams(Device):
    """Contains EPICS PVs used with Offaxis camera for jet tracking."""
    cam_z = Cpt(EpicsSignal, ':CAM_Z',
                doc='z-coordinate of camera position in mm')
    cam_y = Cpt(EpicsSignal, ':CAM_Y',
                doc='y-coordinate of camera position in mm')
    pxsize = Cpt(EpicsSignal, ':PXSIZE',
                 doc='size of pixel in mm')
    cam_pitch = Cpt(EpicsSignal, ':CAM_PITCH',
                    doc='rotation of camera about x axis in radians')
    beam_z = Cpt(EpicsSignal, ':BEAM_Z',
                 doc='z-coordinate of x-ray beam in mm (usually 0)')
    beam_y = Cpt(EpicsSignal, ':BEAM_Y',
                 doc='y-coordinate of x-ray beam in mm (usually 0)')
    beam_z_px = Cpt(EpicsSignal, ':BEAM_Z_PX',
                    doc='z-coordinate of x-ray beam in camera image in pixels')
    beam_y_px = Cpt(EpicsSignal, ':BEAM_Y_PX',
                    doc='y-coordinate of x-ray beam in camera image in pixels')
    nozzle_z = Cpt(EpicsSignal, ':NOZZLE_Z',
                   doc='z-coordinate of nozzle in mm')
    nozzle_y = Cpt(EpicsSignal, ':NOZZLE_Y',
                   doc='y-coordinate of nozzle in mm')
    nozzle_zwidth = Cpt(EpicsSignal, ':NOZZLE_ZWIDTH',
                        doc='width of nozzle in mm')
    jet_z = Cpt(EpicsSignal, ':JET_Z',
                doc='distance from sample jet to x-ray beam in mm')
    jet_pitch = Cpt(EpicsSignal, ':JET_PITCH',
                    doc='rotation of sample jet about z axis in radians')
    state = Cpt(EpicsSignal, ':STATE',
                doc='dictionary of strings')
    jet_counter = Cpt(EpicsSignal, ':JET_Counter',
                      doc='Jet counter')
    jet_reprate = Cpt(EpicsSignal, ':JET_RepRate',
                      doc='Jet repetition rate')
    nozzle_counter = Cpt(EpicsSignal, ':NOZZLE_Counter',
                         doc='Nozzle counter')
    nozzle_reprate = Cpt(EpicsSignal, ':NOZZLE_RepRate',
                         doc='Nozzle repetition rate')
    mean = Cpt(EpicsSignal, ':ROI_mean',
               doc='mean of calibration ROI image with jet')
    std = Cpt(EpicsSignal, ':ROI_std',
              doc='standard devation of calibration ROI image with jet')
    radius = Cpt(EpicsSignal, ':RADIUS',
                 doc='radius of calibration diffraction ring')
    intensity = Cpt(EpicsSignal, ':INTENSITY',
                    doc='intensity of calibration diffraction ring')
    thresh_hi = Cpt(EpicsSignal, ':THRESH_hi',
                    doc='upper threshold for CSPAD ring intensity')
    thresh_lo = Cpt(EpicsSignal, ':THRESH_lo',
                    doc='lower threshold for CSPAD ring intensity')
    thresh_w8 = Cpt(EpicsSignal, ':THRESH_w8',
                    doc='threshold for wave8')
    thresh_cam = Cpt(EpicsSignal, ':THRESH_cam',
                     doc='threshold for camera-based jet tracking')
    bypass_cam = Cpt(EpicsSignal, ':BYPASS_cam',
                     doc='bypass camera during jet tracking')
    frames_cam = Cpt(EpicsSignal, ':FRAMES_cam',
                     doc='number of frames for integration for camera')
    frames_cspad = Cpt(EpicsSignal, ':FRAMES_cspad',
                       doc='number of frames for integration for cspad')


class Control(Device):
    """Contains EPICS PVs used for jet tracking control."""
    re_state = Cpt(EpicsSignal, ':RE:STATE')
    beam_state = Cpt(EpicsSignal, ':BEAM:STATE')
    injector_state = Cpt(EpicsSignal, ':INJECTOR:STATE')
    beam_trans = Cpt(EpicsSignal, ':BEAM:TRANS')
    beam_pulse_energy = Cpt(EpicsSignal, ':BEAM:PULSE_ENERGY')
    beam_e_thresh = Cpt(EpicsSignal, ':BEAM:E_THRESH')
    xstep_size = Cpt(EpicsSignal, ':INJECTOR:XSTEP_SIZE')
    xscan_min = Cpt(EpicsSignal, ':INJECTOR:XSCAN_MIN')
    xscan_max = Cpt(EpicsSignal, ':INJECTOR:XSCAN_MAX')
    bounce_width = Cpt(EpicsSignal, ':INJECTOR:BOUNCE_WIDTH')
    xmin = Cpt(EpicsSignal, ':INJECTOR:XMIN')
    xmax = Cpt(EpicsSignal, ':INJECTOR:XMAX')


class Diffract(Device):
    """
    Contains EPICS PVs used for shared memory X-ray Diffraction detector
    used in jet tracking.
    """
    total_counter = Cpt(EpicsSignal, ':TOTAL_Counter',
                        doc='Total counter')
    total_reprate = Cpt(EpicsSignal, ':TOTAL_RepRate',
                        doc='Diffraction total intensity calc rate')
    ring_counter = Cpt(EpicsSignal, ':RING_Counter',
                       doc='Diffraction ring intensity event counter')
    ring_reprate = Cpt(EpicsSignal, ':RING_RepRate',
                       doc='Diffraction ring intensity event counter')
    psd_counter = Cpt(EpicsSignal, ':PSD_Counter',
                      doc='Diffraction periodogram event counter')
    psd_reprate = Cpt(EpicsSignal, ':PSD_RepRate',
                      doc='Diffraction periodogram event counter')
    stats_counter = Cpt(EpicsSignal, ':STATS_Counter',
                        doc='Diffraction stats event counter')
    stats_reprate = Cpt(EpicsSignal, ':STATS_RepRate',
                        doc='Diffraction stats event counter')
    streak_counter = Cpt(EpicsSignal, ':STREAK_Counter',
                         doc='Diffraction streak event counter')
    streak_reprate = Cpt(EpicsSignal, ':STREAK_RepRate',
                         doc='Diffraction streak event counter')
    cspad_sum = Cpt(EpicsSignal, ':TOTAL_ADU',
                    doc='Total detector ADU')
    streak_fraction = Cpt(EpicsSignal, ':STREAK_FRACTION',
                          doc='Fraction of events with diffraction streak')
    stats_mean = Cpt(EpicsSignal, ':STATS_MEAN',
                     doc='Mean Diffraction Statistic')
    stats_std = Cpt(EpicsSignal, ':STATS_STD',
                    doc='Std Diffraction Statistic')
    stats_min = Cpt(EpicsSignal, ':STATS_MIN',
                    doc='Min Diffraction Statistic')
    stats_max = Cpt(EpicsSignal, ':STATS_MAX',
                    doc='Max Diffraction Statistic')
    psd_frequency = Cpt(EpicsSignal, ':PSD_FREQUENCY',
                        doc='Diffraction periodogram fundamental frequency')
    psd_amplitude = Cpt(EpicsSignal, ':PSD_AMPLITUDE',
                        doc='Diffraction periodogram Frequency analysis'
                            'amplitude')
    psd_rate = Cpt(EpicsSignal, ':PSD_RATE',
                   doc='Event frequency for periodogram')
    psd_events = Cpt(EpicsSignal, ':PSD_EVENTS',
                     doc='Diffraction periodogram')
    psd_resolution = Cpt(EpicsSignal, ':PSD_RESOLUTION',
                         doc='Resultion to smooth over for periodogra')
    psd_freq_min = Cpt(EpicsSignal, ':PSD_FREQ_MIN',
                       doc='Minimum frequency for periodogram calcs')
    psd_amp_wf = Cpt(EpicsSignal, ':PSD_AMP_WF',
                     doc='Diffraction periodogram Frequency analysis waveform'
                         'array')
    psd_freq_wf = Cpt(EpicsSignal, ':PSD_FREQ_WF',
                      doc='Diffraction periodogram frequency waveform')
    psd_amp_array = Cpt(EpicsSignal, ':PSD_AMP_ARRAY',
                        doc='Diffraction periodogram Frequency analysis'
                            'amplitude array')
    state = Cpt(EpicsSignal, ':STATE',
                doc='State of diffraction analysis')


# classes used for jet tracking testing
class JTInput(Device):
    nframe = Cpt(EpicsSignal, ':NFRAME', doc='number of frames passed')
    i0 = Cpt(EpicsSignal, ':i0', doc='Wave8')
    evtcode = Cpt(EpicsSignal, ':EVTCODE', doc='event code')
    mtr = Cpt(EpicsSignal, ':MTR', doc='motor position')
    mtr_prec = Cpt(EpicsSignal, ':MTR_PREC', doc='motor precision')


class JTOutput(Device):
    nframe = Cpt(EpicsSignal, ':NFRAME', doc='number of frames used')
    det = Cpt(EpicsSignal, ':DET', doc='detector intensity')
    i0 = Cpt(EpicsSignal, ':I0', doc='Wave8')
    mtr = Cpt(EpicsSignal, ':MTR', doc='motor position')


class JTFake(Device):
    stopper = Cpt(EpicsSignal, ':STOPPER', doc='fake stopper')
    pulse_picker = Cpt(EpicsSignal, ':PP', doc='fake pulse picker')
