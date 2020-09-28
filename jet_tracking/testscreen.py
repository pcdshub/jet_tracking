from time import sleep

from pydm import Display
from qtpy.QtCore import QThread
from os import path
# from . import jet_control, jt_utils


class TrackThread(QThread):

    # def __init__(self, injector, camera, cspad, stopper, pulse_picker, wave8, params):
    # devices are not connected, use 'fake' PVs instead
    def __init__(self, jt_input, jt_output, jt_fake):
        super().__init__()

        ''' self.injector = injector
        self.camera = camera
        self.cspad = cspad
        self.stopper = stopper
        self.pulse_picker = pulse_picker
        self.wave8 = wave8
        self.params = params '''

        # devices are not connected, use 'fake' PVs instead
        self.jt_input = jt_input
        self.jt_output = jt_output
        self.jt_fake = jt_fake

    def run(self):
        while not self.isInterruptionRequested():
            # check if stopper is in
            ''' if (jt_utils.get_stopper(self.stopper) == 1): '''
            if (self.jt_fake.stopper.get() == 1):
                # if stopper is in, stop jet tracking
                print('Stopper in - TRACKING STOPPED')
                self.requestInterruption()
                continue

            # check if pulse picker is closed
            ''' if (jt_utils.get_pulse_picker(self.pulse_picker) == 1): '''
            if (self.jt_fake.pulse_picker.get() == 1):
                # if pulse picker is closed, stop jet tracking
                print('Pulse picker closed - TRACKING STOPPED')
                self.requestInterruption()
                continue

            # check wave8
            ''' if (jt_utils.get_wave8(self.wave8) < self.params.thresh_w8):
            if wave8 is below threshold, continue running jet tracking but do not move
            print('Wave8 below threshold - NOT TRACKING')
            sleep(2)
            continue '''

            # OR check number of frames passed? used during testing w/ 'fake' PVs
            # get nframes timestamp
            t_nframe = self.jt_output.nframe.get()[1]
            if (self.jt_output.nframe.get()[0] < self.jt_input.nframe.get() * 0.8):
                # if too few frames passed, continue running jet tracking but do not move
                print('Too few frames passed - NOT TRACKING')
                sleep(2)
                continue

            # check CSPAD
            # make sure nframes (or wave8, if that is what is used) timestamp
            # matches with CSPAD timestamp
            if (t_nframe != self.jt_output.det.get()[1]):
                # if the timetamps do not match try again
                continue

            ''' if (jt_utils.get_cspad(self.cspad) < self.params.thresh_lo): '''
            # params IOC is down, hardcode threshold
            if (self.jt_output.det.get()[0] < 0.45):
                # if CSPAD is below lower threshold, move jet
                ''' if (not self.params.bypass_camera()): '''
                # params IOC is down, hardcode bypass
                if (not False):
                    # if camera is not bypassed, check if there is a jet and location of jet
                    try:
                        '''jet_control._jet_calculate_step(self.camera, self.params)
                        # if jet is more than certain microns away from x-rays, move jet
                        # using camera feedback
                        if (self.params.jet_x.get() > self.params.thresh_cam):
                        jet_control._jet_move_step(self.injector, self.camera, self.params)
                        sleep(1) # change to however long it takes for jet to move
                        continue '''

                        # devices are not connected, print status message instead
                        print('Detector below lower threshold - MOVING JET')
                        sleep(1)  # change to however long it takes for jet to move
                        continue
                    except Exception:
                        # if jet is not detected, continue running jet tracking but do not move
                        print('Cannot find jet - NOT TRACKING')
                        sleep(2)
                        continue
            # if camera is bypassed or if jet is less than certain microns away from x-rays,
            # scan jet across x-rays to find new maximum
            ''' jet_control.scan(self.injector, self.cspad)
            intensity = jt_utils.get_cspad(azav, self.params.radius.get(), gas_detect)
            self.params.intensity.put(intensity) '''

            # devices are not connected, print status message instead
            print('Detector below lower threshold - SCANNING JET')
            sleep(1)  # change to however long it takes for jet to scan

            # if CSPAD still below upper threshold, stop jet tracking
            ''' if (get_cspad(self.cspad) < self.params.thresh_hi): '''
            # params IOC is down, hardcode threshold
            if (self.jt_output.det.get()[0] < 0.5):
                print('CSPAD below threshold - TRACKING STOPPED')
                self.requestInterruption()
                continue

            print('Running')
            print(self.jt_output.det.get())
            sleep(2)


# class for jet tracking PyDM display
class JetTrack(Display):

    def __init__(self, parent=None, args=None, macros=None):

        super(JetTrack, self).__init__(parent=parent,args=args, macros=macros)
        '''def __init__(self, injector, camera, cspad, stopper, pulse_picker, wave8,
                  params, macros, *args, **kwargs):'''
        '''def __init__(self, jt_input, jt_output, jt_fake, macros, *args, **kwargs):
        super().__init__(macros=macros, *args, **kwargs)'''

        '''self.track_thread = TrackThread(injector, camera, cspad, stoppper,
                                        pulse_picker, wave8, params)'''
        #self.track_thread = TrackThread(jt_input, jt_output, jt_fake)

        # connect GUI buttons to appropriate methods
        self.ui.calibrate_btn.clicked.connect(self.calibrate_clicked)
        self.ui.start_btn.clicked.connect(self.start_clicked)
        self.ui.stop_btn.clicked.connect(self.stop_clicked)

        self.ui.calibrate_btn.setEnabled(True)
        self.ui.start_btn.setEnabled(False)
        self.ui.stop_btn.setEnabled(False)

    def ui_filepath(self):
        return(path.join(path.dirname(path.realpath(__file__)), self.ui_filename()))

    def ui_filename(self):
        return 'jettracking.ui'

    def calibrate_clicked(self):
        self.ui.logger.write('Calibrating')
        self.ui.calibrate_btn.setEnabled(False)

        # call calibration method
        '''jet_control.calibrate(injector, camera, cspad, params)'''

        self.ui.logger.write('Calibration complete - can now run jet tracking')
        self.ui.calibrate_btn.setEnabled(True)
        self.ui.start_btn.setEnabled(True)
        return

    def start_clicked(self):
        """Starts new jet tracking thread when start button is clicked."""
        self.ui.logger.write('Running jet tracking')
        self.ui.start_btn.setEnabled(False)
        self.ui.stop_btn.setEnabled(True)
        self.ui.calibrate_btn.setEnabled(False)
        self.track_thread.start()

    def stop_clicked(self):
        """Stops jet tracking when stop button is clicked."""
        self.track_thread.requestInterruption()
        self.ui.logger.write('Jet tracking stopped')
        self.ui.stop_btn.setEnabled(False)
        self.ui.start_btn.setEnabled(True)
        self.ui.calibrate_btn.setEnabled(True)
