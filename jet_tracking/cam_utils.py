import numpy as np
from scipy.signal import peak_widths
from skimage.feature import canny, peak_local_max, register_translation
from skimage.transform import hough_line, hough_line_peaks, rotate


def image_stats(img):
    """
    Find the mean and standard deviation of an image.

    Parameters
    ----------
    img : ndarray
        Image that you would like the mean and std of.

    Returns
    -------
    mean : float
        Mean of given image.
    std : float
        Standard deviation of image.
    """

    return img.mean(), img.std()


def jet_detect(img, calibratemean, calibratestd):
    """
    Find the jet using Canny edge detection and Hough line transform.

    This method first compares the mean of the ROI image to the mean of the
    calibrated ROI. Then Canny edge detection is used to detect the edges of
    the jet in the ROI and convert the original image to a binary image. Hough
    line transform is performed on the binary image to determine the
    approximate position of the jet. Peak-finding is performed on several
    horizontal slices of the image, and a line is fitted to these points to
    determine the actual position of the jet. If a peak is found that is not in
    the approximate position of the jet determined by the Hough line transform,
    that point is not considered in the line fitting.

    Parameters
    ----------
    img : ndarray
        ROI of the on-axis image.

    mean : float
        Mean of calibration ROI image with jet (see `~jet_control.calibrate`).

    calibratestd : float
        Standard deviation calibration ROI image with jet (see
        `~jet_control.calibrate`).

    Returns
    -------
    rho : float
        Distance from (0,0) to the line in pixels.

    theta : float
        Angle of the shortest vector from (0,0) to the line in radians.
    """

    # compare mean & std of current image to mean & std of calibrate image
    mean, std = image_stats(img)
    if (mean < calibratemean * 0.8) or (mean > calibratemean * 1.2):
        raise ValueError('ERROR mean: no jet')

    try:
        # use canny edge detection to convert image to binary
        binary = canny(img, sigma=2, use_quantiles=True, low_threshold=0.9,
                       high_threshold=0.99)

        # perform Hough Line Transform on binary image
        h, angles, d = hough_line(binary)
        res = hough_line_peaks(h, angles, d, min_distance=1,
                               threshold=int(img.shape[0] / 3))

        # keep only valid lines
        valid = []
        for _, theta, dist in zip(*res):
            jetValid = True
            # jet must be within 45 degrees of vertical
            if (theta < np.radians(-45)) or (theta > np.radians(45)):
                jetValid = False
            # jet must start from top edge of imagei
            yint = dist / np.sin(theta)
            xint = np.tan(theta) * yint
            if (dist < 0) or (xint > binary.shape[1]):
                jetValid = False
            # jet must be within [x] pixels width
            # if (cam_utils.get_jet_width(img, rho, theta) * pxsize > 0.01):
                #  jetValid = false
                #  print('ERROR width: not a jet')
            if (jetValid):
                valid.append([theta, dist])
    except Exception:
        raise ValueError('ERROR hough: no jet')

    # use local maxes to determine exact jet position
    # line-fitting cannot be performed on vertical line (which is highly likely due to
    # nature of jet) so rotate image first
    imgr = rotate(img, 90, resize=True, preserve_range=True)

    jet_xcoords = []
    jet_ycoords = []

    for x in range(10):
        # try to find local maxes (corresponds to jet) in 10 rows along height of image)
        col = int(imgr.shape[1] / 10 * x)
        ymax = peak_local_max(imgr[:, col], threshold_rel=0.9, num_peaks=1)[0][0]

        # check if point found for max is close to jet lines found with Hough transform
        miny = imgr.shape[0]
        maxy = 0
        for theta, dist in valid:
            xint = dist / np.sin(theta)
            y = imgr.shape[0] - ((xint - col) * np.tan(theta))

            if (y < miny):
                miny = y
            if (y > maxy):
                maxy = y

        # if x found using local max is close to lines found with Hough transform, keep it
        if (ymax >= (miny - 5)) and (ymax <= (maxy + 5)):
            jet_xcoords.append(col)
            jet_ycoords.append(ymax)

    try:
        # fit a line to the points found using local max
        m, b = np.polyfit(jet_xcoords, jet_ycoords, 1)
        theta = -np.arctan(m)
        rho = np.cos(theta) * (imgr.shape[0] - b)
    except Exception:
        raise ValueError('ERROR polyfit: no jet')
    return rho, theta


def get_jet_z(rho, theta, roi_y, roi_z, *, pxsize, cam_y, cam_z, beam_y,
              beam_z, cam_pitch):
    """
    Calculates the jet position at beam height in offaxis camera coordinates.

    This differs from the main coordinate system in that z and pitch replace x
    and roll according to camera orientation.

    Parameters
    ----------
    rho : float
        Distance from (0,0) to the line in pixels.

    theta : float
        Angle of the shortest vector from (0,0) to the line in radians.

    y_roi : int
        Y-coordinate of the origin of the ROI on the camera image in pixels.

    z_roi : int
        Z-coordinate of the origin of the ROI on the camera image in pixels.

    pxsize : float
        Size of pixel in mm.

    cam_y : float
        Y-coordinate of camera position in mm.

    cam_z : float
        Z-coordinate of camera position in mm.

    beam_y : float
        Y-coordinate of x-ray beam in mm (usually 0).

    beam_z : float
        Z-coordinate of x-ray beam in mm (usually 0).

    cam_pitch : float
        Rotation of camera about x axis in radians.

    Returns
    -------
    zj : float
        Jet position at the beam height in millimeters.
    """

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
    """
    Calculates the jet position at beam height in the main coordinate system.

    Parameters
    ----------
    rho : float
        Distance from (0,0) to the line in pixels.

    theta : float
        Angle of the shortest vector from (0,0) to the line in radians.

    x_roi : int
        X-coordinate of the origin of the ROI on the camera image in pixels.

    y_roi : int
        Y-coordinate of the origin of the ROI on the camera image in pixels.

    pxsize : float
        Size of pixel in mm.

    cam_x : float
        X-coordinate of camera position in mm.

    cam_y : float
        Y-coordinate of camera position in mm.

    beam_x : float
        X-coordinate of x-ray beam in mm (usually 0).

    beam_y : float
        Y-coordinate of x-ray beam in mm (usually 0).

    cam_roll : float
        Rotation of camera about z axis in radians.

    Returns
    -------
    xj : float
        Jet position at the beam height in millimeters.
    """

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
    """
    Calculate jet angle in the main coordinate system.

    Result is in radians, from -pi/2 to pi/2.

    Parameters
    ----------
    theta : float
        Angle of the shortest vector from (0,0) to the line in radians.

    cam_pitch : float
        Rotation of camera about x axis in radians.

    Returns
    -------
    jet_pitch : float
        Jet angle in radians.
    """

    return (theta - np.pi / 2 - cam_pitch) % np.pi - np.pi / 2


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
    return (theta - np.pi / 2 - cam_roll) % np.pi - np.pi / 2


def get_jet_width(im, rho, theta):
    """
    Calculate the jet width.

    Parameters
    ----------
    img : ndarray
        ROI of the on-axis image.

    rho : float
        Distance from (0,0) to the line in pixels.

    theta : float
        Angle of the shortest vector from (0,0) to the line in radians.

    Returns
    -------
    w : float
        Jet width in pixels.
    """

    rows, column_indices = np.ogrid[:im.shape[0], :im.shape[1]]
    r = np.asarray([int((rho + y * np.sin(theta)) / np.cos(theta))
                    for y in range(im.shape[0])])
    r = r % im.shape[1]
    column_indices = column_indices - r[:, np.newaxis]

    s = im[rows, column_indices].sum(axis=0)

    return peak_widths(s, [s.argmax()])[0]


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
    """
    Find cam_x and cam_y using the pixel coordinates of the origin.

    Parameters
    ----------
    cam_beam_x : float
        X coordinate for the beam (= main coordinate origin) on the camera in
        pixels.

    cam_beam_y : float
        Y coordinate for the beam (= main coordinate origin) on the camera in
        pixels.

    cam_roll : float
        Rotation of camera about z axis in radians.

    pxsize : float
        Size of pixel in mm.

    Returns
    -------
    cam_x : float
        X-coordinate of the origin of the camera in the main coordinate system
        in millimeters.

    cam_y : float
        Y-coordinate of the origin of the camera in the main coordinate system
        in millimeters.
    """

    cam_x = pxsize * (cam_beam_y * np.sin(cam_roll) +
                      cam_beam_x * np.cos(cam_roll))
    cam_y = pxsize * (cam_beam_y * np.cos(cam_roll) -
                      cam_beam_x * np.sin(cam_roll))
    return cam_x, cam_y


def get_cam_pitch(imgs):
    """
    Find the camera angle.

    Parameters
    ----------
    imgs : list of ndarray
        List of images where nozzle has been moved in x-direction.

    Returns
    -------
    cam_pitch : float
        Offaxis camera pitch angle in radians.
    """

    ytot = 0
    ztot = 0
    for i in range(len(imgs) - 1):
        im1, im2 = imgs[i], imgs[i + 1]
        (dy, dz), error, diffphase = register_translation(im1, im2, 100)
        if dy < 0:
            dy *= -1
            dz *= -1
        ytot += dy
        ztot += dz
    return np.arctan(ytot / ztot)


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
        im1, im2 = imgs[i], imgs[i + 1]
        (dy, dx), error, diffphase = register_translation(im1, im2, 100)
        if dy < 0:
            dy *= -1
            dx *= -1
        ytot += dy
        xtot += dx
    return -np.arctan(ytot / xtot)


def get_cam_pitch_pxsize(imgs, positions):
    """
    Find offaxis camera pitch and pixel size.

    Parameters
    ----------
    imgs : list of ndarray
        List of images where nozzle has been moved in x-direction.

    positions : list of float
        List of motor positions in millimeters.

    Returns
    -------
    cam_pitch : float
        Camera angle in radians.

    pxsize : float
        Pixel size in millimeters.
    """

    ytot = 0
    ztot = 0
    changetot = 0
    for i in range(len(positions) - 1):
        im1, im2 = imgs[i], imgs[i + 1]
        (dy, dz), error, diffphase = register_translation(im1, im2, 100)
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
        im1, im2 = imgs[i], imgs[i + 1]
        (dy, dx), error, diffphase = register_translation(im1, im2, 100)
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
    """
    Find the distance the nozzle has shifted between two images.

    Parameters
    ----------
    im1 : ndarray
        On-axis camera image 1.

    im2 : ndarray
        On-axis camera image 2.

    cam_roll : float
        Rotation of camera about z axis in radians.

    pxsize : float
        Size of pixel in mm.

    Returns
    -------
    dy : float
        Distance in y.

    dx : float
        Distance in x.
    """

    (sy, sx), error, diffphase = register_translation(im1, im2, 100)
    dx = (sx * np.cos(cam_roll) - sy * np.sin(cam_roll)) * pxsize
    dy = (sy * np.cos(cam_roll) + sx * np.sin(cam_roll)) * pxsize
    return dy, dx


def get_burst_avg(n, image_plugin):
    """
    Get the average of n consecutive images from a camera

    Parameters
    ----------
    n : int
        Number of consecutive images to be averaged.

    image_plugin : ImagePlugin
        Camera ImagePlugin from which the images will be taken.

    Returns
    -------
    burst_avg : ndarray
        Average image.
    """

    imageX, imageY = image_plugin.image.shape
    burst_imgs = np.empty((n, imageX, imageY))
    for x in range(n):
        burst_imgs[x] = image_plugin.image
    burst_avg = burst_imgs.mean(axis=0)

    return burst_avg
