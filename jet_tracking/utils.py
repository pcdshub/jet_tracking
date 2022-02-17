import numpy as np
import psana


def get_r_masks(shape, bins=100):
    """Function to generate radial masks for pixels to include in azav"""
    center = (shape[1] / 2, shape[0] / 2)
    x, y = np.meshgrid(np.arange(shape[1]) - center[0],
                       np.arange(shape[0]) - center[1])
    R = np.sqrt(x**2 + y**2)
    max_R = np.max(R)
    min_R = np.min(R)
    bin_size = (max_R - min_R) / bins
    radii = np.arange(1, max_R, bin_size)
    masks = []
    for i in radii:
        mask = (np.greater(R, i - bin_size) & np.less(R, i + bin_size))
        masks.append(mask)

    return masks


def get_evr_w_codes(det_names):
    """Get the evr with the event codes, yes this changes..."""
    evr_keys = [det[1] for det in det_names if 'evr' in det[1]]
    evr_dict = {k: psana.Detector(k)._fetch_configs()[0].neventcodes()
                for k in evr_keys}
    return psana.Detector(max(evr_dict, key=evr_dict.get))
