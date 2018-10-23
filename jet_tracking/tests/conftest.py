import pytest
import types
import ophyd
from pcdsdevices.areadetector.detectors import PCDSDetector
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
    return devices.Injector(
        name='fake_PI1_injector',
        coarseX='fake_CXI:PI1:MMS:01',
        coarseY='fake_CXI:PI1:MMS:02',
        coarseZ='fake_CXI:PI1:MMS:03',
        fineX='fake_CXI:USR:MMS:01',
        fineY='fake_CXI:USR:MMS:02',
        fineZ='fake_CXI:USR:MMS:03'
    )


def _patch_array_data(plugin_inst):
    def get_array_data(*args, count=None, **kwargs):
        # eat the count argument, unsupported by fakeepicssignal.get()
        return orig_get(*args, **kwargs)

    array_data = plugin_inst.array_data
    orig_get = array_data.get
    array_data.get = get_array_data


@pytest.fixture(scope='function')
def questar(devices):
    questar = devices.Questar(
        prefix='fake_CXI:SC1:INLINE',
        name='fake_SC1_questar',
        ROI_port='ROI1',
        ROI_stats_port='Stats1',
        ROI_image_port='IMAGE1',
    )

    _patch_array_data(questar.ROI_image)
    return questar


@pytest.fixture(scope='function')
def parameters(devices):
    return devices.Parameters(
        prefix='fake_CXI:SC1:INLINE',
        name='fake_SC1_params'
    )


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
