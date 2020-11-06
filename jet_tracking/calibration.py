import time


class Calibration(object):

    def __init__(self, signals, parent=None):

        self.parent = parent
        self.signals = signals
        self.ave_low_i0 = 0
        self.mean_diff = 0
        self.sigma_diff = 0
        self.sigma_i0 = 0
        self.mean_ratio = 0
        # values = [[], [], []]

        self.signals.calibration.connect(self.monitor)

    def get_i0(self):

        return(self.ave_low_i0)

    def get_diff(self):

        return(self.mean_diff)

    def get_ratio(self):

        return(self.mean_ratio)

    def get_sigma(self):

        return(self.sigma_i0)

    def monitor(self):

        # want to make Counter more flexible

        # c = Counter(self.signals, 3600)

        self.t = time.time()

        # c.start()
