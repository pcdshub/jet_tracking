import numpy as np

from jet_tracking import cam_utils


# This doesn't really test much...
def test_smoke_jet_detect(onaxis_image):
    print(cam_utils.jet_detect(onaxis_image, onaxis_image.mean(), onaxis_image.std()))


def test_smoke_get_jet_z():
    cam_utils.get_jet_z(rho=0.0, theta=0.0, roi_y=1, roi_z=1, pxsize=0.001,
                        cam_y=1, cam_z=1, beam_y=1, beam_z=1, cam_pitch=1)


def test_smoke_get_jet_x():
    cam_utils.get_jet_x(rho=0.0, theta=0.0, roi_x=1, roi_y=1, pxsize=0.001,
                        cam_x=1, cam_y=1, beam_x=1, beam_y=1, cam_roll=1)


def test_smoke_angle_diff():
    assert np.isclose(cam_utils.angle_diff(np.pi/3, -np.pi/3), -np.pi/3)
    assert np.isclose(cam_utils.angle_diff(-np.pi/3, np.pi/3), np.pi/3)
    assert np.isclose(cam_utils.angle_diff(np.pi/3, np.pi/3), 0)


def test_smoke_get_jet_width(onaxis_image):
    cam_utils.get_jet_width(im=onaxis_image, rho=0.0, theta=1.0)


def test_smoke_get_cam_coords():
    cam_utils.get_cam_coords(cam_beam_x=0.0, cam_beam_y=0.0,
                             cam_angle=1, pxsize=0.001)


# I think all of these random's should be replaced by a second image?
def test_smoke_get_cam_pitch(onaxis_image):
    cam_utils.get_cam_pitch([onaxis_image,
                             np.random.random(onaxis_image.shape)])


def test_smoke_get_cam_roll(onaxis_image):
    cam_utils.get_cam_roll([onaxis_image,
                            np.random.random(onaxis_image.shape)])


def test_smoke_get_cam_pitch_pxsize(onaxis_image):
    cam_utils.get_cam_pitch_pxsize([onaxis_image,
                                    np.random.random(onaxis_image.shape)],
                                   positions=[0, 1])


def test_smoke_get_cam_roll_pxsize(onaxis_image):
    cam_utils.get_cam_roll_pxsize([onaxis_image,
                                   np.random.random(onaxis_image.shape)],
                                  positions=[0, 1])


def test_smoke_get_nozzle_shift(onaxis_image):
    cam_utils.get_nozzle_shift(
        onaxis_image, np.random.random(onaxis_image.shape),
        cam_roll=1, pxsize=0.001)


def test_smoke_get_burst_avg(camera):
    cam_utils.get_burst_avg(2, camera.ROI_image)
