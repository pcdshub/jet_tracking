from os import path

import pytest
from matplotlib import image
from ophyd.sim import make_fake_device
from skimage.color import rgb2gray
from skimage.transform import resize

from jet_tracking.devices import OffaxisParams, Parameters, Questar
from pcdsdevices.jet import Injector


def instantiate_fake_device(cls, *args, **kwargs):
    fake_cls = make_fake_device(cls)
    fake_obj = fake_cls(*args, **kwargs)
    return fake_obj


def test_jet_image(dimx=100, dimy=100):
    'Returns a test image of the jet, sampled at the desired dimensions'
    imgpath = path.join(path.dirname(__file__), 'test_jet.png')
    testimage = image.imread(imgpath)[:, :, :3]
    return rgb2gray(resize(testimage, (dimx, dimy)))


@pytest.fixture(scope='function')
def onaxis_image():
    return test_jet_image()


def set_test_jet_image(plugin, dimx=100, dimy=100):
    'Set up a test jet image of dimensions (dimx, dimy) on the given image plugin'
    plugin.array_data.put(test_jet_image(dimx, dimy))
    plugin.array_size.width.sim_put(dimx)
    plugin.array_size.height.sim_put(dimy)
    plugin.array_size.depth.sim_put(0)
    plugin.ndimensions.sim_put(2)


@pytest.fixture(scope='function')
def questar():
    fake_questar = instantiate_fake_device(Questar, 'FAKE:INLINE',
                                           name='fake_inline',
                                           ROI_port='ROI1',
                                           ROI_stats_port='Stats1',
                                           ROI_image_port='IMAGE1')
    set_test_jet_image(fake_questar.image2)
    set_test_jet_image(fake_questar.ROI_image)
    return fake_questar


def _patch_user_setpoint(motor):
    def putter(pos, *args, **kwargs):
        motor.user_setpoint.sim_put(pos, *args, **kwargs)
        motor.user_readback.sim_put(pos)
        motor._done_moving(success=True)
    motor.user_setpoint.sim_set_putter(putter)


@pytest.fixture(scope='function')
def injector():
    injector = instantiate_fake_device(Injector, 'FAKE:INJECT',
                                       name='fake_injector',
                                       coarseX_prefix='fake_X',
                                       coarseY_prefix='fake_Y',
                                       coarseZ_prefix='fake_Z',
                                       fineX_prefix='fake_x',
                                       fineY_prefix='fake_y',
                                       fineZ_prefix='fake_z')
    for i, attr in enumerate(['coarseX', 'coarseY', 'coarseZ',
                              'fineX', 'fineY', 'fineZ']):
        motor = getattr(injector, attr)
        motor.user_readback.sim_put(0.1 * i)
        motor.user_setpoint.sim_put(0.0)
        motor.motor_spg.sim_put('Go')
        _patch_user_setpoint(motor)
    return injector


@pytest.fixture(scope='function')
def offaxis_parameters():
    params = instantiate_fake_device(OffaxisParams, 'FAKE:OFFAXIS:PARAMS',
                                     name='fake_offaxis_params')
    params.beam_y.put(1.0)
    params.beam_z.put(1.0)
    params.beam_y_px.put(1)
    params.beam_z_px.put(1)
    params.cam_y.put(1.0)
    params.cam_z.put(1.0)
    params.pxsize.put(0.001)
    params.cam_pitch.put(1.0)
    params.frames_cam.put(20)
    return params


@pytest.fixture(scope='function')
def inline_parameters():
    params = instantiate_fake_device(Parameters, 'FAKE:INLINE:PARAMS',
                                     name='fake_inline_params')
    params.beam_x.put(1.0)
    params.beam_y.put(1.0)
    params.beam_x_px.put(1)
    params.beam_y_px.put(1)
    params.cam_x.put(1.0)
    params.cam_y.put(1.0)
    params.pxsize.put(0.001)
    params.cam_roll.put(1.0)
    params.frames_cam.put(20)
    return params
