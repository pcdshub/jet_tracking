import math
import random


class SimulationGenerator(object):
    def __init__(self, context, signals):

        # initial values from the control widget
        self.context = context
        self.signals = signals
        self.percent_dropped = 10
        self.peak_intensity = 10
        self.motor_position = 0
        self.radius = 0.025
        self.center = 0.03
        self.max = 10
        self.bg = 0.05
        self.percent = 0
        # get current simulated motor position
        self.signals.update.connect(self.updateVals)
        # self.signals.changeMotorPosition.connect(self.change_motor)
        self.signals.changeMotorPosition.connect(self.change_position)
        self.signals.changeDroppedShots.connect(self.change_dropped)
        self.signals.changePeakIntensity.connect(self.change_intensity)
        self.signals.changeJetRadius.connect(self.change_radius)
        self.signals.changeJetCenter.connect(self.change_center)
        self.signals.changeMaxIntensity.connect(self.change_max)
        self.signals.changeBackground.connect(self.change_noise)

    def change_position(self, position):
        self.motor_position = position

    def change_motor(self, motor_position):
        self.motor_position = motor_position

    def change_dropped(self, percent_dropped):
        self.percent_dropped = percent_dropped

    def change_intensity(self, peak_intensity):
        self.peak_intensity = peak_intensity

    def change_radius(self, radius):
        self.radius = radius

    def change_center(self, center):
        self.center = center

    def change_max(self, maxi):
        self.max = maxi

    def change_noise(self, bg):
        self.bg = bg

    def updateVals(self, name, vals):
        if name == "percent":
            self.percent_dropped = vals
        elif name == "peak":
            self.peak_intensity = vals
        elif name == "motor_position":
            self.motor_position = vals
        elif name == "radius":
            self.radius = vals
        elif name == "center":
            self.center = vals
        elif name == "max":
            self.max = vals
        elif name == "background":
            self.bg = vals

    def sim(self):

        val = {}
        val["i0"] = self.peak_intensity
        val["diff"] = self.max
        val["ratio"] = 1
        val["dropped"] = False

        a = random.random()
        # dropped shots. for input percentage of shots, 0 is returned for the
        # scattering intensity
        b = random.random()
        c = random.random()
        self.percent = self.percent_dropped/100

        # dropped shots
        if b < self.percent:
            # val["diff"] = 0
            val["dropped"] = True
            val["diff"] = (self.bg / 10) * (1 + (a - 0.5))
            val["i0"] = self.bg * (1 + (c - 0.5))

        # on jet
        else:
            # calculates length of chord of a circle if on jet or sets diff
            # to 0 (plus noise) if off jet
            if abs(self.motor_position - self.center) < self.radius:
                val["diff"] = (self.max * ((2 * math.sqrt(self.radius ** 2 -
                               abs(self.motor_position - self.center) ** 2)) /
                               (2 * self.radius)) * (1 + self.bg * (a - 0.5)))
                val["dropped"] = False
                val["i0"] = self.peak_intensity * 1 + self.bg * (c - 0.5)

            # off jet
            else:
                val["diff"] = self.bg * (1 + (a - 0.5))
                val["dropped"] = False
                val["i0"] = self.peak_intensity * 1 + self.bg * (c - 0.5)

        val["ratio"] = val["diff"] / val["i0"]
        return val
