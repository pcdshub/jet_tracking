from .cam_utils import get_nozzle_shift


def movex(motor, dist):
    """Moves motor a certain distance in the x-direction

    Parameters
    ----------
    motor : EpicsSignal
        The motor
    dist : float
        The distance in millimeters
    """
    pos = motor.get()
    motor.put(pos + dist)


def pi_moving_test_script(motor, cam, params, im0 = None, min_shift = 1):
    """Moves the motor back to original position when shift is large enough

    Parameters
    ----------
    motor : EpicsSignal
        The motor to be moved
    cam : Questar
        Camera for getting the images
    params : dict
        Dictionary of PVs (pxsize and cam_roll)
    im0 : ndarray, optional
        Camera image at the beginning
    min_shift : float
        Minimum shift in mm to trigger motor movement

    """

    if not im0:
        im0 = cam.image.image
    while True:
        try:
            im = cam.image.image
            shift = get_nozzle_shift(im0, im, params)
            if shift[1] > min_shift:
                movex(motor, -shift[1])
                print('moving')
                im0 = im
        except KeyboardInterrupt:
            return
