import math
import statistics
import random
import matplotlib.pyplot as plt
import time
import logging

log = logging.getLogger(__name__)


def average_intensity(self, nsamp):
    i0 = []
    for i in range(nsamp):
        i0.append(self.ratio.get())
        time.sleep(1 / 15)
    return statistics.mean(i0)


def sim_linear(motor, left, right, step_size, nsamp):


def sim_ternary(motor, intensity, absolute, left, right, tol, nsamp)

