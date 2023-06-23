import logging
import time

log = logging.getLogger(__name__)


class SimulatedMotor:
    def __init__(self, context, signals):

        # initial values from the control widget
        self.context = context
        self.signals = signals
        self.position = 0
        self.wait = 1
        self.update_position()

    def move(self, position, wait=False):
        self.position = position
        if wait:
            time.sleep(self.wait)

    def update_position(self):
        self.position = self.context.motor_position
        return self.position
