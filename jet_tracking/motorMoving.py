"""Algorithms for Motor Moving

These function definitions are created to allow for different
mechanisms for motor moving to be tested in the various
hutches. It is assumed for each of them that the motor
and a dictionary of values including the range (left and right
limits from the GUI), tolerance, and number of values to average
for each move are included in that dictionary.

This file requires that _____ be installed within the python
environment you are running this script in

this file can also be imported as a module and contains the
following functions:
*
"""

import logging

from .tools.motorAlgorithm import (BasicScan, DynamicLinear, LinearTernary,
                                   TernarySearch)

logger = logging.getLogger(__name__)


class MotorAction:
    def __init__(self, motor_thread, context, signals):
        self.context = context
        self.signals = signals
        self.motor_thread = motor_thread
        self.ternary_search = TernarySearch(self.motor_thread, context, signals)
        self.basic_scan = BasicScan(self.motor_thread, context, signals)
        self.linear_ternary = LinearTernary(self.motor_thread, context, signals)
        self.dyn_linear = DynamicLinear(self.motor_thread, context, signals)
        self.motor = self.motor_thread.motor
        self.stop_search = False
        self.last_direction = "none"   # positive or negative or none
        self.new_direction = "none"  # positive or negative or none
        self.last_position = 0
        self.new_position = 0
        self.last_intensity = 0
        self.new_intensity = 0
        self.last_distance_from_image_center = 0
        self.new_distance_from_image_center = 0
        self.make_connections()

    def make_connections(self):
        self.signals.endEarly.connect(self.stop_the_search)

    def stop_the_search(self):
        self.stop_search = True

    def execute(self):
        if self.motor_thread.algorithm == "Ternary Search":
            if self.stop_search:
                self.stop_search = False
                return True, self.ternary_search.max_value
            self.ternary_search.search()
            if self.ternary_search.done:
                return True, self.ternary_search.max_value
            return False, self.ternary_search.max_value

        if self.motor_thread.algorithm == "Basic Scan":
            if self.stop_search:
                self.basic_scan.move_to_max()
                self.stop_search = False
                return True, self.basic_scan.max_value
            self.basic_scan.scan()
            if self.basic_scan.done:
                return True, self.basic_scan.max_value
            return False, self.basic_scan.max_value

        if self.motor_thread.algorithm == "Linear + Ternary":
            if self.stop_search:
                self.stop_search = False
                return True, self.linear_ternary.max_value
            self.linear_ternary.search()
            if self.linear_ternary.done:
                return True, self.linear_ternary.max_value
            return False, self.linear_ternary.max_value

        if self.motor_thread.algorithm == "Dynamic Linear Scan":
            if self.stop_search:
                self.stop_search = False
                return True, self.dyn_linear.max_value
            self.dyn_linear.scan()
            if self.dyn_linear.done:
                return True, self.dyn_linear.max_value
            return False, self.dyn_linear.max_value

        self.signals.message.emit("That algorithm does not exist yet..")
        self.stop_search = True
        return True, self.motor_thread.motor.position
