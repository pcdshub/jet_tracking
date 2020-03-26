# methods for jet tracking

import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt


def gaussianslope(x, a, mean, std, m, b):
  '''
  Define the function for a Gaussian on a slope (Gaussian + linear)

  Parameters
  ----------
  x : float
    x-coordinate
  a : float
    amplitude of Gaussian
  mean : float
    mean of Gaussian
  std : float
    standard deviation of Gaussian
  m : float
    slope of linear baseline
  b : float
    y-intercept of linear baseline

  Returns
  -------
  y : float
    the y-coordinate for the given x-coordinate as defined by the
    parameters given for the Gaussian on a slope
  '''

  return (a * np.exp(-((x-mean) / 2 / std) ** 2)) + (m * x + b)


def fit_cspad(azav, norm, gas_det):
  '''
  Fit the Azimuthal average of the CSPAD to a Gaussian on a slope

  Parameters
  ----------
  azav : ndarray
    Azimuthal average for CSPAD
  norm : ndarray
    number of pixels in each qbin
  gas_det : float
    gas detector  

  Returns
  -------
  center : int
    radius of the diffraction ring
  intensity : float
    sum of qbins 5 above and below the center, normalized by gas detector
  '''

  # determine number of pixels in each qbin, only use qbins where pixels > 15
  start = 0
  end = len(norm)
  begin = end / 2
  for i in range(begin):
    a = begin - i
    b = begin + i
    if (norm[a] < 150) and (a > start):
      start = a
    if (norm[b] < 150) and (b < end):
      end = b

  x = np.arange(len(azav))

  # estimate mean and standard deviation for Gaussian
  n = len(x)
  mean = sum(x*azav) / sum(azav)
  std = np.sqrt(sum((x-mean)**2)/n)

  # estimate slope and y-intercept for linear baseline
  x0 = 50/2
  l = len(azav)
  x1 = l - (50/2)
  y0 = np.mean(azav[0:50])
  y1 = np.mean(azav[l-50:])
  m, b = np.polyfit((x0, x1), (y0, y1), 1)

  # fit Gaussian + linear to Azimuthal average; provide initial parameters
  popt, pcov = curve_fit(gaussianslope, x, azav, p0=[max(azav), mean, std, m, b])

  # calculate radius of ring and intensity of center 10 qbins
  center = int(round(popt[1]))
  intensity = sum(azav[center-5:center+5]) / gas_det

  # display fit
  plt.plot(x, azav, 'ro')
  plt.plot(x, gaussianslope(x, *popt), 'b-')
  plt.show()

  return center, intensity


def get_cspad(azav, r, gas_det):
  '''
  Get the intensity of the diffraction ring on the CSPAD

  Parameters
  ----------
  azav : ndarray
    Azimuthal average calculated from CSPAD
  r : int
    radius of diffraction ring
  gas_det : float
    gas detector

  Returns
  -------
  intensity : float
    sum of qbins 5 above and below the center, normalized by gas detector
  '''
  intensity = sum(azav[r-5:r+5]) / gas_det
  return intensity


def get_stopper(stopper):
  return stopper


def get_pulse_picker(pulse_picker):
  return pulse_picker


def get_wave8(wave8):
  return wave8


