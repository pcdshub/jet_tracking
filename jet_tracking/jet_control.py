import numpy as np
from time import sleep

from . import cam_utils
from . import jt_utils
from .move_motor import movex


# import cam_utils
# import jt_utils
# from move_motor import movex

class JetControl:
    '''
    Jet tracking control class using jet_tracking methods
    '''

    def __init__(self, name,
                 injector, camera, params, diffract,
                 # camera_offaxis=None,
                 **kwargs):

        self.injector = injector
        self.camera = camera
        self.params = params
        self.diffract = diffract

    def set_beam(self, beamX, beamY):
        '''
        Set the coordinates for the x-ray beam

        Parameters
        ----------
        beamX_px : int
            x-coordinate of x-ray beam in the camera image in pixels
        beamY_px : int
            y-coordinate of x-ray beam in the camera image in pixels
        '''
        set_beam(beamX, beamY, self.params)

    def calibrate(self):
        '''
        Calibrate the onaxis camera
        '''
        calibrate(self.injector, self.camera, self.params)

    def jet_calculate(self):
        '''
        Track the sample jet and calculate the distance to the x-ray beam
        '''
        jet_calculate(self.camera, self.params)

    def jet_move(self):
        '''
        Move the sample jet to the x-ray beam
        '''
        jet_move(self.injector, self.camera, self.params)


def get_burst_avg(n, image_plugin):
    '''
    Get the average of n consecutive images from a camera

    Parameters
    ----------
    n : int
        number of consecutive images to be averaged
    image_plugin : ImagePlugin
        camera ImagePlugin from which the images will be taken

    Returns
    -------
    burst_avg : ndarray
        average image
    '''
    imageX, imageY = image_plugin.image.shape
    burst_imgs = np.empty((n, imageX, imageY))
    for x in range(n):
        burst_imgs[x] = image_plugin.image
    burst_avg = burst_imgs.mean(axis=0)

    return burst_avg


def set_beam(beamX_px, beamY_px, params):
    '''
    Set the coordinates for the x-ray beam

    Parameters
    ----------
    beamX_px : int
        x-coordinate of x-ray beam in the camera image in pixels
    beamY_px : int
        y-coordinate of x-ray beam in the camera image in pixels
    params : Parameters
        EPICS PVs used for recording jet tracking data
    '''
    params.beam_x_px.put(beamX_px)
    params.beam_y_px.put(beamY_px)


def calibrate(injector, camera, CSPAD, params, *, offaxis=False,
              delay=0.1):
    '''
    Calibrate the camera and CSPAD and determine parameters needed for
    jet tracking
    NEED TO CHECK offaxis calculation sign

    First set the ROI of the camera to show the proper jet and illumination.

    Determines the mean, standard deviation, jet position and tilt, pixel
    size, beam position, camera position and tilt

    Params determined if onaxis camera used: mean, std, pxsize, camX, camY,
    cam_roll, beamX_px, beamY_px, jet_roll

    Params determined if offaxis camera used: mean, std, pxsize, camY, camZ,
    cam_pitch, beamY_px, beamZ_px, jet_pitch

    Parameters
    ----------
    injector : Injector
        sample injector
    camera : Questar
        camera looking at sample jet and x-rays
    CSPAD : CSPAD
        CSPAD for data
    params : Parameters
        EPICS PVs used for recording jet tracking data
    delay : float, optional
        Additional settle time after moving the motor
    offaxis : bool, optional
        Camera is off-axis in y-z plane
    '''

    # find jet in camera ROI
    ROI_image = get_burst_avg(params.frames_cam.get(), camera.ROI_image)
    mean, std = cam_utils.image_stats(ROI_image)
    rho, theta = cam_utils.jet_detect(ROI_image, mean, std)
    params.mean.put(mean)
    params.std.put(std)

    # take calibration CSPAD data
    # get CSPAD and wave8 data
    azav, norm = get_azav(CSPAD) # call azimuthal average function
    r, i = jt_utils.fit_CSPAD(azav, norm, gas_det) 
    params.radius.put(r)
    params.intensity.put(i)

    # set injector motor based on camera inline or offaxis
    if offaxis:
        injector_axis = injector.coarseZ
    else:
        injector_axis = injector.coarseX

    # collect images and motor positions needed for calibration
    imgs = []
    positions = []
    start_pos = injector_axis.user_readback.get()
    for i in range(2):
        image = get_burst_avg(params.frames_cam.get(), camera.image)
        imgs.append(image)
        positions.append(injector_axis.user_readback.get())
        next_position = injector_axis.user_setpoint.get() - 0.1
        injector_axis.set(next_position, wait=True)
        sleep(delay)

    injector_axis.set(start_pos, wait=True)
    sleep(delay)

    if offaxis:
        cam_pitch, pxsize = cam_utils.get_cam_pitch_pxsize(imgs, positions)
        params.pxsize.put(pxsize)
        params.cam_pitch.put(cam_pitch)

        beamY_px = params.beam_y_px.get()
        beamZ_px = params.beam_z_px.get()
        camY, camZ = cam_utils.get_offaxis_coords(beamY_px, beamZ_px,
                                                  cam_pitch=cam_pitch,
                                                  pxsize=pxsize)
        params.cam_y.put(camY)
        params.cam_z.put(camZ)

        jet_pitch = cam_utils.get_jet_pitch(theta, cam_pitch=cam_pitch)
        params.jet_pitch.put(jet_pitch)

    else:
        # cam_roll: rotation of camera abou z axis in radians
        # pxsize: size of pixel in mm
        cam_roll, pxsize = cam_utils.get_cam_roll_pxsize(imgs, positions)
        params.pxsize.put(pxsize)
        params.cam_roll.put(cam_roll)

        # beam_x_px: x-coordinate of x-ray beam in camera image in pixels
        beamX_px = params.beam_x_px.get()
        # beam_y_ox: y-coordinate of x-ray beam in camera image in pixels
        beamY_px = params.beam_y_px.get()
        # cam_x: x-coordinate of camera position in mm
        # cam_y: y-coordinate of camera position in mm
        camX, camY = cam_utils.get_cam_coords(beamX_px, beamY_px,
                                              cam_roll=cam_roll, pxsize=pxsize)
        params.cam_x.put(camX)
        params.cam_y.put(camY)

        # jet_roll: rotation of sample jet about z axis in radians
        jet_roll = cam_utils.get_jet_roll(theta, cam_roll=cam_roll)
        params.jet_roll.put(jet_roll)


def _jet_calculate_step_offaxis(camera, params):
    'A single step of the infinite-loop jet_calculate (off-axis)'
    # detect the jet in the camera ROI
    ROI_image = get_burst_avg(params.frames_cam.get(), camera.ROI_image)
    rho, theta = cam_utils.jet_detect(ROI_image, params.mean.get(), params.std.get())

    # check x-ray beam position
    beamY_px = params.beam_y_px.get()
    beamZ_px = params.beam_z_px.get()
    camY, camZ = cam_utils.get_offaxis_coords(beamY_px, beamZ_px,
                                              cam_pitch=params.cam_pitch.get(),
                                              pxsize=params.pxsize.get())

    params.cam_y.put(camY)
    params.cam_z.put(camZ)

    # find distance from jet to x-rays
    ROIz = camera.ROI.min_xyz.min_x.get()
    ROIy = camera.ROI.min_xyz.min_y.get()
    jetZ = cam_utils.get_jet_z(rho, theta, roi_y=ROIy, roi_z=ROIz,
                               pxsize=params.pxsize.get(),
                               cam_y=camY,
                               cam_z=camZ,
                               beam_y=params.beam_y.get(),
                               beam_z=params.beam_z.get(),
                               cam_pitch=params.cam_pitch.get())
    params.jet_z.put(jetZ)


def _jet_calculate_step(camera, params):
    'A single step of the infinite-loop jet_calculate (on-axis)'
    # detect the jet in the camera ROI
    ROI_image = get_burst_avg(params.frames_cam, camera.ROI_image)
    rho, theta = cam_utils.jet_detect(ROI_image, params.mean.get(), params.std.get())

    # check x-ray beam position
    beamX_px = params.beam_x_px.get()
    beamY_px = params.beam_y_px.get()
    camX, camY = cam_utils.get_cam_coords(beamX_px, beamY_px,
                                          cam_roll=params.cam_roll.get(),
                                          pxsize=params.pxsize.get())

    params.cam_x.put(camX)
    params.cam_y.put(camY)

    # find distance from jet to x-rays
    ROIx = camera.ROI.min_xyz.min_x.get()
    ROIy = camera.ROI.min_xyz.min_y.get()
    jetX = cam_utils.get_jet_x(rho, theta, ROIx, ROIy,
                               pxsize=params.pxsize.get(),
                               cam_x=camX,
                               cam_y=camY,
                               beam_x=params.beam_x.get(),
                               beam_y=params.beam_y.get(),
                               cam_roll=params.cam_roll.get())
    params.jet_x.put(jetX)


def jet_calculate(camera, params, offaxis=False):
    '''
    Track the sample jet and calculate the distance to the x-ray beam
    NEED TO CHECK offaxis calculation sign

    Parameters
    ----------
    camera : Questar
        camera looking at the sample jet and x-ray beam
    params : Parameters
        EPICS PVs used for recording jet tracking data
    offaxis : bool
        Camera is off-axis in y-z plane
    '''

    print('Running...')
    try:
        while True:
            if offaxis:
                _jet_calculate_step_offaxis(camera, params)
            else:
                _jet_calculate_step(camera, params)
    except KeyboardInterrupt:
        print('Stopped.')


def _jet_move_step(injector, camera, params):
    'A single step of the infinite-loop jet_move'
    ROIx = camera.ROI.min_xyz.min_x.get()
    # ROIy = camera.ROI.min_xyz.min_y.get()

    if abs(params.jet_x.get()) > 0.01:
        # move jet to x-rays using injector motor
        print(f'Moving {params.jet_x.get()} mm')
        movex(injector.coarseX, -params.jet_x.get())
        # move the ROI to keep looking at the jet
        min_x = ROIx + (params.jet_x.get() / params.pxsize.get())
        camera.ROI.min_xyz.min_x.put(min_x)


def jet_move(injector, camera, params):
    '''
    Move the sample jet to the x-ray beam

    Parameters
    ----------
    injector : Injector
        sample injector
    camera : Questar
        camera looking at the sample jet and x-ray beam
    params : Parameters
        EPICS PVs used for recording jet tracking data
    '''

    print('Running...')
    try:
        while True:
            _jet_move_step(injector, camera, params)
            sleep(5)
    except KeyboardInterrupt:
        print('Stopped.')


def jet_scan(injector, cspad, params):
  x_min = 0.0012
  steps = 50
  x_step = (-1) * steps * x_min / 2
  hi_intensities = []
  best_pos = []
  for i in range(2):
    # move motor to first position  
    injector.coarseX.mv(x_step, wait=True)
    intensities = []
    positions = []
    for j in range(steps):
      positions.append(injector.coarseX.user_readback.get())
      # get azav from CSPAD
      # get CSPAD and wave8
      azav, norm = get_azav(CSPAD) #call azimuthal average function
      intensities.append(jt_utils.get_cspad(azav, params.radius.get(), gas_det))
    hi_intensities.append(max(intensities))
    best_pos.append(positions[intensities.index(max(intensities))])
  # move motor to average of best positions from two sweeps
  injector.coarseX.mv(np.average(best_pos)) 
  # save CSPAD intensity
  params.intensity.put(np.average(hi_intensities))


