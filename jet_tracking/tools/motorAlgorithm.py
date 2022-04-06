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
logger = logging.getLogger(__name__)


class LinearTernary(object):
    def __init__(self, motor_thread, context, signals):
        self.motor_thread = motor_thread
        self.context = context
        self.signals = signals
        self.beginning = True
        self.original_intensity = 0
        self.original_position = 0
        self.max_value = 0
        self.step_size = self.motor_thread.step_size
        self.ll = float(self.motor_thread.low_limit)
        self.hl = float(self.motor_thread.high_limit)
        self.done = False
        self.step = 1
        self.num_tries = 1

    def search(self):
        self.basic_scan()
        if self.basic_scan.done:
            self.ternary_search.search()
            if self.ternary_search.done:
                # need to update ll and hl to smaller values
                self.linear_ternary.max_value = self.ternary_search.max_value
                self.done = True


class DynamicLinear(object):
    def __init__(self, motor_thread, context, signals):
        self.motor_thread = motor_thread
        self.context = context
        self.signals = signals
        self.beginning = True
        self.original_intensity = 0
        self.original_position = 0
        self.max_value = 0
        self.max_location = 0
        self.step_size = self.motor_thread.step_size
        self.ll = float(self.motor_thread.low_limit)
        self.hl = float(self.motor_thread.high_limit)
        self.done = False
        self.step = 1
        self.num_tries = 1
        self.make_connections()

    def make_connections(self):
        pass

    def end_scan(self):
        self.done = True
        self.beginning = True

    def check_motor_options(self):
        self.ll = float(self.motor_thread.low_limit)
        self.hl = float(self.motor_thread.high_limit)
        if self.num_tries == 1:
            self.step_size = self.motor_thread.step_size

    def start_fresh(self):
        print('Resettting values...')
        self.done = False
        self.step = 1
        self.num_tries = 1
        self.max_value = 0
        self.original_intensity = self.motor_thread.moves[-1][0]
        self.original_position = self.motor_thread.moves[-1][1]
        self.beginning = False

    def find_max_location(self):
        if not self.motor_thread.moves:
            moves_reorg = list(map(list, (zip(*self.motor_thread.moves))))
            intensities = moves_reorg[0]
            self.max_value = max(intensities)
            self.min_value = min(intensities)
            index = intensities.index(self.max_value)
            max_location = moves_reorg[1][index]
            return max_location
        else:
            return self.motor_thread.motor.position

    def move_to_max(self):
        max_location = self.find_max_location()
        self.motor_thread.motor.move(max_location, self.motor_thread.wait)

    def scan(self):
        """does a basic scan from the low limit to one step below the high limit
        in steps if step_size"""
        self.check_motor_options()
        self.start_fresh()
        print(f"next position: {self.motor_thread.moves[-1][1] + self.step_size}, limit:{self.hl}")
        if self.beginning:
            self.start_fresh()
            self.beginning = False
            self.motor_thread.motor.move(self.ll, self.motor_thread.wait)
        elif self.motor_thread.moves[-1][1] + self.step_size < self.hl and not self.beginning:
            position = self.ll + (self.step * self.step_size)
            self.motor_thread.motor.move(position, self.motor_thread.wait)
            self.context.update_read_motor_position(self.motor_thread.motor.position)
            self.step += 1
            print("next step")
        elif self.motor_thread.moves[-1][1] + self.step_size > self.hl and not self.beginning:
            max_location = self.find_max_location()
            print(f"max value: {self.max_value}, original_intensity: {self.original_intensity}")
            if self.max_value > self.original_intensity:
                self.motor_thread.motor.move(max_location, self.motor_thread.wait)
                self.context.update_read_motor_position(self.motor_thread.motor.position)
                self.done = True
                self.beginning = True
                print("Over original, done!")
            else:
                self.step_size = self.step_size - 0.02
                if self.step_size <= 0.02:  # for CXI - should not get any smaller than 1/5 size of jet
                    self.signals.message.emit("Did not find a better value, returning to original position")
                    print("Did not find a better value, returning to original position")
                    self.motor_thread.motor.move(self.original_position, self.motor_thread.wait)
                    self.context.update_read_motor_position(self.motor_thread.motor.position)
                    self.done = True
                    self.beginning = True
                else:
                    self.num_tries += 1
                    self.signals.message.emit(
                        f"Trying linear scan again, Try {self.num_tries}... 0.005 mm smaller step size")
                    print(f"Trying linear scan again, Try {self.num_tries}... 0.005 mm smaller step size")
                    self.step = 1


class BasicScan(object):
    def __init__(self, motor_thread, context, signals):
        self.motor_thread = motor_thread
        self.context = context
        self.signals = signals
        self.beginning = True
        self.original_intensity = 0
        self.original_position = 0
        self.min_value = 0
        self.max_value = 0
        self.step_size = self.motor_thread.step_size
        self.ll = float(self.motor_thread.low_limit)
        self.hl = float(self.motor_thread.high_limit)
        self.done = False
        self.step = 1
        self.num_tries = 1
        self.make_connections()

    def make_connections(self):
        pass

    def end_scan(self):
        self.done = True
        self.beginning = True

    def check_motor_options(self):
        self.ll = float(self.motor_thread.low_limit)
        self.hl = float(self.motor_thread.high_limit)
        if self.num_tries == 1:
            self.step_size = self.motor_thread.step_size

    def find_max_location(self):
        if self.motor_thread.moves:
            moves_reorg = list(map(list, (zip(*self.motor_thread.moves))))
            intensities = moves_reorg[0]
            self.max_value = max(intensities)
            self.min_value = min(intensities)
            index = intensities.index(self.max_value)
            max_location = moves_reorg[1][index]
            return max_location
        else:
            return self.motor_thread.motor.position

    def move_to_max(self):
        max_location = self.find_max_location()
        self.motor_thread.motor.move(max_location, self.motor_thread.wait)
        self.context.update_read_motor_position(self.motor_thread.motor.position)

    def start_fresh(self):
        print('Resettting values...')
        self.done = False
        self.step = 1
        self.num_tries = 1
        self.max_value = 0
        self.original_intensity = self.motor_thread.moves[-1][0]
        self.original_position = self.motor_thread.moves[-1][1]

    def scan(self):
        """does a basic scan from the low limit to one step below the high limit
        in steps if step_size"""
        self.check_motor_options()
        print(f"next position: {self.motor_thread.moves[-1][1] + self.step_size}, limit:{self.hl}")
        if self.beginning:
            self.start_fresh()
            self.beginning = False
            self.motor_thread.motor.move(self.ll, self.motor_thread.wait)
            self.context.update_read_motor_position(self.motor_thread.motor.position)
        elif self.motor_thread.moves[-1][1] + self.step_size < self.hl and not self.beginning:
            position = self.ll + (self.step * self.step_size)
            self.motor_thread.motor.move(position, self.motor_thread.wait)
            self.context.update_read_motor_position(self.motor_thread.motor.position)
            self.step += 1
            print("next step")
        elif self.motor_thread.moves[-1][1] + self.step_size > self.hl and not self.beginning:
            max_location = self.find_max_location()
            print(f"max value: {self.max_value}, original_intensity: {self.original_intensity}")
            if self.max_value > self.original_intensity:
                self.motor_thread.motor.move(max_location, self.motor_thread.wait)
                self.context.update_read_motor_position(self.motor_thread.motor.position)
                self.end_scan()
                print("Over original, done!")
            else:
                self.step_size = self.step_size - 0.02
                if self.step_size <= 0.02:  # for CXI - should not get any smaller than 1/5 size of jet
                    self.signals.message.emit("Did not find a better value, returning to original position")
                    print("Did not find a better value, returning to original position")
                    self.motor_thread.motor.move(self.original_position, self.motor_thread.wait)
                    self.context.update_read_motor_position(self.motor_thread.motor.position)
                    self.end_scan()
                else:
                    self.num_tries += 1
                    self.signals.message.emit(
                        f"Trying linear scan again, Try {self.num_tries}... 0.005 mm smaller step size")
                    print(f"Trying linear scan again, Try {self.num_tries}... 0.005 mm smaller step size")
                    self.motor_thread.motor.move(self.ll, self.motor_thread.wait)
                    self.context.update_read_motor_position(self.motor_thread.motor.position)
                    self.step = 1


class TernarySearch(object):
    def __init__(self, motor_thread, signals):
        logger.info("TernarySearch object created.")
        self.motor_thread = motor_thread
        self.signals = signals
        self.beginning = True
        self.done = False
        self.max_value = 0
        self.step = 0
        self.smart_check_vals = []
        self.abs_ll = float(self.motor_thread.low_limit)
        self.abs_hl = float(self.motor_thread.high_limit)
        self.tolerance = self.motor_thread.tolerance
        self.low = 0
        self.high = 0
        self.mid1 = 0
        self.mid2 = 0
        self.make_connections()

    def make_connections(self):
        pass

    def end_scan(self):
        self.done = True
        self.beginning = True

    def check_motor_options(self):
        self.abs_ll = float(self.motor_thread.low_limit)
        self.abs_hl = float(self.motor_thread.high_limit)
        self.abs_ll = min(self.abs_ll, self.abs_hl)
        self.abs_hl = max(self.abs_ll, self.abs_hl)
        self.tolerance = self.motor_thread.tolerance
        if self.beginning:
            self.max_value = 0
            self.done = False
            self.step = 0
            self.smart_check_vals = []
            self.low = self.abs_ll
            self.high = self.abs_hl
            self.beginning = False

    def find_mids(self, low, high):
        if low < self.abs_ll:
            low = self.abs_ll
        if high > self.abs_hl:
            high = self.abs_hl
        print(low, high, abs(high - low))
        self.mid1 = low + abs(high - low) / 3.0
        self.mid2 = high - abs(high - low) / 3.0
        print(self.mid1, self.mid2)

    def compare_to_old(self):
        if self.smart_check_vals[0] > self.motor_thread.moves[-1][0]:
            self.try_again()

    def try_again(self):
        """puts the low and high limits back with the range slightly
        reduced to get new values"""
        self.abs_ll = self.motor_thread.low_limit + 0.0005
        self.abs_hl = self.motor_thread.high_limit - 0.0005

    def search(self):
        self.check_motor_options()
        if self.step == 3:
            self.compare_and_move()
            self.step = 0
        if self.step == 2:
            self.move_to_mid2()
            self.step += 1
        if self.step == 1:
            self.move_to_mid1()
            self.step += 1
        if self.step == 0:
            if len(self.smart_check_vals) != 0:
                self.compare_to_old()
            self.find_mids(self.low, self.high)
            self.check_if_done()
            self.step += 1

    def check_if_done(self):
        if abs(self.high - self.low) < self.motor_thread.tolerance:
            self.motor_thread.motor.move((self.high + self.low) * 0.5, self.motor_thread.wait)
            self.context.update_read_motor_position(self.motor_thread.motor.position)
            self.end_scan()

    def move_to_mid1(self):
        """Move toward low limit"""
        self.motor_thread.motor.move(self.mid1, self.motor_thread.wait)
        self.context.update_read_motor_position(self.motor_thread.motor.position)

    def move_to_mid2(self):
        """Move toward high limit"""
        self.motor_thread.motor.move(self.mid2, self.motor_thread.wait)
        self.context.update_read_motor_position(self.motor_thread.motor.position)

    def compare_and_move(self):
        i1 = self.motor_thread.moves[-2][0]
        i2 = self.motor_thread.moves[-1][0]
        print(i1, i2)
        if i1 > i2:
            self.low = self.low
            self.high = self.mid2
            self.max_value = i1
        elif i1 < i2:
            self.low = self.mid1
            self.high = self.high
            self.max_value = i2

