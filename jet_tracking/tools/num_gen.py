import math
import random


def sinwv(x, shift):
    a = random.random()
    return(a*(math.sin(x)**2 + shift))
