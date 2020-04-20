import pytest

from jet_tracking.jet_control import (calibrate, jet_calculate_inline,
                                      jet_calculate_off_axis, jet_move_inline,
                                      set_beam)

from . import conftest


def test_smoke_set_beam(jet_control):
    set_beam(1, 2, jet_control.params)
    assert jet_control.params.beam_x_px.get() == 1
    assert jet_control.params.beam_y_px.get() == 2


@pytest.mark.skip(reason="The calibrate function is far from complete")
@pytest.mark.parametrize("use_offaxis", [False, True])
def test_smoke_calibrate(jet_control, injector, questar, parameters,
                         offaxis_parameters, use_offaxis):
    params = (offaxis_parameters
              if use_offaxis
              else parameters)

    conftest.set_test_jet_image(questar.image)
    conftest.set_test_jet_image(questar.ROI_image)
    calibrate(injector=injector, camera=questar, params=params,
              offaxis=use_offaxis)


@pytest.mark.parametrize("use_offaxis", [False, True])
def test_smoke_jet_calculate(questar, parameters,
                             offaxis_parameters, use_offaxis):
    conftest.set_test_jet_image(questar.image)
    conftest.set_test_jet_image(questar.ROI_image)
    questar.ROI.min_xyz.min_x.sim_put(1)
    questar.ROI.min_xyz.min_y.sim_put(1)
    questar.ROI.min_xyz.min_z.sim_put(1)
    if use_offaxis:
        jet_calculate_off_axis(camera=questar, params=offaxis_parameters)
    else:
        jet_calculate_inline(camera=questar, params=parameters)


@pytest.mark.parametrize("jet_x", [0.0, 0.1])
def test_smoke_jet_move(injector, questar, parameters,
                        jet_x):
    questar.ROI.min_xyz.min_x.put(1)
    parameters.jet_x.sim_put(jet_x)
    jet_move_inline(injector=injector, camera=questar, params=parameters)


devices_without_table = {'Questar', 'Offaxis', 'SDS'}


def test_table(device_instances):
    for dev_name in dir(device_instances):
        if dev_name.startswith('_') or dev_name in devices_without_table:
            continue
        dev = getattr(device_instances, dev_name)
        print()
        print(f'-- {dev_name} --')
        print(dev.table)
