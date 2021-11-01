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

class MotorAction(object):
    def __init__(self, motor_thread, context, signals):
        self.context = context
        self.signals = signals
        self.motor_thread = motor_thread
        self.ternary_search = TernarySearch(self.motor_thread)
        self.basic_scan = BasicScan(self.motor_thread, signals)
        self.motor = self.motor_thread.motor
        self.last_direction = "none" # positive or negative or none
        self.new_direction = "none" # positive or negative or none
        self.last_position = 0
        self.new_position = 0
        self.last_intensity = 0
        self.new_intensity = 0
        self.last_distance_from_image_center = 0
        self.new_distance_from_image_center = 0

    def execute(self):
        if self.motor_thread.algorithm == "Ternary Search":
            self.ternary_search.search()
            if self.ternary_search.done:
                return(True, self.ternary_search.max_value)
            else: return(False, self.ternary_search.max_value)
        elif self.motor_thread.algorithm == "Basic Scan":
            self.basic_scan.scan()
            if self.basic_scan.done:
                return(True, self.basic_scan.max_value)
            else: return(False, self.basic_scan.max_value)


class BasicScan(object):
    def __init__(self, motor_thread, signals):
        self.motor_thread = motor_thread
        self.signals = signals
        self.beginning = True
        self.original_intensity = 0
        self.original_position = 0
        self.max_value = 0
        self.step_size = self.motor_thread.step_size
        self.ll = float(self.motor_thread.low_limit)
        self.hl = float(self.motor_thread.high_limit)
        self.done = False
        self.step = 0
        self.num_tries = 1

    def check_motor_options(self):
        self.ll = float(self.motor_thread.low_limit)
        self.hl = float(self.motor_thread.high_limit)
        self.step_size = self.motor_thread.step_size

    def get_original_values(self):
        if self.beginning:
            self.original_intensity = self.motor_thread.moves[-1][0]
            self.original_position = self.motor_thread.moves[-1][1]
            self.beginning = False

    def scan(self):
        """does a basic scan from the low limit to one step below the high limit
        in steps if step_size"""
        self.check_motor_options()
        self.get_original_values()
        print(self.motor_thread.moves[-1][1] + self.step_size, self.hl)
        if self.motor_thread.moves[-1][1] + self.step_size > self.hl:
            moves_reorg = list(map(list, (zip(*self.motor_thread.moves))))
            intensities = moves_reorg[0]
            self.max_value = max(intensities)
            index = intensities.index(self.max_value)
            max_location = moves_reorg[1][index]
            if self.max_value > self.original_intensity:
                self.motor_thread.motor.move(max_location, wait=False)
                self.done = True
                self.beginning = True
            else:
                self.step_size = self.step_size - 0.005
                if self.step_size < 0.001: # for CXI - should not get any smaller than 1/5 size of jet
                    self.signals.message.emit("Did not find a better value, returning to original position")
                    self.motor_thread.motor.move(self.original_position, wait=False)
                    self.done = True
                    self.beginning = True
                else:
                    self.num_tries += 1
                    self.signals.message.emit(f"Trying linear scan again, Try {self.num_tries}... 0.005 mm smaller step size")
                    self.step = 0
        else:
            position = self.ll + (self.step*self.step_size)
            self.motor_thread.motor.move(position, wait=False)
            self.step += 1


class TernarySearch(object):
    def __init__(self, motor_thread):
        self.motor_thread = motor_thread
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

    def check_motor_options(self):
        self.abs_ll = float(self.motor_thread.low_limit)
        self.abs_hl = float(self.motor_thread.high_limit)
        self.tolerance = self.motor_thread.tolerance
        if self.beginning:
            self.low = self.abs_ll
            self.high =self.abs_hl
            self.beginning = False

    def find_mids(self, low, high):
        if low < self.abs_ll:
            low = self.abs_ll
        if high > self.abs_hl:
            high = self.abs_hl
        print(low, high, abs(high-low))
        self.mid1 = ((low + (high - low)) / 3.0) + low
        self.mid2 = ((high - (high - low)) / 3.0) + high
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
            self.motor_thread.motor.move((self.high + self.low)*0.5, wait=False)
            self.done = True
            self.beginning = True

    def move_to_mid1(self):
        """Move toward low limit"""
        self.motor_thread.motor.move(self.mid1, wait=False)

    def move_to_mid2(self):
        """Move toward high limit"""
        self.motor_thread.motor.move(self.mid2, wait=False)

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
'''
    def _search(motor, intensity, absolute, left, right, tol, nsamp):
        # this needs quite a bit more thought...
        # right now I am thinking about the signals and dictionary
        # to track moves and to graph the points as the motor is moving
        # do we need to pass signals and that dictionary of motor moves
        # into all of these functions or is there a better way?
        # maybe all we need is signals and that can handle everything
        # I also believe that the recursive function was not correct
        # the way it was written because it was not passing the correct
        # absolute motor position in the case of i1 < i2
        #
        # also... another way to possibly make sure that the motor doesn't
        # get too far away from the peak when it is searching is to always
        # check the dictionary of moves and basically check every couple
        # of moves if it's very far off from the highest value in the
        # list of moves??

        if abs(right - left) < tol:
            motor.move(((left + absolute) + (right + absolute)) / 2)
            return (self.motor.position, self.average_int(nsamp))
        left_third = (2 * left + right) / 3
        right_third = (left + 2 * right) / 3
        motor.move(left_third + absolute, wait=True)
        left_p = self.motor.position
        i1 = self.average_int(nsamp)
        motor.move(right_third + absolute, wait=True)
        right_p = self.motor.position
        i2 = self.average_int(nsamp)
        moves.extend([(left_p, i1), (right_p, i2)])
        if i1 < intensity and i2 < intensity:
            signals.message.emit('neither direction was better!: ' + intensity + ' > ' \
                                 + str(i1) + ' and ' + str(i2) \
                                 + '\n' + 'left position:  ' + str(left_p) + ' \n' \
                                 + 'right position:  ' + str(right_p) + ' \n')
            return (_search(motor, intensity, absolute, right, tol, nsamp))
        if i1 < i2:
            signals.message.emit("i1<i2:  " + str(i1) + ' < ' + str(i2) \
                                 + '\n' + 'left position:  ' + str(left_p) + ' \n' \
                                 + 'right position:  ' + str(right_p) + ' \n')
            return (_search(motor, intensity, left_p, left_third, right, tol, nsamp))
        else:
            signals.message.emit("i1>i2:  " + str(i1) + ' > ' + str(i2) \
                                 + '\n' + 'left position:  ' + str(left_p) + ' \n' \
                                 + 'right position:  ' + str(right_p) + ' \n'))
            return (_search(motor, intensity, right_p, right_third, left, tol, nsamp))


    """
    def _search(self, absolute, left, right, tol, nsamp):
        if abs(right - left) < tol:
            self.motor.move(((left+absolute)+(right+absolute))/2)
            return(self.motor.position, self.average_int(nsamp))
        left_third = (2*left + right) / 3
        right_third = (left + 2*right) / 3
        self.motor.move(left_third+absolute, wait=True)
        left_p = self.motor.position
        i1 = self.average_int(nsamp)
        self.motor.move(right_third+absolute, wait=True)
        right_p = self.motor.position
        i2 = self.average_int(nsamp)
        self.moves.extend([(left_p, i1), (right_p, i2)])
        if i1 < i2:
    
            self.signals.message.emit("i1<i2" + "left position: " + str(left_p) + " \n" + str(i1) + "right position: " + str(right_p) + " \n" + str(i2))
            return(self._search(right_p, left_third, right, tol, nsamp))
        else:
            self.signals.message.emit("i1>i2" + "left position: " + str(left_p) + " \n" + str(i1) + "right position: " + str(right_p) + " \n" + str(i2))
            return(self._search(left_p, right_third, left, tol, nsamp))
    
    """


    def _scan(motor, left, right, step_size, nsamp):
        moves =
        i1 = average_int(nsamp)
        m1 = motor.position
        motor.move(left, wait=True)


    def backlash_scan(self, left, right, tol, nsamp):
        # scans in positive direction in steps of tol
        # until the intensity starts going down
        i1 = self.average_int(nsamp)
        m1 = self.motor.position
        self.motor.move(tol, wait=True)
        i2 = self.average_int(nsamp)
        m2 = self.motor.position
        self.moves.extend([(m1, i1), (m2, i2)])
        if i1 < i2:  # shot 1 is i1 and shot 2 is i2
            while i1 < i2:
                print("i1<i2", i1, i2)
                i1 = self.average_int(nsamp)
                self.position_left = self.motor.position
                self.motor.move(tol, wait=True)
                i2 = self.average_int(nsamp)
                self.position_right = self.motor.position
                self.moves.extend([(m2, i2)])
                print(self.moves)
            # this is for graphing purposes to prove that the peak was found
            # it should be commented out after full testing
            i = 0
            for i in range(5):
                i += 1
                self.motor.move(tol, wait=True)
                self.moves.append([(self.motor.position, self.average_int(nsamp))])
            self.motor.move(self.position_left, wait=True)
            return (self.position_left)

        else:  # go back and move right
            # makes a large step to the negative position
            # ideally such that it goes OVER the peak
            #
            self.motor.move(left, wait=True)
            i1 = self.average_int(nsamp)
            m1 = self.motor.position
            self.motor.move(tol, wait=True)
            i2 = self.average_int(nsamp)
            m2 = self.motor.position
            self.moves.extend([(m1, i1), (m2, i2)])
            print(i1, i2)
            if i1 < i2:
                while i1 < i2:
                    i1 = self.average_int(nsamp)
                    self.position_left = self.motor.position
                    self.motor.move(tol, wait=True)
                    i2 = self.average_int(nsamp)
                    self.position_right = self.motor.position
                    self.moves.extend([(m2, i2)])
                    print(self.moves)
                i = 0
                for i in range(5):
                    i += 1
                    self.motor.move(tol, wait=True)

'''