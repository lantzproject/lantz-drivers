# -*- coding: utf-8 -*-
"""
    lantz.drivers.stanford.sr400
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of SR400 GATED PHOTON COUNTER

    Author: Alexandre Bourassa
    Date: 10/23/2016
"""

from lantz import Action, Feat, DictFeat, ureg
from lantz.messagebased import MessageBasedDriver

import time as _t

class SR400(MessageBasedDriver):
    DEFAULTS = {
        'COMMON': {
            'write_termination': '\r\n',
            'read_termination': '\r\n',
        }
    }

    COUNTERS = {'A':0, 'B':1, 'T':2}

    def write(self, *args, **kwargs):
        super().write(*args, **kwargs)
        _t.sleep(0.05)

    @Action()
    def reset(self):
        self.write('CL')
        _t.sleep(0.1)

    @Feat(values={'A,B FOR T PRESET': 0, 'A-B FOR T PRESET': 1, 'A+B FOR T PRESET': 2, 'A FOR B PRESET': 3})
    def counting_mode(self):
        return int(self.query('CM'))

    @counting_mode.setter
    def counting_mode(self, value):
        self.write('CM {}'.format(value))

    @DictFeat(keys=['A','B','T'], values={'10 MHz': 0, 'INPUT 1': 1, 'INPUT 2': 2, 'TRIG': 3})
    def counter_input(self, key):
        return int(self.query('CI {}'.format(self.COUNTERS[key])))

    @counter_input.setter
    def counter_input(self, key, value):
        if key is 'A' and not value in [0,1]: raise Exception("Counter A input can only be '10 MHz' or 'INPUT 1'")
        if key is 'B' and not value in [1,2]: raise Exception("Counter B input can only be 'INPUT 1' or 'INPUT 2'")
        if key is 'T' and not value in [0,2,3]: raise Exception("Counter T input can only be '10 MHz', 'INPUT 2' or 'TRIG'")
        self.write('CI {}, {}'.format(self.COUNTERS[key], value))

    @Feat(units='seconds')
    def dwell_time(self):
        return float(self.query('DT'))

    @dwell_time.setter
    def dwell_time(self, value):
        if not int(value) is 0:
            if not 2E-3<=value<=6E1:
                raise Exception("Dwell time must be either 0 (External) or between 2e-3 and 6e1 (only first significant digit matters)")
        self.write('DT {}'.format(value))

    @DictFeat(keys=['B','T'], limits=(1,9E11))
    def counter_preset(self, key):
        return int(float(self.query('CP {}'.format(self.COUNTERS[key]))))

    @counter_preset.setter
    def counter_preset(self, key, value):
        self.write('CP {}, {}'.format(self.COUNTERS[key], value))

    @Feat(limits=(1,2000))
    def period_per_scan(self):
        return int(self.query('NP'))

    @period_per_scan.setter
    def period_per_scan(self, value):
        self.write('NP {}'.format(value))

    @DictFeat(keys=['A', 'B'], values={'CW': 0, 'FIXED': 1, 'SCAN': 2})
    def gate_mode(self, key):
        return int(self.query('GM {}'.format(self.COUNTERS[key])))

    @gate_mode.setter
    def gate_mode(self, key, value):
        self.write('GM {}, {}'.format(self.COUNTERS[key], value))

    @DictFeat(keys=['A', 'B'], units='seconds', limits=(0,999.2E-3, 1e-9))
    def gate_delay(self, key):
        return float(self.query('GD {}'.format(self.COUNTERS[key])))

    @gate_delay.setter
    def gate_delay(self, key, value):
        self.write('GD {}, {}'.format(self.COUNTERS[key], value))

    @DictFeat(keys=['A', 'B'], units='seconds', limits=(0,99.92E-3, 1e-9))
    def scan_gate_delay(self, key):
        return float(self.query('GY {}'.format(self.COUNTERS[key])))

    @scan_gate_delay.setter
    def scan_gate_delay(self, key, value):
        self.write('GY {}, {}'.format(self.COUNTERS[key], value))

    @DictFeat(keys=['A', 'B'], units='seconds', limits=(0.005E-6, 99.92E-3, 1e-9))
    def gate_width(self, key):
        return float(self.query('GW {}'.format(self.COUNTERS[key])))

    @gate_width.setter
    def gate_width(self, key, value):
        self.write('GW {}, {}'.format(self.COUNTERS[key], value))

    @DictFeat(keys=['A', 'B', 'T'], values={'RISE': 0, 'FALL': 1})
    def disc_slope(self, key):
        return int(self.query('DS {}'.format(self.COUNTERS[key])))

    @disc_slope.setter
    def disc_slope(self, key, value):
        self.write('DS {}, {}'.format(self.COUNTERS[key], value))

    @DictFeat(keys=['A', 'B', 'T'], limits=(-0.3,0.3,0.0002), units='V')
    def disc_level(self, key):
        return float(self.query('DL {}'.format(self.COUNTERS[key])))

    @disc_level.setter
    def disc_level(self, key, value):
        self.write('DL {}, {}'.format(self.COUNTERS[key], value))
