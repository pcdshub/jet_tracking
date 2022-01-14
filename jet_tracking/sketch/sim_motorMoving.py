import logging
import time

log = logging.getLogger(__name__)


class SimulatedMotor(object):
    def __init__(self, context, signals):

        # initial values from the control widget
        self.context = context
        self.signals = signals
        self.position = 0
        self.i0 = 0
        self.i0_ave = 0
        self.left = -0.1
        self.right = 0.1
        self.step = 0.01
        self.wait = 5

    def move(self, position, wait=False):
        self.position = position
        if wait:
            time.sleep(self.wait)
        self.signals.changeMotorPosition.emit(self.position)

    def position(self):
        return self.position