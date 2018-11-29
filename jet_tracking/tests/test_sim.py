import pytest
import jet_tracking.sim


@pytest.fixture(scope='function')
def simulation():
    return jet_tracking.sim.generate_simulation(adu_max=1.0,
                                                beam_energy=2.0,
                                                adu_sigma=0.5,
                                                adu_floor=0.,
                                                beam_position=0.,
                                                jet_width=1.0,
                                                jet_noise=0.,
                                                energy_noise=0.,
                                                drop_rate=0.)


def test_at_max(simulation):
    simulation.inj_x.set(0.)
    simulation.cspad_adu.trigger()
    assert simulation.cspad_adu.get() == 2.0
    simulation.beam.put(3.0)
    simulation.cspad_adu.trigger()
    assert simulation.cspad_adu.get() == 3.0


def test_symmetry(simulation):
    simulation.inj_x.set(0.2)
    simulation.cspad_adu.trigger()
    right = simulation.cspad_adu.get()
    simulation.inj_x.set(-0.2)
    simulation.cspad_adu.trigger()
    left = simulation.cspad_adu.get()
    assert left == right


def test_off_jet(simulation):
    simulation.inj_x.set(1000)
    simulation.cspad_adu.trigger()
    assert simulation.cspad_adu.get() == simulation.params.adu_floor


def test_drop_rate(simulation):
    simulation.beam.drop_rate = 1.0
    simulation.beam.trigger()
    simulation.cspad_adu.trigger()
    assert simulation.beam.get() == simulation.params.adu_floor


@pytest.mark.parametrize('det', (jet_tracking.sim.simulation.beam,
                                 jet_tracking.sim.simulation.cspad_adu),
                         ids=('beam', 'cspad_adu'))
def test_noise(det):
    readings = list()
    for i in range(10):
        det.trigger()
        readings.append(det.read()[det.name]['value'])
    assert len(set(readings)) > 1
