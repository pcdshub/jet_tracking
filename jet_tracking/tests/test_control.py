import pytest
import numpy as np


def test_smoke_get_burst_avg(jet_control):
    from ..jet_control import get_burst_avg
    roi_image = jet_control.camera.ROI_image
    roi_image.array_data.put(np.random.random((100, 100)))

    roi_image.array_size.width.sim_put(100)
    roi_image.array_size.height.sim_put(100)
    roi_image.array_size.depth.sim_put(0)
    roi_image.dimensions.sim_put(2)
    get_burst_avg(2, roi_image)


def test_smoke_set_beam(jet_control):
    from ..jet_control import set_beam
    set_beam(1, 2, jet_control.params)
    assert jet_control.params.beam_x_px.get() == 1
    assert jet_control.params.beam_y_px.get() == 2
