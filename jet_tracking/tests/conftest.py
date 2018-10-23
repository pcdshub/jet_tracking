import numpy as np
import pytest
import types
from ..devices import (Injector, Selector, CoolerShaker, HPLC,
                       PressureController, FlowIntegrator, Offaxis, Questar,
                       Parameters, OffaxisParams, Control, Diffract,
                       SDS)


all_devices = (Injector, Selector, CoolerShaker, HPLC, PressureController,
               FlowIntegrator, Offaxis, Questar, Parameters, OffaxisParams,
               Control, Diffract, SDS)


@pytest.fixture(scope='function')
def devices(monkeypatch):
    '''A namespace containing faked versions of all devices

    Separately, this monkeypatches jet_tracking.devices so that all access
    to those devices returns the faked versions.
    '''
    from .. import devices as _devices
    from ophyd.areadetector import EpicsSignalWithRBV
    import ophyd.sim

    ns = types.SimpleNamespace()
    ophyd.sim.fake_device_cache[EpicsSignalWithRBV] = ophyd.sim.FakeEpicsSignal

    for cls in all_devices:
        name = cls.__name__
        if cls is not SDS:
            cls = ophyd.sim.make_fake_device(cls)

        setattr(ns, name, cls)
        monkeypatch.setattr(_devices, name, cls)

    # Short-circuit all plugin type checks, array data

    for dev in (ns.Questar, ns.Offaxis):
        for plugin_name in ('ROI', 'ROI_stats', 'ROI_image', 'image', 'stats'):
            plugin_cls = getattr(dev, plugin_name).cls
            monkeypatch.setattr(plugin_cls, '_plugin_type', None)
    return ns


@pytest.fixture(scope='function')
def injector(devices):
    injector = devices.Injector(
        name='fake_PI1_injector',
        coarseX='fake_CXI:PI1:MMS:01',
        coarseY='fake_CXI:PI1:MMS:02',
        coarseZ='fake_CXI:PI1:MMS:03',
        fineX='fake_CXI:USR:MMS:01',
        fineY='fake_CXI:USR:MMS:02',
        fineZ='fake_CXI:USR:MMS:03'
    )

    for attr in ('coarseX', 'coarseY', 'coarseZ',
                 'fineX', 'fineY', 'fineZ'):
        motor = getattr(injector, attr)
        motor.user_readback.sim_put(0.0)
        motor.user_setpoint.sim_put(0.0)
        _patch_user_setpoint(motor)
    return injector


def _patch_array_data(plugin_inst):
    def get_array_data(*args, count=None, **kwargs):
        # eat the count argument, unsupported by fakeepicssignal.get()
        return orig_get(*args, **kwargs)

    array_data = plugin_inst.array_data
    orig_get = array_data.get
    array_data.get = get_array_data


def _patch_user_setpoint(motor):
    def putter(pos, *args, **kwargs):
        motor.user_setpoint.sim_put(pos, *args, **kwargs)
        motor.user_readback.sim_put(pos)
        motor._done_moving(success=True)

    motor.user_setpoint.sim_set_putter(putter)


@pytest.fixture(scope='function')
def questar(devices):
    questar = devices.Questar(
        prefix='fake_CXI:SC1:INLINE',
        name='fake_SC1_questar',
        ROI_port='ROI1',
        ROI_stats_port='Stats1',
        ROI_image_port='IMAGE1',
    )

    _patch_array_data(questar.image)
    _patch_array_data(questar.ROI_image)
    return questar


@pytest.fixture(scope='function')
def offaxis_parameters(devices):
    params = devices.OffaxisParams(
        prefix='fake_CXI:SC1:INLINE',
        name='fake_SC1_params'
    )
    params.beam_y.put(1.0)
    params.beam_z.put(1.0)
    params.beam_y_px.put(1)
    params.beam_z_px.put(1)
    params.cam_y.put(1.0)
    params.cam_z.put(1.0)
    params.pxsize.put(0.001)
    params.cam_pitch.put(1.0)
    return params


@pytest.fixture(scope='function')
def parameters(devices):
    params = devices.Parameters(
        prefix='fake_CXI:SC1:INLINE',
        name='fake_SC1_params'
    )
    params.beam_x.put(1.0)
    params.beam_y.put(1.0)
    params.beam_x_px.put(1)
    params.beam_y_px.put(1)
    params.cam_x.put(1.0)
    params.cam_y.put(1.0)
    params.pxsize.put(0.001)
    params.cam_roll.put(1.0)
    return params


@pytest.fixture(scope='function')
def diffract(devices):
    return devices.Diffract(prefix='fake_CXI:SC1:DIFFRACT',
                            name='fake_SC1_diffract')


@pytest.fixture(scope='function')
def jet_control(injector, questar, parameters, diffract):
    from ..jet_control import JetControl
    return JetControl(name='test_control',
                      injector=injector,
                      camera=questar,
                      params=parameters,
                      diffract=diffract)


def set_random_image(plugin, dimx=100, dimy=100):
    'Set up a random image of dimensions (dimx, dimy) on the given image plugin'
    plugin.array_data.put(np.random.random((dimx, dimy)))
    plugin.array_size.width.sim_put(dimx)
    plugin.array_size.height.sim_put(dimy)
    plugin.array_size.depth.sim_put(0)
    plugin.ndimensions.sim_put(2)
