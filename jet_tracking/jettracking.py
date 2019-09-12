from qtpy.QtCore import QThread
from pydm import Display

import jt_utils
import jet_control
from time import sleep


class TrackThread(QThread):

  def __init__(self):
  # def __init__(self, injector, camera, cspad, stopper, pulse_picker, wave8, params):
    super().__init__()

    '''
    self.stopper = stopper
    self.pulse_picker = pulse_picker
    self.wave8 = wave8
    self.cspad = cspad
    self.camera = camera
    self.injector = injector
    self.params = params
    '''

  def run(self):
    while not self.isInterruptionRequested():
      
      '''
      # check devices first
      # check if stopper is in
      if (jt_utils.get_stopper(self.stopper) == 1):
        # if stopper is in, stop jet tracking
        print('Stopper in - TRACKING STOPPED')
        self.requestInterruption()
        continue

      # check if pulse picker is closed
      if (jt_utils.get_pulse_picker(self.pulse_picker) == 1):
        # if pulse picker is closed, stop jet tracking
        print('Pulse picker closed - TRACKING STOPPED')
        self.requestInterruption()
        continue

      # check wave8
      if (jt_utils.get_wave8(self.wave8) < self.params.thresh_w8):
        # if wave8 is below threshold, continue running jet tracking but do not move
        print('Wave8 below threshold - NOT TRACKING')
        continue

      # check CSPAD
      if (jt_utils.get_cspad(self.cspad) < self.params.thresh_lo):
        # if CSPAD is below lower threshold, move jet
        if (not self.params.bypass_camera()):
          # if camera is not bypassed, check if there is a jet and location of jet
          try:
            jet_control.jet_calculate_inline(self.camera, self.params)
            # if jet is more than certain microns away from x-rays, move jet using camera feedback
            if (self.params.jet_x.get() > 0.01):
              jet_control.jet_move_inline(self.injector, self.camera, self.params)
              continue
          except Exception:
            # if jet is not detected, continue running jet tracking but do not move
            print('Cannot find jet - NOT TRACKING')
            continue

        # if camera is bypassed or if jet is less than certain microns away from x-rays, scan jet across x-rays to find new maximum
        jet_control.scan(self.injector, self.cspad)
        intensity = jt_utils.get_cspad(azav, self.params.radius.get(), gas_det)
        self.params.intensity.put(intensity)

        # if CSPAD is still below upper threshold, stop jet tracking
        if (get_cspad(self.cspad) < self.params.thresh_hi):
          print('CSPAD below threshold - TRACKING STOPPED')
          self.requestInterruption()
    '''


class JetTrack(Display):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.track_thread = TrackThread()
    # self.track_thread = TrackThread(injector, camera, cspad, stopper, pulse_picker, wave8, params)

    # connect GUI buttons to appropriate methods
    self.ui.calibrate_btn.clicked.connect(self.calibrate_clicked)
    self.ui.start_btn.clicked.connect(self.start_clicked)
    self.ui.stop_btn.clicked.connect(self.stop_clicked)

    self.ui.calibrate_btn.setEnabled(True)
    self.ui.start_btn.setEnabled(False)
    self.ui.stop_btn.setEnabled(False)

  def ui_filename(self):
    '''
    Load ui file for GUI
    '''

    return 'jettracking.ui'

  def calibrate_clicked(self):
    '''
    Runs calibration method when calibrate button is clicked
    '''

    self.ui.logger.write('Calibrating')
    self.ui.calibrate_btn.setEnabled(False)
    #jet_control.calibrate(injector, camera, cspad, params)
    self.ui.logger.write('Calibration complete - can now run jet tracking')
    self.ui.calibrate_btn.setEnabled(True)
    # activate start button
    self.ui.start_btn.setEnabled(True)
    return

  def start_clicked(self):
    '''
    Starts new thread to run jet tracking in when start button is clicked
    '''

    self.ui.logger.write('Running jet tracking')
    self.ui.start_btn.setEnabled(False)
    self.ui.stop_btn.setEnabled(True)
    self.ui.calibrate_btn.setEnabled(False)
    self.track_thread.start()

  def stop_clicked(self):
    '''
    Stops jet tracking when stop button is clicked
    '''

    self.track_thread.requestInterruption()
    self.ui.logger.write('Jet tracking stopped')
    self.ui.stop_btn.setEnabled(False)
    self.ui.start_btn.setEnabled(True)
    self.ui.calibrate_btn.setEnabled(True)

