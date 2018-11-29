from types import SimpleNamespace

import numpy as np
from ophyd import Signal
from ophyd.sim import SynAxis, SynSignal


class BeamSignal(Signal):
    """
    Class to represent the energy of the beam

    The setpoint can be entered by the user simply by use ``.put``. After that,
    two kinds of noise will be added. First, a gaussian distribution of with
    ``sigma`` equal to the :param:`.noise` is added. Secondly, in order to
    simulate frequent drops in the beam, certain ``.get`` attempts will report
    a zero value as if the shot was dropped.

    Parameters
    ----------
    noise: float, optional
        Width of distribution of values around the energy setpoint. For
        instance, if set to 1.0, 68% of values will lie within 1.0 of the
        setpoint.

    drop_rate: float, optional
        Probability that a shot will be dropped and report 0. as the energy.
        This should be a value between 0 and 1, with 1 being a 100% chance that
        the shot is counted as dropped.

    args, kwargs:
        Passed to ``ophyd.Signal`` constructor
    """
    def __init__(self, *args, noise=0., drop_rate=0., **kwargs):
        super().__init__(*args, **kwargs)
        self.noise = noise
        self.drop_rate = drop_rate

    def get(self):
        """Get the signal. Add noise or drop based on settings"""
        if np.random.uniform(0, 1) > self.drop_rate:
            value = super().get()
            if self.noise:
                value += np.random.normal(0., self.noise)
            return value
        return 0.


def generate_simulation(motor_precision=3,
                        beam_energy=2.5,
                        energy_noise=0.3,
                        beam_position=0.,
                        drop_rate=0.15,
                        adu_max=15000,
                        adu_sigma=1500,
                        adu_floor=200,
                        jet_width=0.01,
                        jet_noise=0.005,
                        ):
    """
    Generate a simulation of the injector, gas detector and CSPAD intensity

    Parameters
    ----------
    motor_precision: int, optional
        Limit the number of significant digits of the injector position. Stored
        on ``inj_x``.

    beam_energy: float, optional
        The starting energy of the beam in the simulation. Modify by setting
        ``beam``

    drop_rate: float, optional
        The probability that the energy of a shot will be zero. Stored on the
        ``beam`` object.

    energy_noise: float, optional
        The value of a single standard deviation for flucuations in beam
        energy. Stored on the ``beam`` object.

    beam_position: float, optional
        Position of the beam. This is where the center of the Gaussian
        distribution will be for the ``cspad_adu``.

    adu_max: float, optional
        Value to scale the Gaussian distribution underlying the ``cspad_adu``
        signal.

    adu_sigma: float, optional
        The value of a single standard deviation for flucuations in the CSPAD
        intensity.

    adu_floor: float, optional
        The base value of the detector when it is not seeing any evidence of
        thet jet.

    jet_width: float, optional
        The width of the jet where we expect to receive a measurable difference
        in CSPAD intensity.

    jet_noise: float, optional
        A single standard deviation for the difference between the injector
        position and where the jet is located.

    Returns
    -------
    namespace: types.SimpleNamespace
        With attributes, ``params``, ``beam``, ``inj_x`` and ``cspad_adu``

    Notes
    -----
    The calculation has a number of layers with the potential for noise to be
    added in a number of places to properly simulate real data:

    1. A :class:`.BeamEnergy` named ``beam`` is created and will simulate the
    energy of the incoming photons. This also has a statistical flucuation with
    an introduced ``drop_rate``

    2. A ``SynAxis``, ``inj_x``, is instantiated. A simplification is made that
    the position of the jet is equivalent to the position of this motor. In
    order to simulate a flucuating jet, ``jet_noise`` can be modified to
    introduced to add Gaussian noise on top of the injector position when
    considering the jet position

    3. If the jet position, including its ``jet_width``, is within range to
    of the ``beam_position``, the total ADU of the detector is determined via a
    Gaussian distribution with width controlled via ``adu_sigma`` and height
    scaled by both ``adu_max`` and the current ``beam_energy`` reading. The
    detector will never report less than ``adu_floor``.

    4. If the jet and the beam are considered non-overalapping, ``adu_floor``
    is returned.

    Examples
    --------
    Draw a quick scan through the distribution where the only noise is in the
    energy of the beam

    >>> import matplotlib.pyplot as plt
    >>> import numpy as np
    >>> simulation = generate_simulation(jet_noise=0.,
    ...                                  drop_rate=0.,
    ...                                  energy_noise=0.4)
    >>> positions = np.linspace(-1, 1, 250)
    >>> values = []
    >>> for position in positions:
    ...     simulation.inj_x.set(position)
    ...     simulation.cspad_adu.trigger()
    ...     values.append(simulation.cspad_adu.get())
    >>> plt.plot(positions, values, facecolors='none', edgecolors='blue')
    >>> plt.show()

    """
    # Input parameters
    params = SimpleNamespace(beam_position=beam_position,
                             adu_max=adu_max, adu_sigma=adu_sigma,
                             jet_width=jet_width, jet_noise=jet_noise,
                             adu_floor=adu_floor)
    beam = BeamSignal(name='beam',
                      value=beam_energy,
                      noise=energy_noise,
                      drop_rate=drop_rate)

    inj_x = SynAxis(name='inj_x', precision=motor_precision)

    def func():
        # Current jet position with noise
        jet_position = inj_x.read()['inj_x']['value']
        if params.jet_noise:
            jet_position += np.random.normal(0., params.jet_noise)
        # If we are in a position to to see a signal
        if np.isclose(jet_position,
                      params.beam_position,
                      atol=params.jet_width / 2.):
            adu = np.exp(-(jet_position - params.beam_position) ** 2
                         / (2 * params.adu_sigma ** 2))
            # Current energy with noise
            current_energy = beam.read()['beam']['value']
            # Scale by beam energy, but always report the floor
            return max(current_energy * adu * params.adu_max, params.adu_floor)
        # Not on jet means no signal
        else:
            return params.adu_floor

    cspad_adu = SynSignal(name='cspad_adu', func=func)
    return SimpleNamespace(inj_x=inj_x,
                           beam=beam,
                           cspad_adu=cspad_adu,
                           params=params)


# Create convenient namespaces
simulation = generate_simulation()
noiseless_simulation = generate_simulation(energy_noise=0.,
                                           jet_noise=0.,
                                           drop_rate=0.)
