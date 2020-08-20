# -*- coding: utf-8 -*-
"""
    lantz.drivers.swabian.PSWidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Implementation of Swabian GUI over a local socket
    Author: Berk Diler
    Date: 4/4/2020
"""

from collections import OrderedDict
from lantz import Action, Feat, DictFeat, Q_
from lantz.messagebased import MessageBasedDriver
import numpy as np


class Swabian(MessageBasedDriver):
    DEFAULTS = {
        'COMMON': {
            'write_termination': '\n',
            'read_termination': '\n',
            "timeout": 5
        }
    }

    @Feat(units="ns")
    def duty_cycle(self):
        return int(float(self.query("GetPulseTime")))

    @Feat(units="ns")
    def ctr1(self):
        return int(float(self.query('GetCtr1')))

    @Feat(units="ns")
    def ctr2(self):
        return int(float(self.query('GetCtr2')))

    @DictFeat()
    def sweep(self, key):
        return "Okkk!"

    @sweep.setter
    def sweep(self, key, arrargs):
        self.write('SetSweep {} {start} {stop} {steps} {func} {endpoint}'.format(key, **arrargs))

    @DictFeat()
    def sweep_index(self, key):
        return int(float(self.query('GetIterSweep {}'.format(key))))

    @sweep_index.setter
    def sweep_index(self, key, el):
        self.write('IterSweep {} {}'.format(key, el))

    @DictFeat(units="ns")
    def sweep_value(self, key):
        return int(1e9 * float(self.query('GetSweepVal {}'.format(key))))

    @Action()
    def stream(self):
        self.write("Stream")
