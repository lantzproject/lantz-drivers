from ctypes import c_double

import numpy as np
from lantz.core import Feat
from lantz.core.foreign import LibraryDriver

from lantz.drivers import Wavemeter


class WS6_200(LibraryDriver, Wavemeter):
    LIBRARY_NAME = r'C:\Windows\System32\wlmData.dll'
    LIBRARY_PREFIX = ''

    def __init__(self):
        super().__init__()

        # Function definitions
        self.lib.GetFrequency.argtypes = [c_double]
        self.lib.GetFrequency.restype = c_double

        self._averaging = True
        self._num_avg = 10
        return

    def initialize(self, devNo=None):
        pass

    def finalize(self):
        pass

    @Feat()
    def averaging(self):
        return self._averaging

    @averaging.setter
    def averaging(self, value):
        self._averaging = value

    @Feat()
    def num_avg(self):
        return self._num_avg

    @num_avg.setter
    def num_avg(self, value):
        self._num_avg = value

    @Feat(units='THz')
    def frequency(self):
        if self._averaging:
            return np.mean([self.lib.GetFrequency(0) for _ in range(self._num_avg)])
        else:
            return self.lib.GetFrequency(0)
