import os.path

import numpy as np
import pandas as pd
import pytest
from jet_tracking.sim import generate_simulation


@pytest.fixture(scope='session')
def simulated_data():
    return pd.read_csv(os.path.join(os.path.dirname(__file__), 'sim.csv'))


def test_generate_simulation(simulated_data):
    ns = generate_simulation('x', 'y', simulated_data,
                             motor_precision=0,
                             random_state=np.random.RandomState(0))
    assert ns.motor.precision == 0
    # Set our motor
    ns.motor.set(4)

    # Grab ten readings
    values = list()
    for i in range(10):
        ns.signal.trigger()
        values.append(ns.signal.get())

    possible_values = ns.data[ns.data['x'] == 4]['y'].unique()
    assert len(set(values)) == len(possible_values)
    assert all(val in possible_values for val in values)
