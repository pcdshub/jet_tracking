import cv2
import numpy as np


def read_noise(image, amount, gain=1):
    """
    Generate simulated read noise.

    Parameters
    ----------

    image: numpy array
        noise array should match the image shape.
    amount: float
        amount of read noise, in electrons.
    gain: float, optional
        gain of te camera, in units of electrons/ADU.
    """
    shape = image.shape
    noise = np.random.randint(0, 255, size=shape, dtype=np.uint8)
    ret, thresh = cv2.threshold(noise, 240, 255, cv2.THRESH_BINARY)
    noise_image = image + thresh
    return noise_image


def jet_display(img, mp, jet_center, pix_per_mm, x_size):
    diff = ((mp - jet_center)/2)*pix_per_mm  # negative - mp is left of jc
    pix_position = int((x_size/2) + (diff))
    for i in range(len(img)):
        img[i][pix_position] = 255
    kernel = np.ones((5, 5), np.uint8)
    img = cv2.dilate(img, kernel, iterations=2)
    img = read_noise(img, 500, 1)
    kernel = np.ones((5, 5), np.uint8)
    erode = cv2.erode(img, kernel, iterations=2)
    kernel = np.ones((3, 3), np.uint8)
    blackhat = cv2.morphologyEx(img, cv2.MORPH_BLACKHAT, kernel)
    final_image = img + blackhat + erode
    #final_image = img
    return final_image
