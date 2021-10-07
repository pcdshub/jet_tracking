import math
import statistics
import random
import matplotlib.pyplot as plt
import time
import logging

log = logging.getLogger(__name__)

class SimulatedMotor(object)

    def __init__(self, context, signals):

        # initial values from the control widget
        self.context = context
        self.signals = signals
        self.motor_position = 0
        self.i0 = 0
        self.i0_ave = 0
        self.left = -0.1
        self.right = 0.1
        self.step = 0.01
        self.wait = 5
        # get current simulated motor position
#        self.signals.update.connect(self.updateVals)
        self.signals.changeMotorPosition.connect(self.change_motor)

#        self.make_connections()
#        self.set_sim_options()
#
#    def set_sim_options(self):
#        self.context.update_motor_position(float(self.motor_position))
#
#    def make_connections(self):
#        self.box_motor_pos.checkVal.connect(self.context.update_motor_position)

    def change_motor(self, motor_position):
        self.motor_position = motor_position

    def average_intensity(self, nsamp):
        i0 = []
        for i in range(nsamp):
            i0.append(self.ratio.get())
            time.sleep(1 / 15)
        return statistics.mean(i0)


    def sim_linear(self):
        self.motor_position = self.left
        self.i0_pt = []
        while self.motor_position <= self.right:
            while t <
                self.i0_pt.append(self.i0.get())
                self.i0_ave =


    def sim_ternary(self):
        print("ternary search")


    def sim_test(self):
        print("you are now tracking")
        time.sleep(5)
        self.motor_position = 0.03

