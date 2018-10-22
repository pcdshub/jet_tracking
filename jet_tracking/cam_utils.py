import numpy as np
import cv2

from scipy.signal import peak_widths
from skimage.feature import register_translation


def jet_detect(img):
    '''Finds the jet from the online camera roi using HoughLines

    Parameters
    ----------
    img : ndarray
        ROI of the on-axis image

    Returns
    -------
    rho : float
        Distance from (0,0) to the line in pixels
    theta : float
        Angle of the shortest vector from (0,0) to the line in radians
    '''
    c = 0
    while True:
        try:
            binary = (img / (img.mean() + 2 * img.std() * 0.90 ** c)).astype(np.uint8)
            lines = cv2.HoughLines(binary, 1, np.radians(0.25), 30)
            rho, theta = lines[0][0]
        except Exception:
            c += 1
            continue
        else:
            return rho, theta


def get_jet_z(rho, theta, roi_y, roi_z, *, pxsize, cam_y, cam_z, beam_y,
              beam_z, cam_pitch):
    '''
    Calculates the jet position at beam height in the main coordinate system
    in offaxis camera (z and pitch replace x and roll given camera orientation)

    Parameters
    ----------
    rho : float
        Distance from (0,0) to the line in pixels
    theta : float
        Angle of the shortest vector from (0,0) to the line in radians
    y_roi : int
        Y-coordinate of the origin of the ROI on the camera image in pixels
    z_roi : int
        Z-coordinate of the origin of the ROI on the camera image in pixels
    pxsize : float
        size of pixel in mm
    cam_y : float
        y-coordinate of camera position in mm
    cam_z : float
        z-coordinate of camera position in mm
    beam_y : float
        y-coordinate of x-ray beam in mm (usually 0)
    beam_z : float
        z-coordinate of x-ray beam in mm (usually 0)
    cam_pitch : float
        rotation of camera about x axis in radians

    Returns
    -------
    zj : float
        Jet position at the beam height in millimeters
    '''
    yb_roi = (1.0 / pxsize) * ((cam_y - beam_y) * np.cos(-cam_pitch) +
                               (cam_z - beam_z) * np.sin(-cam_pitch)) - roi_y
    # print('yb_roi: {}'.format(yb_roi))
    zj_roi = (rho - yb_roi * np.sin(theta)) / np.cos(theta)
    # print('zj_roi: {}'.format(zj_roi))
    z0_roi = (1.0 / pxsize) * (cam_z * np.cos(cam_pitch) -
                               cam_y * np.sin(-cam_pitch)) - roi_z
    zj = pxsize * (z0_roi - zj_roi)
    return zj


def get_jet_x(rho, theta, roi_x, roi_y, *, pxsize, cam_x, cam_y, beam_x,
              beam_y, cam_roll):
    '''Calculates the jet position at beam height in the main coordinate system

    Parameters
    ----------
    rho : float
        Distance from (0,0) to the line in pixels
    theta : float
        Angle of the shortest vector from (0,0) to the line in radians
    x_roi : int
        X-coordinate of the origin of the ROI on the camera image in pixels
    y_roi : int
        Y-coordinate of the origin of the ROI on the camera image in pixels
    pxsize : float
        size of pixel in mm
    cam_x : float
        x-coordinate of camera position in mm
    cam_y : float
        y-coordinate of camera position in mm
    beam_x : float
        x-coordinate of x-ray beam in mm (usually 0)
    beam_y : float
        y-coordinate of x-ray beam in mm (usually 0)
    cam_roll : float
        rotation of camera about z axis in radians

    Returns
    -------
    xj : float
        Jet position at the beam height in millimeters
    '''
    yb_roi = (1.0 / pxsize) * ((cam_y - beam_y) * np.cos(cam_roll) +
                               (cam_x - beam_x) * np.sin(cam_roll)) - roi_y
    # print('yb_roi: {}'.format(yb_roi))
    xj_roi = (rho - yb_roi * np.sin(theta)) / np.cos(theta)
    # print('xj_roi: {}'.format(xj_roi))
    x0_roi = (1.0 / pxsize) * (cam_x * np.cos(cam_roll) -
                               cam_y * np.sin(cam_roll)) - roi_x
    xj = pxsize * (x0_roi - xj_roi)
    return xj


def get_jet_pitch(theta, cam_pitch):
    '''Calculates jet angle in the main coordinate system (in radians, from -pi/2 to pi/2)

    Parameters
    ----------
    theta : float
        Angle of the shortest vector from (0,0) to the line in radians
    cam_pitch : float
        rotation of camera about x axis in radians

    Returns
    -------
    jet_pitch : float
        Jet angle in radians
    '''
    jet_pitch = (theta - np.pi / 2 - cam_pitch) % np.pi - np.pi / 2
    return jet_pitch


def get_jet_roll(theta, cam_roll):
    '''Calculates jet angle in the main coordinate system (in radians, from -pi/2 to pi/2)

    Parameters
    ----------
    theta : float
        Angle of the shortest vector from (0,0) to the line in radians
    cam_roll : float
        rotation of camera about z axis in radians

    Returns
    -------
    jet_roll : float
        Jet angle in radians
    '''
    jet_roll = (theta - np.pi / 2 - cam_roll) % np.pi - np.pi / 2
    return jet_roll


def get_jet_width(im, rho, theta):
    '''Calculates the jet width

    Parameters
    ----------
    img : ndarray
        ROI of the on-axis image
    rho : float
        Distance from (0,0) to the line in pixels
    theta : float
        Angle of the shortest vector from (0,0) to the line in radians

    Returns
    -------
    w : float
        Jet width in pixels
    '''
    rows, column_indices = np.ogrid[:im.shape[0], :im.shape[1]]
    r = np.asarray([int((rho + y * np.sin(theta)) / np.cos(theta))
                    for y in range(im.shape[0])])
    r = r % im.shape[1]
    column_indices = column_indices - r[:, np.newaxis]

    s = im[rows, column_indices].sum(axis=0)

    w = peak_widths(s, [s.argmax()])[0]
    return w


def get_offaxis_coords(cam_beam_y, cam_beam_z, *, cam_pitch, pxsize):
    '''Finds cam_y and cam_z using the pixel coordinates of the origin

    Parameters
    ----------
    cam_beam_y : float
        y coordinate for the beam (= main coordinate origin) on the camera in pixels
    cam_beam_z : float
        z coordinate for the beam (= main coordinate origin) on the camera in pixels
    cam_pitch : float
        rotation of camera about x axis in radians
    pxsize : float
        size of pixel in mm

    Returns
    -------
    cam_y : float
        Y-coordinate of the origin of the camera in the main coordinate system in millimeters
    cam_z : float
        Z-coordinate of the origin of the camera in the main coordinate system in millimeters

    '''
    cam_y = pxsize * (cam_beam_z * np.sin(cam_pitch) +
                      cam_beam_y * np.cos(cam_pitch))
    cam_z = pxsize * (cam_beam_z * np.cos(cam_pitch) -
                      cam_beam_y * np.sin(cam_pitch))

    return cam_y, cam_z


def get_cam_coords(cam_beam_x, cam_beam_y, *, cam_roll, pxsize):
    '''Finds cam_x and cam_y using the pixel coordinates of the origin

    Parameters
    ----------
    cam_beam_x : float
        x coordinate for the beam (= main coordinate origin) on the camera in pixels
    cam_beam_y : float
        y coordinate for the beam (= main coordinate origin) on the camera in pixels
    cam_roll : float
        rotation of camera about z axis in radians
    pxsize : float
        size of pixel in mm

    Returns
    -------
    cam_x : float
        X-coordinate of the origin of the camera in the main coordinate system in millimeters
    cam_y : float
        Y-coordinate of the origin of the camera in the main coordinate system in millimeters

    '''
    cam_x = pxsize * (cam_beam_y * np.sin(cam_roll) +
                      cam_beam_x * np.cos(cam_roll))
    cam_y = pxsize * (cam_beam_y * np.cos(cam_roll) -
                      cam_beam_x * np.sin(cam_roll))

    return cam_x, cam_y


def get_cam_pitch(imgs):
    '''Finds the camera angle

    Parameters
    ----------
    imgs : list(ndarray)
        List of images where nozzle has been moved in x-direction

    Returns
    -------
    cam_pitch : float
        Offaxis camera pitch angle in radians
    '''
    ytot = 0
    ztot = 0
    for i in range(len(imgs) - 1):
        im1 = imgs[i]
        im2 = imgs[i + 1]
        shift, error, diffphase = register_translation(im1, im2, 100)
        dy = shift[0]
        dz = shift[1]
        if dy < 0:
            dy *= -1
            dz *= -1
        ytot += dy
        ztot += dz

    cam_pitch = np.arctan(ytot / ztot)
    return cam_pitch


def get_cam_roll(imgs):
    '''Finds the camera angle

    Parameters
    ----------
    imgs : list(ndarray)
        List of images where nozzle has been moved in x-direction

    Returns
    -------
    cam_roll : float
        Camera angle in radians
    '''
    ytot = 0
    xtot = 0
    for i in range(len(imgs) - 1):
        im1 = imgs[i]
        im2 = imgs[i + 1]
        shift, error, diffphase = register_translation(im1, im2, 100)
        dy = shift[0]
        dx = shift[1]
        if dy < 0:
            dy *= -1
            dx *= -1
        ytot += dy
        xtot += dx

    cam_roll = -np.arctan(ytot / xtot)
    return cam_roll


def get_cam_pitch_pxsize(imgs, positions):
    '''Finds offaxis camera pitch and pixel size

    Parameters
    ----------
    imgs : list(ndarray)
        List of images where nozzle has been moved in x-direction
    positions : list(float)
        List of motor positions in millimeters

    Returns
    -------
    cam_pitch : float
        Camera angle in radians
    pxsize : float
        Pixel size in millimeters
    '''
    ytot = 0
    ztot = 0
    changetot = 0
    for i in range(len(positions) - 1):
        im1 = imgs[i]
        im2 = imgs[i + 1]
        shift, error, diffphase = register_translation(im1, im2, 100)
        dy = shift[0]
        dz = shift[1]
        if dy < 0:
            dy *= -1
            dz *= -1
        ytot += dy
        ztot += dz

        changetot += abs(positions[i + 1] - positions[i])

    cam_pitch = np.arctan(ytot / ztot)
    pxsize = changetot / np.sqrt(ytot**2 + ztot**2)
    return cam_pitch, pxsize


def get_cam_roll_pxsize(imgs, positions):
    '''Finds camera angle and pixel size

    Parameters
    ----------
    imgs : list(ndarray)
        List of images where nozzle has been moved in x-direction
    positions : list(float)
        List of motor positions in millimeters

    Returns
    -------
    cam_roll : float
        Camera angle in radians
    pxsize : float
        Pixel size in millimeters
    '''
    ytot = 0
    xtot = 0
    changetot = 0
    for i in range(len(positions) - 1):
        im1 = imgs[i]
        im2 = imgs[i + 1]
        shift, error, diffphase = register_translation(im1, im2, 100)
        dy = shift[0]
        dx = shift[1]
        if dy < 0:
            dy *= -1
            dx *= -1
        ytot += dy
        xtot += dx

        changetot += abs(positions[i + 1] - positions[i])

    cam_roll = -np.arctan(ytot / xtot)
    pxsize = changetot / np.sqrt(ytot**2 + xtot**2)
    return cam_roll, pxsize


def get_nozzle_shift(im1, im2, *, cam_roll, pxsize):
    '''Finds the distance the nozzle has shifted between two images

    Parameters
    ----------
    im1 : ndarray
        On-axis camera image 1
    im2 : ndarray
        On-axis camera image 2
    cam_roll : float
        rotation of camera about z axis in radians
    pxsize : float
        size of pixel in mm

    Returns
    -------
    dy : float
        Distance in y
    dx : float
        Distance in x
    '''

    shift, error, diffphase = register_translation(im1, im2, 100)
    sy = shift[0]
    sx = shift[1]

    dx = (sx * np.cos(cam_roll) - sy * np.sin(cam_roll)) * pxsize
    dy = (sy * np.cos(cam_roll) + sx * np.sin(cam_roll)) * pxsize
    return dy, dx
