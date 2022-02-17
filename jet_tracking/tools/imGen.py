import numpy as np
import cv2


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
    noise = np.random.normal(scale=amount/gain, size=shape)
    noise_image = image + noise
    return noise_image


def jet_display(img, mp, jet_center, pix_per_mm, x_size):
    diff = ((mp - jet_center)/2)*pix_per_mm  # negative - mp is left of jc
    pix_position = int((x_size/2) + (diff))
    print(pix_position)
    for i in range(len(img)):
        img[i][pix_position] = 255
    kernel = np.ones((5, 5), np.uint8)
    dilation = cv2.dilate(img, kernel, iterations=2)

    return dilation

