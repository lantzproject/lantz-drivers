# -*- coding: utf-8 -*-
"""
    dummydrivers
    ~~~~~~~~~~~~

    Just some fake drivers to show how the backend, frontend works.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import numpy as np
from lantz.core import Action, Driver, Feat, ureg


class DummyFunGen(Driver):
    """A Function Generator Driver.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._amplitude = 0.0
        self._frequency = 1e3

    @Feat(units='Hz')
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, value):
        self._frequency = value

    @Feat(units='V')
    def amplitude(self):
        return self._amplitude

    @amplitude.setter
    def amplitude(self, value):
        self._amplitude = value


class DummyOsci(Driver):
    """An Oscilloscope Driver.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @Action()
    def measure(self):
        return np.random.random((100,))


class DummyShutter(Driver):
    """A Shutter Driver.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._opened = False

    @Feat(values={True, False})
    def opened(self):
        return self._opened

    @opened.setter
    def opened(self, value):
        self._opened = value
