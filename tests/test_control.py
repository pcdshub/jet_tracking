import pytest

from jet_tracking.jet_control import (calibrate, jet_calculate_inline,
                                      jet_calculate_off_axis, jet_move_inline,
                                      set_beam)


def test_smoke_set_beam(inline_parameters):
    set_beam(1, 2, inline_parameters)
    assert inline_parameters.beam_x_px.get() == 1
    assert inline_parameters.beam_y_px.get() == 2


@pytest.mark.skip(reason="The calibrate function is far from complete")
@pytest.mark.parametrize("use_offaxis", [False, True])
def test_smoke_calibrate(jet_control, injector, questar, inline_parameters,
                         offaxis_parameters, use_offaxis):
    params = (offaxis_parameters if use_offaxis else inline_parameters)
    calibrate(injector=injector, camera=questar, params=params,
              offaxis=use_offaxis)


@pytest.mark.parametrize("use_offaxis", [False, True])
def test_smoke_jet_calculate(questar, inline_parameters,
                             offaxis_parameters, use_offaxis):
    questar.ROI.min_xyz.min_x.sim_put(1)
    questar.ROI.min_xyz.min_y.sim_put(1)
    questar.ROI.min_xyz.min_z.sim_put(1)
    if use_offaxis:
        jet_calculate_off_axis(camera=questar, params=offaxis_parameters)
    else:
        jet_calculate_inline(camera=questar, params=inline_parameters)


@pytest.mark.parametrize("jet_x", [0.0, 0.1])
def test_smoke_jet_move(injector, questar, inline_parameters,
                        jet_x):
    questar.ROI.min_xyz.min_x.put(1)
    inline_parameters.jet_x.sim_put(jet_x)
    jet_move_inline(injector=injector, camera=questar, params=inline_parameters)
