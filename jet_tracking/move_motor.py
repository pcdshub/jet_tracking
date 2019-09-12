import ophyd


def movex(motor, dist):
    """Moves motor a certain distance in the x-direction

    Parameters
    ----------
    motor : EpicsSignal
        The motor
    dist : float
        The distance in millimeters
    """
    if isinstance(motor, ophyd.PositionerBase):
        pos = motor.user_setpoint.get()
        motor.set(pos + dist, wait=True)
    else:
        pos = motor.get()
        motor.put(pos + dist)
