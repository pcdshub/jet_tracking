import numpy as np
import pytest
import types
import inspect
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
    injector = _instantiate_fake_device(
        devices.Injector,
        name='fake_PI1_injector',
        coarseX='fake_CXI:PI1:MMS:01',
        coarseY='fake_CXI:PI1:MMS:02',
        coarseZ='fake_CXI:PI1:MMS:03',
        fineX='fake_CXI:USR:MMS:01',
        fineY='fake_CXI:USR:MMS:02',
        fineZ='fake_CXI:USR:MMS:03'
    )

    for i, attr in enumerate(['coarseX', 'coarseY', 'coarseZ',
                              'fineX', 'fineY', 'fineZ']):
        motor = getattr(injector, attr)
        motor.user_readback.sim_put(0.1 * i)
        motor.user_setpoint.sim_put(0.0)
        motor.motor_spg.sim_put('Go')
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
    questar = _instantiate_fake_device(
        devices.Questar,
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
def offaxis_camera(devices):
    offaxis = _instantiate_fake_device(
        devices.Offaxis,
        prefix='fake_CXI:SC1:OFFAXIS',
        name='fake_SC1_offaxis',
        ROI_port='ROI1',
        ROI_stats_port='Stats1',
        ROI_image_port='IMAGE1',
    )

    _patch_array_data(offaxis.image)
    _patch_array_data(offaxis.ROI_image)
    return offaxis


@pytest.fixture(scope='function')
def offaxis_parameters(devices):
    params = _instantiate_fake_device(
        devices.OffaxisParams,
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
    params = _instantiate_fake_device(
        devices.Parameters,
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
    return _instantiate_fake_device(devices.Diffract,
                                    prefix='fake_CXI:SC1:DIFFRACT',
                                    name='fake_SC1_diffract')


@pytest.fixture(scope='function')
def jet_control(injector, questar, parameters, diffract):
    from ..jet_control import JetControl
    return JetControl(name='test_control',
                      injector=injector,
                      camera=questar,
                      params=parameters,
                      diffract=diffract)


def _instantiate_fake_device(dev_cls, name=None, prefix='_prefix',
                             **specified_kw):
    '''Instantiate a FakeDevice, optionally specifying some initializer kwargs

    If unspecified, all initializer keyword arguments will default to
    the string f"_{argument_name}_".

    All signals on the device (and its subdevices) are initialized to either 0
    or ''.
    '''
    sig = inspect.signature(dev_cls)
    ignore_kw = {'kind', 'read_attrs', 'configuration_attrs', 'parent',
                 'args', 'name', 'prefix'}
    kwargs = {name: specified_kw.get(name, f'_{param.name}_')
              for name, param in sig.parameters.items()
              if param.kind != param.VAR_KEYWORD and
              name not in ignore_kw
              }
    kwargs['name'] = (name if name is not None else dev_cls.__name__)
    kwargs['prefix'] = prefix
    dev = dev_cls(**kwargs)

    devs = [dev]
    while devs:
        sub_dev = devs.pop(0)
        devs.extend([getattr(sub_dev, name)
                     for name in sub_dev._sub_devices])
        for name, cpt in sub_dev._sig_attrs.items():
            sig = getattr(sub_dev, name)
            try:
                if cpt.kwargs.get('string', False):
                    sig.sim_put('')
                else:
                    sig.sim_put(0)
            except Exception as ex:
                ...

    return dev


@pytest.fixture(scope='function')
def device_instances(injector, questar, offaxis_camera, parameters,
                     offaxis_parameters, diffract, devices):
    ns = types.SimpleNamespace()
    ns.Control = _instantiate_fake_device(devices.Control)
    ns.CoolerShaker = _instantiate_fake_device(devices.CoolerShaker)
    ns.Diffract = _instantiate_fake_device(devices.Diffract)
    ns.Diffract = diffract
    ns.FlowIntegrator = _instantiate_fake_device(devices.FlowIntegrator)
    ns.HPLC = _instantiate_fake_device(devices.HPLC)
    ns.Injector = injector
    ns.Offaxis = offaxis_camera
    ns.OffaxisParams = offaxis_parameters
    ns.Parameters = parameters
    ns.PressureController = _instantiate_fake_device(devices.PressureController)
    ns.Questar = questar
    ns.Selector = _instantiate_fake_device(devices.Selector)
    ns.SDS = SDS({})
    ns.SDS.SDS_devices.extend([ns.Selector, ns.CoolerShaker, ns.HPLC,
                               ns.PressureController, ns.FlowIntegrator])
    return ns


def set_random_image(plugin, dimx=100, dimy=100):
    'Set up a random image of dimensions (dimx, dimy) on the given image plugin'
    plugin.array_data.put(np.random.random((dimx, dimy)))
    plugin.array_size.width.sim_put(dimx)
    plugin.array_size.height.sim_put(dimy)
    plugin.array_size.depth.sim_put(0)
    plugin.ndimensions.sim_put(2)
