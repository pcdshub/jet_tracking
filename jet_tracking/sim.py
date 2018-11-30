import numpy as np
from ophyd.sim import SynAxis, SynSignal


def generate_simulation(motor_column, signal_column, dataframe,
                        motor_precision=3, random_state=None):
    """
    Generate a simulation based on a provided DataFrame

    Use collected data to simulate the relationship between a single
    input and output variable. A ``SynAxis`` object will be returned that can
    be set to a specified precision. The value of the dependent variable is
    then determined by finding the closest position of the motor we have
    recorded and returning the corresponding value. If multiple readings were
    taken at this position one is randomly chosen.

    Parameters
    ----------
    motor_column: str
        The column of data that will be used as the independent variable. Will
        also be the name of the created motor

    signal_column: str
        The name of the column to be the dependent variable. Will also be the
        name of the created signal

    dataframe: pandas.DataFrame
        Data to use in simulation

    motor_precision: int, optional
        Limit the accuracy of the simulated motor

    random_state: np.random.RandomState, optional
        Seed the simulation
    """
    # Create our motor that will serve as the independent variable
    motor = SynAxis(name=motor_column, precision=motor_precision)

    # Create a function to return a random value from closest motor position
    motor_positions = dataframe[motor_column].unique()
    sim_data = dict(iter(dataframe.groupby(motor_column)))
    random_state = random_state or np.random.RandomState(0)

    def func():
        pos = motor.position
        closest_position = motor_positions[np.abs(motor_positions - pos).argmin()]
        return random_state.choice(sim_data[closest_position][signal_column])

    sig = SynSignal(name=signal_column, func=func)
    return (motor, sig)
