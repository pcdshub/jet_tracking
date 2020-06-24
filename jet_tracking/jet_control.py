from time import sleep

import numpy as np

from . import cam_utils, jt_utils


class JetControl:
    """Jet tracking control class using jet_tracking methods."""

    def __init__(self, name, injector, camera, params, diffract, *,
                 offaxis=False, **kwargs):
        self.name = name
        self.injector = injector
        self.camera = camera
        self.params = params
        self.diffract = diffract
        self.offaxis = offaxis

    def set_beam(self, beam_x_px, beam_y_px):
        """
        Set the coordinates for the x-ray beam.

        Parameters
        ----------
        beam_x_px : int
            X-coordinate of x-ray beam in the camera image in pixels.

        beam_y_px : int
            Y-coordinate of x-ray beam in the camera image in pixels.
        """

        set_beam(beam_x_px, beam_y_px, self.params)

    def calibrate(self, **kwargs):
        """Calibrate the onaxis camera."""
        if self.offaxis:
            return calibrate_off_axis(self.injector, self.camera, self.params,
                                      **kwargs)
        else:
            return calibrate_inline(self.injector, self.camera, self.params,
                                    **kwargs)

    def jet_calculate(self):
        """
        Track the sample jet and calculate the distance to the x-ray beam.
        """
        if self.offaxis:
            return jet_calculate_off_axis(self.camera, self.params)
        else:
            return jet_calculate_inline(self.camera, self.params)

    def jet_move(self):
        """Move the sample jet to the x-ray beam."""
        if self.offaxis:
            raise NotImplementedError()
        else:
            jet_move_inline(self.injector, self.camera, self.params)


def set_beam(beam_x_px, beam_y_px, params):
    """
    Set the coordinates for the x-ray beam.

    Parameters
    ----------
    beam_x_px : int
        X-coordinate of x-ray beam in the camera image in pixels.

    beam_y_px : int
        Y-coordinate of x-ray beam in the camera image in pixels.

    params : InlineParams
        EPICS PVs used for recording jet tracking data.
    """

    params.beam_x_px.put(beam_x_px)
    params.beam_y_px.put(beam_y_px)


def get_calibration_images(axis, camera, *, settle_time=1.0,
                           burst_images=20):
    # collect images and motor positions to calculate pxsize and cam_roll
    imgs = []
    positions = []
    start_pos = axis.user_readback.get()
    for i in range(2):
        image = cam_utils.get_burst_avg(burst_images, camera.image2)
        imgs.append(image)
        positions.append(axis.user_readback.get())
        next_position = axis.user_setpoint.get() - 0.1
        axis.set(next_position, wait=True)
        sleep(settle_time)

    axis.set(start_pos, wait=True)
    sleep(settle_time)
    return positions, imgs


def calibrate_off_axis(injector, camera, params, *, settle_time=1.0,
                       burst_images=20):
    """
    Calibrate the off-axis camera.

    First, set the ROI of the camera to show the proper jet and illumination.

    Determines the mean, standard deviation, jet position and tilt, pixel
    size, beam position, camera position and tilt

    Params determined if onaxis camera used: mean, std, pxsize, camX, camY,
    cam_roll, beamX_px, beamY_px, jet_roll

    Params determined if offaxis camera used: mean, std, pxsize, camY, camZ,
    cam_pitch, beamY_px, beamZ_px, jet_pitch

    Parameters
    ----------
    injector : Injector
        Sample injector.

    camera : JetCamera
        Camera looking at sample jet and x-rays.

    CSPAD : CSPAD
        CSPAD for data.

    params : OffaxisParams
        EPICS PVs used for recording jet tracking data.

    settle_time : float, optional
        Additional settle time after moving the motor.

    burst_imagess : int, optional
        Number of burst images to average from the camera.
    """

    # TODO: (koglin) check sign for off-axis calculations
    injector_axis = injector.x
    positions, imgs = get_calibration_images(injector_axis, camera,
                                             settle_time=settle_time)

    cam_pitch, pxsize = cam_utils.get_cam_pitch_pxsize(imgs, positions)
    params.pxsize.put(pxsize)
    params.cam_pitch.put(cam_pitch)

    beam_y_px = params.beam_y_px.get()
    beam_z_px = params.beam_z_px.get()
    cam_y, cam_z = cam_utils.get_cam_coords(beam_y_px, beam_z_px,
                                            cam_angle=cam_pitch,
                                            pxsize=pxsize)
    params.cam_y.put(cam_y)
    params.cam_z.put(cam_z)

    # Where is theta coming from?
    # Find the jet pitch from its angle in the camera frame
    jet_pitch = cam_utils.angle_diff(params.theta.get(), cam_pitch)
    params.jet_pitch.put(jet_pitch)
    return dict(jet_pitch=jet_pitch, pxsize=pxsize, cam_pitch=cam_pitch)


def calibrate_inline(injector, camera, params, *, settle_time=1.0,
                     burst_images=20):
    """
    Calibrate the inline camera.

    Parameters
    ----------
    injector : Injector
        Sample injector.

    camera : JetCamera
        Camera looking at sample jet and x-rays.

    params : InlineParams
        EPICS PVs used for recording jet tracking data.

    settle_time : float, optional
        Additional settle time after moving the motor.

    burst_imagess : int, optional
        Number of burst images to average from the camera.
    """

    injector_axis = injector.z
    # collect images and motor positions needed for calibration
    positions, imgs = get_calibration_images(injector_axis, camera,
                                             settle_time=settle_time,
                                             burst_images=burst_images)

    # cam_roll: rotation of camera about z axis in radians
    # pxsize: size of pixel in mm
    cam_roll, pxsize = cam_utils.get_cam_roll_pxsize(imgs, positions)
    params.pxsize.put(pxsize)
    params.cam_roll.put(cam_roll)

    # beam_x_px: x-coordinate of x-ray beam in camera image in pixels
    beam_x_px = params.beam_x_px.get()
    # beam_y_px: y-coordinate of x-ray beam in camera image in pixels
    beam_y_px = params.beam_y_px.get()
    # cam_x: x-coordinate of camera position in mm
    # cam_y: y-coordinate of camera position in mm
    cam_x, cam_y = cam_utils.get_cam_coords(beam_x_px, beam_y_px,
                                            cam_angle=cam_roll, pxsize=pxsize)
    params.cam_x.put(cam_x)
    params.cam_y.put(cam_y)

    # Find jet_roll, the rotation of sample jet about z axis in radians, from
    # the jet angle in the camera frame
    jet_roll = cam_utils.angle_diff(params.theta.get(), cam_roll)
    params.jet_roll.put(jet_roll)
    return dict(jet_roll=jet_roll, pxsize=pxsize, cam_roll=cam_roll)


def calibrate(injector, camera, cspad, wave8, gas_det, params, *, offaxis=False, settle_time=0.1):
    """
    Calibrate the camera and CSPAD and determine necessary parameters.

    TODO: NEED TO CHECK offaxis calculation sign

    First, set the ROI of the camera to show the proper jet and illumination.

    Determines the mean, standard deviation, radius, intensity, jet position
    and tilt, pixel size, camera position and tilt.

    Params determined if onaxis camera used: mean, std, radius, intensity,
    pxsize, camX, camY, cam_roll, jet_roll

    Params determined if offaxis camera used: mean, std, radius, intensity,
    pxsize, camY, camZ, cam_pitch, jet_pitch

    Parameters
    ----------
    injector : Injector
        Sample injector.

    camera : JetCamera
        Camera looking at sample jet and x-rays

    cspad : CSPAD
        CSPAD for data.

    wave8 : Wave8
        Wave8 to normalize data from CSPAD.

    gas_det : float
        Gas detector.

    params : InlineParams or OffaxisParams
        EPICS PVs used for recording jet tracking data.

    settle_time : float, optional
        Additional settle time after moving the motor.

    offaxis : bool, optional
        Camera is off-axis in y-z plane.
    """

    # find jet in camera ROI
    ROI_image = cam_utils.get_burst_avg(params.frames_cam.get(), camera.ROI_image)
    mean = ROI_image.mean()
    std = ROI_image.std()
    # the mean and std are passed to be compared to themselves?
    rho, theta = cam_utils.jet_detect(ROI_image, mean, std)
    params.mean.put(mean)
    params.std.put(std)

    # take calibration CSPAD data
    # get CSPAD and wave8 data
    azav, norm = get_azav(cspad)  # call azimuthal average function
    r, i = jt_utils.fit_CSPAD(azav, norm, gas_det)
    params.radius.put(r)
    params.intensity.put(i)

    # call appropriate camera calibration method
    if offaxis:
        return calibrate_off_axis(injector, camera, params,
                                  settle_time=settle_time)
    else:
        return calibrate_inline(injector, camera, params,
                                settle_time=settle_time)


def jet_calculate_off_axis(camera, params):
    """
    Calculate distance to x-ray beam using off-axis camera.

    First, detect the sample jet. Then, calculate the distance between it and
    the x-ray beam.

    Parameters
    ----------
    camera : JetCamera
        Camera looking at the sample jet and x-ray beam.

    params : OffaxisParams
        EPICS PVs used for recording jet tracking data.

    offaxis : bool
        Camera is off-axis in y-z plane.
    """

    # detect the jet in the camera ROI
    ROI_image = cam_utils.get_burst_avg(params.frames_cam.get(), camera.ROI_image)
    mean = ROI_image.mean()
    std = ROI_image.std()
    rho, theta = cam_utils.jet_detect(ROI_image, mean, std)

    # check x-ray beam position
    beam_y_px = params.beam_y_px.get()
    beam_z_px = params.beam_z_px.get()
    cam_y, cam_z = cam_utils.get_cam_coords(beam_y_px, beam_z_px,
                                            cam_angle=params.cam_pitch.get(),
                                            pxsize=params.pxsize.get())

    params.cam_y.put(cam_y)
    params.cam_z.put(cam_z)

    # find distance from jet to x-rays
    roi_z = camera.ROI.min_xyz.min_x.get()
    roi_y = camera.ROI.min_xyz.min_y.get()
    jet_z = cam_utils.get_jet_z(rho, theta, roi_y=roi_y, roi_z=roi_z,
                                pxsize=params.pxsize.get(), cam_y=cam_y,
                                cam_z=cam_z, beam_y=params.beam_y.get(),
                                beam_z=params.beam_z.get(),
                                cam_pitch=params.cam_pitch.get())
    params.jet_z.put(jet_z)
    return dict(rho=rho, theta=theta, cam_y=cam_y, cam_z=cam_z, jet_z=jet_z)


def jet_calculate_inline(camera, params):
    """
    Calculate distance to x-ray beam using inline camera.

    First, detect the sample jet. Then, calculate the distance between it and
    the x-ray beam.

    Parameters
    ----------
    camera : JetCamera
        Camera looking at the sample jet and x-ray beam.

    params : InlineParams
        EPICS PVs used for recording jet tracking data.

    offaxis : bool
        Camera is off-axis in y-z plane.
    """

    # detect the jet in the camera ROI
    ROI_image = cam_utils.get_burst_avg(params.frames_cam.get(), camera.ROI_image)
    mean = ROI_image.mean()
    std = ROI_image.std()
    rho, theta = cam_utils.jet_detect(ROI_image, mean, std)

    # check x-ray beam position
    beam_x_px = params.beam_x_px.get()
    beam_y_px = params.beam_y_px.get()
    cam_x, cam_y = cam_utils.get_cam_coords(beam_x_px, beam_y_px,
                                            cam_angle=params.cam_roll.get(),
                                            pxsize=params.pxsize.get())

    params.cam_x.put(cam_x)
    params.cam_y.put(cam_y)

    # find distance from jet to x-rays
    ROIx = camera.ROI.min_xyz.min_x.get()
    roi_y = camera.ROI.min_xyz.min_y.get()
    jet_x = cam_utils.get_jet_x(rho, theta, ROIx, roi_y,
                                pxsize=params.pxsize.get(), cam_x=cam_x,
                                cam_y=cam_y, beam_x=params.beam_x.get(),
                                beam_y=params.beam_y.get(),
                                cam_roll=params.cam_roll.get())
    params.jet_x.put(jet_x)
    return dict(rho=rho, theta=theta, cam_y=cam_y, cam_x=cam_x, jet_x=jet_x)


def jet_move_inline(injector, camera, params):
    """A single step of the infinite-loop jet_move."""
    ROIx = camera.ROI.min_xyz.min_x.get()
    # roi_y = camera.ROI.min_xyz.min_y.get()

    if abs(params.jet_x.get()) > 0.01:
        # move jet to x-rays using injector motor
        print(f'Moving {params.jet_x.get()} mm')
        injector.x.mvr(-params.jet_x.get())
        # move the ROI to keep looking at the jet
        min_x = ROIx + (params.jet_x.get() / params.pxsize.get())
        camera.ROI.min_xyz.min_x.put(min_x)


def jet_scan(injector, cspad, gas_det, params):
    x_min = 0.0012
    steps = 50
    x_step = (-1) * steps * x_min / 2
    hi_intensities = []
    best_pos = []
    for i in range(2):
        # move motor to first position
        injector.x.mv(x_step, wait=True)
        intensities = []
        positions = []
        for j in range(steps):
            positions.append(injector.x.user_readback.get())
            # get azav from CSPAD
            # get CSPAD and wave8
            azav, norm = get_azav(cspad)  # call azimuthal average function
            intensities.append(jt_utils.get_cspad(azav, params.radius.get(), gas_det))
        hi_intensities.append(max(intensities))
        best_pos.append(positions[intensities.index(max(intensities))])
    # move motor to average of best positions from two sweeps
    injector.x.mv(np.average(best_pos))
    # save CSPAD intensity
    params.intensity.put(np.average(hi_intensities))


def get_azav(cspad):
    return NotImplemented
