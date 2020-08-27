# -*- coding: utf-8 -*-
import os
import time

import numpy as np
import pandas as pd
from lantz.core import Action, Driver, Feat, Q_

from lantz.drivers.ni.daqmx import AnalogOutputTask, VoltageOutputChannel

default_folder = os.path.dirname(__file__)
default_filename = os.path.join(default_folder, 'power_calibration.csv')


class V1000F(Driver):
    def __init__(self, ch, calibration_file=default_filename, min_max=(0., 5.)):
        super().__init__()
        self._voltage = 0
        self.ch = ch
        self.min_max = min_max
        self.calibration_file = calibration_file
        return

    @Feat(units='V', limits=(0., 5.))
    def voltage(self):
        return self._voltage

    @voltage.setter
    def voltage(self, val):
        task_config = {
            'data': np.ones(5) * val,
            'auto_start': True,
        }
        self.task.write(**task_config)
        self._voltage = val

    @Feat(units='W', limits=(0, 100.e-3))
    def power(self):
        return self.voltage2power(self.voltage)

    @power.setter
    def power(self, val):
        self.voltage = self.power2voltage(val)

    def _get_cal(self):
        d = pd.read_csv(self.calibration_file)
        return d.voltage.values, d.power.values

    def power2voltage(self, p):
        cal_vs, cal_ps = self._get_cal()
        if type(p) is Q_:
            p = p.to('W').m
        return Q_(np.interp(p, cal_ps, cal_vs, period=1000), 'V')

    def voltage2power(self, v):
        cal_vs, cal_ps = self._get_cal()
        if type(v) is Q_:
            v = v.to('V').m
        return Q_(np.interp(v, cal_vs, cal_ps), 'W')

    def initialize(self):
        self.task = AnalogOutputTask('Analog_Out_{}'.format(self.ch.split('/')[-1]))
        VoltageOutputChannel(self.ch, min_max=self.min_max, units='volts', task=self.task)

    def finalize(self):
        self.task.clear()

    @Action()
    def run_calibration(self, power_fun, npoints=500, min_pt=0, max_pt=5, delay_per_point=0.1):
        voltages = np.linspace(min_pt, max_pt, npoints)
        powers = np.zeros(npoints)
        for i, v in enumerate(voltages):
            self.voltage = Q_(v, 'V')
            time.sleep(delay_per_point)
            powers[i] = power_fun().to('W').m
            print('{} V = {} W'.format(v, powers[i]))
        data = np.transpose(np.array([voltages, powers]))
        np.savetxt(self.calibration_file, data, delimiter=",", header='voltage,power', comments='')
        return data
