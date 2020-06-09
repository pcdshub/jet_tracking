import numpy as np
from matplotlib import pyplot as plt
from skimage.feature import canny, peak_local_max
from skimage.transform import hough_line, hough_line_peaks, rotate


def detect_edge(img):
    """
    Use detect jet edges with Canny edge detection.

    Canny parameters:
    sigma: standard deviation of Gaussian filter
    use_quantiles=True: treat low_threshold & high_threshold as quantiles
    rather than absolute values
    low_threshold & high_threshold: thresholds for edge detection
    """

    binary = canny(img, sigma=2, use_quantiles=True, low_threshold=0.9,
                   high_threshold=0.99)
    fix, axes = plt.subplots(1, 2)
    axes[0].imshow(img)
    axes[1].imshow(binary)
    plt.show()
    return binary


def hough_transform(binary):
    try:
        h, angles, d = hough_line(binary)
        res = hough_line_peaks(h, angles, d, min_distance=1,
                               threshold=int(binary.shape[0] / 3))
    except Exception:
        raise ValueError('ERROR hough: not a jet')
    fig, axes = plt.subplots(1, 2)
    axes[0].imshow(binary)
    axes[1].imshow(binary)
    valid = []
    for _, theta, dist in zip(*res):
        jetValid = True
        if (theta < np.radians(-45)) or (theta > np.radians(45)):
            print('ERROR angle: not a jet')
            jetValid = False
        yint = dist / np.sin(theta)
        xint = np.tan(theta) * yint
        if (dist < 0) or (xint > binary.shape[1]):
            print('ERROR xint: not a jet')
            jetValid = False
        if (jetValid):
            y0 = (dist - 0 * np.cos(theta)) / np.sin(theta)
            y1 = (dist - binary.shape[1] * np.cos(theta)) / np.sin(theta)
            axes[1].plot((0, binary.shape[1]), (y0, y1), 'r')
            valid.append([theta, dist])
    axes[1].set_xlim((0, binary.shape[1]))
    axes[1].set_ylim((binary.shape[0], 0))
    return valid


# def jet_detect(img, calibrate_mean, calibrate_std, pxsize):
def jet_detect(img, calibrate_mean, calibrate_std):
    """
    Detect the jet.

    Canny Parameters:
    img: ROI image to look for jet in
    calibrate_mean: mean from calibration ROI image with jet (see calibrate())
    calibrate_std: standard deviation from calibration ROI image
         with jet (see calibrate())
    pxsize: pixel size in mm (see calibrate())
    """

    # TODO: add std comparison?
    # compare mean & std of current image to mean & std of calibrate image
    mean = img.mean()
    if (mean < calibrate_mean * 0.8) or (mean > calibrate_mean * 1.2):
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
            #     jetValid = false
            #     print('ERROR width: not a jet')
            if (jetValid):
                valid.append([theta, dist])
    except Exception:
        raise ValueError('ERROR hough: no jet')

    # use local maxes to determine exact jet position
    # line-fitting cannot be performed on a vertical line (which is highly
    # likely due to the nature of the jet) so rotate the image first
    imgr = rotate(img, 90, resize=True, preserve_range=True)

    jet_xcoords = []
    jet_ycoords = []

    for x in range(10):
        # try to find local maxes (corresponds to jet) in 10 rows along height
        # of image)
        col = int(imgr.shape[1] / 10 * x)
        ymax = peak_local_max(imgr[:, col], threshold_rel=0.9,
                              num_peaks=1)[0][0]

        # check if point found for max is close to jet lines found with Hough
        # transform
        miny = imgr.shape[0]
        maxy = 0
        for theta, dist in valid:
            xint = dist / np.sin(theta)
            y = imgr.shape[0] - ((xint - col) * np.tan(theta))

            if (y < miny):
                miny = y
            if (y > maxy):
                maxy = y

        # if x found using local max is close to lines found with Hough
        # transform, keep it
        if (ymax >= (miny - 5)) and (ymax <= (maxy + 5)):
            jet_xcoords.append(col)
            jet_ycoords.append(ymax)

    try:
        # fit a line to the points found using local max
        m, b = np.polyfit(jet_xcoords, jet_ycoords, 1)
        theta = np.arctan(-m)
        rho = np.cos(theta) * (imgr.shape[0] - b)
    except Exception:
        raise ValueError('ERROR polyfit: no jet')
    return rho, theta


def find_jet(camera, params):
    # get image from JetCamera
    # img = get_burst_avg(20, camera.ROI_image)
    img = camera.ROI_image.image2

    # get mean and std for calibration
    mean = img.mean()
    std = img.std()
    params.mean.put(mean)
    params.std.put(std)

    try:
        # m, b = jet_detect(img, params.mean.get(), params.std.get(),
        # params.pxsize.get())
        rho, theta = jet_detect(img, params.mean.get(), params.std.get())
        print(rho, theta)

        fix, axes = plt.subplots(1, 2)
        axes[0].imshow(img)
        y0 = rho / np.sin(theta)
        y1 = (rho - img.shape[1] * np.cos(theta)) / np.sin(theta)
        axes[1].imshow(img)
        axes[1].plot((0, img.shape[1]), (y0, y1), 'r')
        axes[1].set_xlim((0, img.shape[1]))
        axes[1].set_ylim((img.shape[0], 0))
        plt.show()
    except Exception:
        raise ValueError('ERROR: unable to find jet')

# 1. calibrate w/ expected jet in ROI using calibrate(injector, camera, params)
#    in jet_control.py
# 2. calibrate collects: expected mean, std, c, cam_pitch, pxsize, beam x & y,
#    camera x & y, cam_roll, jet_roll
# 2b. first find mean & std using separate function, then pass to jet_detect()
#     - save mean & std (w/ some +/- ?) to params
# 2c. jet_detect returns rho, theta, c - save c (w/ some +/- ?) to params
# 3. use jet_detect(img, mean, std, x) in cam_utils.py for constant tracking of
#    jet position (pass image from JetCamera; mean, std, x from params)
# 3b. call jet_detect() from jet_calculate(camera, params) in jet_control.py

# *** check which other functions call jet_detect()
