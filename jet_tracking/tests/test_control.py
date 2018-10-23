import pytest
import numpy as np
from . import conftest


def test_smoke_get_burst_avg(jet_control):
    from ..jet_control import get_burst_avg
    roi_image = jet_control.camera.ROI_image
    conftest.set_random_image(roi_image)
    get_burst_avg(2, roi_image)


def test_smoke_set_beam(jet_control):
    from ..jet_control import set_beam
    set_beam(1, 2, jet_control.params)
    assert jet_control.params.beam_x_px.get() == 1
    assert jet_control.params.beam_y_px.get() == 2


@pytest.mark.parametrize("use_offaxis", [False, True])
def test_smoke_calibrate(jet_control, injector, questar, parameters,
                         offaxis_parameters, use_offaxis):
    from ..jet_control import calibrate
    params = (offaxis_parameters
              if use_offaxis
              else parameters)

    conftest.set_random_image(jet_control.camera.image)
    conftest.set_random_image(jet_control.camera.ROI_image)
    calibrate(injector=injector, camera=questar, params=params,
              offaxis=use_offaxis)
