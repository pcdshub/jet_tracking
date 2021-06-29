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
def average_intensity(self, nsamp):
   i0 = []
   for i in range(nsamp):
      i0.append(self.ratio.get())
      time.sleep(1/15)
   return(mean(i0))

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
        motor.move(((left+absolute)+(right+absolute))/2)
        return(self.motor.position, self.average_int(nsamp))
    left_third = (2*left + right) / 3
    right_third = (left + 2*right) / 3
    motor.move(left_third+absolute, wait=True)
    left_p = self.motor.position
    i1 = self.average_int(nsamp)
    motor.move(right_third+absolute, wait=True)
    right_p = self.motor.position
    i2 = self.average_int(nsamp)
    moves.extend([(left_p, i1), (right_p, i2)])
    if i1 < intensity and i2 < intensity: 
        signals.message.emit('neither direction was better!: ' + intensity + ' > '\
            + str(i1) + ' and ' + str(i2) \
            + '\n' + 'left position:  ' + str(left_p) + ' \n' \
            + 'right position:  ' + str(right_p) + ' \n')
        return(_search(motor, intensity, absolute, right, tol, nsamp))
    if i1 < i2:
        signals.message.emit("i1<i2:  " + str(i1) + ' < ' + str(i2) \
            + '\n' + 'left position:  ' + str(left_p) + ' \n' \ 
            + 'right position:  ' + str(right_p) + ' \n')
        return(_search(motor, intensity, left_p, left_third, right, tol, nsamp))
    else:
        signals.message.emit("i1>i2:  " + str(i1) + ' > ' + str(i2) \
            + '\n' + 'left position:  ' + str(left_p) + ' \n' \
            + 'right position:  ' + str(right_p) + ' \n'))
        return(_search(motor, intensity, right_p, right_third, left, tol, nsamp))

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
    if i1 < i2: #shot 1 is i1 and shot 2 is i2
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
            i+=1
            self.motor.move(tol, wait=True)
            self.moves.append([(self.motor.position, self.average_int(nsamp))])
        self.motor.move(self.position_left, wait=True)
        return(self.position_left)

    else: #go back and move right
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
                i+=1
                self.motor.move(tol, wait=True)

