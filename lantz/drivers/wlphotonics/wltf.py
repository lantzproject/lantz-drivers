# -*- coding: utf-8 -*-
"""
    lantz.drivers.wlphotonics.wltf
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Lantz interface to WL Photonics tunable filter

    Authors: Alexandre Bourassa
    Date: 08/1/2018

"""

from lantz import Action, Feat, DictFeat, Q_
from lantz.errors import InstrumentError, LantzTimeoutError
from lantz.messagebased import MessageBasedDriver

from pyvisa.constants import Parity, StopBits

import time

class Wltf(MessageBasedDriver):

    DEFAULTS = {
        'ASRL': {
            'write_termination': '\r\n',
            'read_termination': '\r\n',
            'baud_rate': 115200,
            'timeout': 2000,
            'parity':Parity.none,
            'stop_bits':StopBits.one,
        }
    }   

    def query(self, cmd, delay=0.01):
        self.write(cmd)
        time.sleep(delay)
        done = False
        ans = ''
        while not done:
            line = self.read()
            if 'ER: ' in line:
                raise Exception(line)
            elif 'OK' in line:
                done = True
            else:
                ans += line + '\n'
        return ans[0:-1]

    def cmd_list(self):
        print(self.query('CMD?'))

    @Feat()
    def idn(self):
        return self.query('DEV?').split('\n')[0]

    @Action()
    def run_frequency_calibration(self):
        return self.query('FC')
    
    @Feat()
    def step(self):
        s = self.query('S?').split(',')[0]
        return int(s.split(':')[1].strip())

    @step.setter
    def step(self, val):
        val = int(val)
        if val < 0:
            return self.query('SB: {}'.format(abs(val)))
        elif val > 0:
            return self.query('SF: {}'.format(val))
        else:
            return

    @Feat(units='nm', limits=(1050., 1170., 0.01))
    def wavelength(self):
        return Q_(self.query('WL?').split(':')[1].strip())

    @wavelength.setter
    def wavelength(self, val):
        return self.query('WL{}'.format(val))


        