import pytest
import numpy as np
from .. import cam_utils


@pytest.fixture()
def onaxis_image():
    # TODO: an actual image would be nice...
    return np.random.random((100, 100))


def test_smoke_jet_detect(onaxis_image):
    print(cam_utils.jet_detect(onaxis_image))


def test_smoke_get_jet_z():
    cam_utils.get_jet_z(rho=0.0, theta=0.0, roi_y=1, roi_z=1, pxsize=0.001,
                        cam_y=1, cam_z=1, beam_y=1, beam_z=1, cam_pitch=1)


def test_smoke_get_jet_x():
    cam_utils.get_jet_x(rho=0.0, theta=0.0, roi_x=1, roi_y=1, pxsize=0.001,
                        cam_x=1, cam_y=1, beam_x=1, beam_y=1, cam_roll=1)


def test_smoke_get_jet_pitch():
    cam_utils.get_jet_pitch(theta=0.0, cam_pitch=1)


def test_smoke_get_jet_roll():
    cam_utils.get_jet_roll(theta=0.0, cam_roll=1)


def test_smoke_get_jet_width(onaxis_image):
    cam_utils.get_jet_width(im=onaxis_image, rho=0.0, theta=1.0)


def test_smoke_get_offaxis_coords():
    cam_utils.get_offaxis_coords(cam_beam_y=0.0, cam_beam_z=0.0,
                                 cam_pitch=1, pxsize=0.001)


def test_smoke_get_cam_coords():
    cam_utils.get_cam_coords(cam_beam_x=0.0, cam_beam_y=0.0,
                             cam_roll=1, pxsize=0.001)


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
