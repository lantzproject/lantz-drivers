from lantz import Feat, DictFeat, Action
from lantz.driver import Driver
from collections import OrderedDict
import time
import ripy
import numpy as np

class RI(Driver):

    gain_values = OrderedDict([
        ('High', True),
        ('Low', False),
    ])

    antialias_values = OrderedDict([
        ('On', True),
        ('Off', False),
    ])

    def __init__(self):
        super(RI, self).__init__()
        self._ripy = ripy.Device()
        self._ripy.open()

    @Feat(units = "Hz")
    def sample_rate(self):
        return self._ripy.samplerate

    @Feat()
    def usb_speed(self):
        return self._ripy.usb_speed

    @Feat(values = gain_values)
    def gain(self):
        """
        Get the current gain setting
        """
        return self._ripy.highgain

    @gain.setter
    def gain(self, gain_value):
        """
        Set the current gain setting \n
        It can be \"High\" or \"Low\"
        """
        self._ripy.set_highgain(gain_value)

    @Feat(values = antialias_values)
    def antialias(self):
        """
        Get the current antialias setting
        """
        return self._ripy.antialias


    @antialias.setter
    def antialias(self, antialias_value):
        """
        Set the current gain setting \n
        It can be \"On\" or \"Off\"
        """
        self._ripy.set_antialias(antialias_value)

    @Action()
    def get_raw_data(self, nsamples):
        """
        Get n many samples
        """
        return self._ripy.get_raw_data(nsamples)


    @Action()
    def get_triggered_data(self, nsamples, ntimes=1, key="T"):
        """
        Get n many samples ntimes many trigger detects a rising edge
        """
        total = nsamples*ntimes
        raw_return = self._ripy.get_raw_data(total, trig_port = key, trig_mode = "rising", samples_per_trigger = nsamples)
        if ntimes == 1:
            return raw_return
        else:
            return np.hsplit(raw_return,ntimes)

