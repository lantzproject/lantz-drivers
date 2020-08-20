# -*- coding: utf-8 -*-
"""
    lantz.drivers.newport.fsm300
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of FSM300 using NI DAQ controller

    Author: Kevin Miao
    Date: 9/27/2016
"""

from lantz import Driver
from lantz.driver import Feat, DictFeat, Action
from lantz.drivers.ni.daqmx import AnalogOutputTask, VoltageOutputChannel
from lantz.drivers.ni.simple_daq import Read_DAQ

from lantz import Q_

import time

import numpy as np

def enforce_units(val, units):
    if not isinstance(val, Q_):
        val = Q_(val, units)
    else:
        val = val.to(units)
    return val

def enforce_point_units(point, units='um'):
    point = enforce_units(point[0], units) , enforce_units(point[1], units)
    return point

class FSM300(Driver):

    def __init__(self, x_ao_ch, y_ao_ch,
                 ao_smooth_rate=Q_('10 kHz'), ao_smooth_steps=Q_('1000 1/V'),
                 limits=((Q_(-10, 'V'), Q_(10, 'V')), (Q_(-10, 'V'), Q_(10, 'V'))),
                 cal=(Q_(10, 'um/V'), Q_(7.6, 'um/V'))):
        self.x_limits_mag = tuple(float(val / Q_('1 V')) for val in limits[0])
        self.y_limits_mag = tuple(float(val / Q_('1 V')) for val in limits[1])

        self.ao_smooth_rate = ao_smooth_rate
        self.ao_smooth_steps = ao_smooth_steps
        self.cal = cal

        self._position = (Q_('0 um'), Q_('0 um'))

        super().__init__()

        self.x_ao_ch = x_ao_ch
        self.y_ao_ch = y_ao_ch

        return

    def initialize(self):
        self.task = AnalogOutputTask('fsm300')
        VoltageOutputChannel(self.x_ao_ch, name='fsm_x', min_max=self.x_limits_mag, units='volts', task=self.task)
        VoltageOutputChannel(self.y_ao_ch, name='fsm_y', min_max=self.y_limits_mag, units='volts', task=self.task)
        super().initialize()

    def finalize(self):
        self.task.clear()
        super().finalize()


    def ao_smooth_func(self, init_point, final_point):
        init_x, init_y = init_point
        final_x, final_y = final_point

        init_x_voltage, final_x_voltage = init_x / self.cal[0], final_x / self.cal[0]
        init_y_voltage, final_y_voltage = init_y / self.cal[1], final_y / self.cal[1]
        diff_x_voltage = final_x_voltage - init_x_voltage
        diff_y_voltage = final_y_voltage - init_y_voltage

        diff_voltage = max(abs(diff_x_voltage), abs(diff_y_voltage))
        steps = int(np.ceil(diff_voltage * self.ao_smooth_steps))
        init = np.array([val.to('V').magnitude for val in [init_x_voltage, init_y_voltage]])
        diff = np.array([val.to('V').magnitude for val in [diff_x_voltage, diff_y_voltage]])

        versine_steps = (1.0 - np.cos(np.linspace(0.0, np.pi, steps))) / 2.0

        step_voltages = np.outer(np.ones(steps), init) + np.outer(versine_steps, diff)
        return step_voltages

    def ao_linear_func(self, init_point, final_point, steps):
        init_x, init_y = init_point
        final_x, final_y = final_point

        init_x_voltage, final_x_voltage = init_x / self.cal[0], final_x / self.cal[0]
        init_y_voltage, final_y_voltage = init_y / self.cal[1], final_y / self.cal[1]
        diff_x_voltage = final_x_voltage - init_x_voltage
        diff_y_voltage = final_y_voltage - init_y_voltage

        diff_voltage = max(abs(diff_x_voltage), abs(diff_y_voltage))
        init = np.array([val.to('V').magnitude for val in [init_x_voltage, init_y_voltage]])
        diff = np.array([val.to('V').magnitude for val in [diff_x_voltage, diff_y_voltage]])

        linear_steps = np.linspace(0.0, 1.0, steps)

        step_voltages = np.outer(np.ones(steps), init) + np.outer(linear_steps, diff)
        return step_voltages

    @Feat()
    def abs_position(self):
        return self._position


    @abs_position.setter
    def abs_position(self, point):
        point = enforce_point_units(point)
        step_voltages = self.ao_smooth_func(self._position, point)
        if step_voltages.size:
            steps = step_voltages.shape[0]
            clock_config = {
                'source': 'OnboardClock',
                'rate': self.ao_smooth_rate.to('Hz').magnitude,
                'sample_mode': 'finite',
                'samples_per_channel': steps,
            }
            self.task.configure_timing_sample_clock(**clock_config)
            self.task.configure_trigger_disable_start()
            task_config = {
                'data': step_voltages,
                'auto_start': False,
                'timeout': Q_(0,'s'),
                'group_by': 'scan',
            }
            self.task.write(**task_config)
            self.task.start()
            time.sleep((steps / self.ao_smooth_rate).to('s').magnitude)
            self.task.stop()
        self._position = point

    @Action()
    def line_scan(self, init_point, final_point, steps, acq_task, acq_rate=Q_('20 kHz'), pts_per_pos=100):
        init_point = enforce_point_units(init_point)
        final_point = enforce_point_units(final_point)
        timeout = enforce_units(1.5*(pts_per_pos*steps/acq_rate), units='s')
        # AO smooth move to initial point
        self.abs_position = init_point
        step_voltages = self.ao_linear_func(init_point, final_point, steps)
        if acq_task.IO_TYPE == 'CI':
            chs = list(acq_task.channels.keys())
            if not chs:
                raise ValueError('acquisition task must have at least one channel')
            ch = chs[0]
            dev = ch.split('/')[0]

            step_voltages = np.repeat(step_voltages, pts_per_pos + 1, axis=0)
            clock_config = {
                'rate': acq_rate.to('Hz').magnitude,
                'sample_mode': 'finite',
                'samples_per_channel': len(step_voltages),
            }
            self.task.configure_timing_sample_clock(**clock_config)
            clock_config = {
                'source': '/{}/ao/SampleClock'.format(dev),
                'rate': acq_rate.to('Hz').magnitude,
                'sample_mode': 'finite',
                'samples_per_channel': len(step_voltages),
            }
            acq_task.configure_timing_sample_clock(**clock_config)
            task_config = {
                'data': step_voltages,
                'auto_start': False,
                'timeout': Q_('0 s'),
                'group_by': 'scan',
            }
            self.task.write(**task_config)
            acq_task.arm_start_trigger_source = 'ao/StartTrigger'.format(dev)
            acq_task.arm_start_trigger_type = 'digital_edge'
            acq_task.start()
            self.task.start()
            scanned = acq_task.read(samples_per_channel=len(step_voltages), timeout=timeout)
            acq_task.stop()
            self.task.stop()
            scanned = scanned.reshape((steps, pts_per_pos + 1))
            averaged = np.diff(scanned).mean(axis=1)
            return averaged*acq_rate.to('Hz').magnitude
        elif acq_task.IO_TYPE == 'AI':
            step_voltages = np.repeat(step_voltages, pts_per_pos, axis=0)
            clock_config = {
                'source': 'OnboardClock',
                'rate': acq_rate.to('Hz').magnitude,
                'sample_mode': 'finite',
                'samples_per_channel': len(step_voltages),
            }
            print(clock_config)
            self.task.configure_timing_sample_clock(**clock_config)
            acq_task.configure_timing_sample_clock(**clock_config)
            task_config = {
                'data': step_voltages,
                'auto_start': False,
                'timeout': Q_('0 s'),
                'group_by': 'scan',
            }
            self.task.write(**task_config)
            self.task.configure_trigger_digital_edge_start('ai/StartTrigger')
            self.task.start()
            acq_task.start()
            scanned = acq_task.read(samples_per_channel=len(step_voltages), timeout=timeout)
            acq_task.stop()
            self.task.stop()
            scanned = scanned.reshape((steps, pts_per_pos))
            averaged = scanned.mean(axis=1)
            return averaged
        else:
            pass

class Read_FSM(Driver):
    def __init__(self, x_ao_ch, y_ao_ch,
                 ao_smooth_rate=Q_('10 kHz'), ao_smooth_steps=Q_('1000 1/V'),
                 limits=((Q_(-10, 'V'), Q_(10, 'V')), (Q_(-10, 'V'), Q_(10, 'V'))),
                 cal=(Q_(7.6, 'um/V'), Q_(10, 'um/V'))):

        super().__init__()
        self.x_limits, self.y_limits = [(val / Q_('1 V')).m for val in limits[0]], [(val / Q_('1 V')).m for val in limits[1]]
        self.ao_smooth_rate, self.ao_smooth_steps, self.cal = ao_smooth_rate, ao_smooth_steps, cal
        self.x_ao_ch, self.y_ao_ch = x_ao_ch, y_ao_ch

        self._position = (Q_(0.0, 'um'), Q_(0.0, 'um'))
        self._daq = Read_DAQ('Dev1')
        self.acq_task = None

    def initialize(self):
        self.task = AnalogOutputTask('fsm300')
        VoltageOutputChannel(self.x_ao_ch, name='fsm_x', min_max=self.x_limits, units='volts', task=self.task)
        VoltageOutputChannel(self.y_ao_ch, name='fsm_y', min_max=self.y_limits, units='volts', task=self.task)

    def finalize(self):
        self.task.clear()
        self._daq.clear_task(self.task_name)

    @Action()
    def new_input_task(self, read_chs):
        self.task_name = 'Read_FSM_{}'.format(np.random.randint(2**31))
        self._daq.new_task(self.task_name, read_chs)
        self.acq_task = self._daq._tasks[self.task_name]

    @Action()
    def line_scan(self, init_point, final_point, steps, acq_rate=Q_('20 kHz'), pts_per_pos=100):
        if self.acq_task is None:
            raise Exception('Must first define the input task using the "new_input_task" action')

        init_point = enforce_point_units(init_point)
        final_point = enforce_point_units(final_point)
        timeout = enforce_units(1.5*(pts_per_pos*steps/acq_rate), units='s')
        # AO smooth move to initial point
        self._set_position(*init_point)
        step_voltages = self.ao_linear_func(init_point, final_point, steps)
        if self.acq_task.IO_TYPE == 'CI':
            chs = list(self.acq_task.channels.keys())
            if not chs:
                raise ValueError('acquisition task must have at least one channel')
            dev = chs[0].split('/')[0]

            step_voltages = np.repeat(step_voltages, pts_per_pos + 1, axis=0)
            clock_config = {
                'rate': float(acq_rate.to('Hz').m),
                'sample_mode': 'finite',
                'samples_per_channel': len(step_voltages),
            }
            self.task.configure_timing_sample_clock(**clock_config)
            clock_config = {
                'source': '/{}/ao/SampleClock'.format(dev),
                'rate': float(acq_rate.to('Hz').m),
                'sample_mode': 'finite',
                'samples_per_channel': len(step_voltages),
            }
            self.acq_task.configure_timing_sample_clock(**clock_config)
            task_config = {
                'data': step_voltages,
                'auto_start': False,
                'timeout': Q_('0 s'),
                'group_by': 'scan',
            }
            self.task.write(**task_config)
            self.acq_task.arm_start_trigger_source = 'ao/StartTrigger'.format(dev)
            self.acq_task.arm_start_trigger_type = 'digital_edge'
            self.acq_task.start()
            self.task.start()
            scanned = self.acq_task.read(samples_per_channel=len(step_voltages), timeout=timeout)
            self.acq_task.stop()
            self.task.stop()
            scanned = scanned.reshape((steps, pts_per_pos + 1))
            averaged = np.diff(scanned).mean(axis=1)
            self._position = final_point #Set the position now to be at the end of the line
            return averaged*acq_rate.to('Hz').m
        elif self.acq_task.IO_TYPE == 'AI':
            step_voltages = np.repeat(step_voltages, pts_per_pos, axis=0)
            clock_config = {
                'source': 'OnboardClock',
                'rate': float(acq_rate.to('Hz').m),
                'sample_mode': 'finite',
                'samples_per_channel': len(step_voltages),
            }
            self.task.configure_timing_sample_clock(**clock_config)
            self.acq_task.configure_timing_sample_clock(**clock_config)
            task_config = {
                'data': step_voltages,
                'auto_start': False,
                'timeout': Q_('0 s'),
                'group_by': 'scan',
            }
            self.task.write(**task_config)
            self.task.configure_trigger_digital_edge_start('ai/StartTrigger')
            self.task.start()
            self.acq_task.start()
            scanned = self.acq_task.read(samples_per_channel=len(step_voltages), timeout=timeout)
            self.acq_task.stop()
            self.task.stop()
            scanned = scanned.reshape((steps, pts_per_pos))
            averaged = scanned.mean(axis=1)
            self._position = final_point #Set the position now to be at the end of the line
            return averaged
        else:
            pass

    @Feat(units='um')
    def x(self):
        return self._position[0]

    @x.setter
    def x(self, pos):
        self._set_position(pos, self._position[1])

    @Feat(units='um')
    def y(self):
        return self._position[1]

    @y.setter
    def y(self, pos):
        self._set_position(self._position[0], pos)

    @Action()
    def set_position(self, x, y):
        self._set_position(x,y)
        self._position = enforce_point_units([x,y])

    def _set_position(self, x, y):
        target = enforce_point_units([x,y])
        step_voltages = self.ao_smooth_func(self._position, target)
        if step_voltages.size:
            clock_config = {
                'source': 'OnboardClock',
                'rate': self.ao_smooth_rate.to('Hz').m,
                'sample_mode': 'finite',
                'samples_per_channel': step_voltages.shape[0],
            }
            self.task.configure_timing_sample_clock(**clock_config)
            self.task.configure_trigger_disable_start()
            task_config = {
                'data': step_voltages,
                'auto_start': False,
                'timeout': Q_(0,'s'),
                'group_by': 'scan',
            }
            self.task.write(**task_config)
            self.task.start()
            time.sleep((step_voltages.shape[0] / self.ao_smooth_rate).to('s').m)
            self.task.stop()
        self._position = target

    def positions_to_volt(self, pt):
        return np.array([(pt[0] / self.cal[0]).to('V').m, (pt[1] / self.cal[1]).to('V').m])

    def ao_smooth_func(self, pt0, pt1):
        pt0, pt1 = self.positions_to_volt(pt0), self.positions_to_volt(pt1)
        steps = int(np.ceil(max(abs(pt1-pt0)) * self.ao_smooth_steps.to('1/V').m))

        versine_steps = (1.0 - np.cos(np.linspace(0.0, np.pi, steps))) / 2.0
        return np.outer(np.ones(steps), pt0) + np.outer(versine_steps, pt1-pt0)

    def ao_linear_func(self, pt0, pt1, steps):
        pt0, pt1 = self.positions_to_volt(pt0), self.positions_to_volt(pt1)
        linear_steps = np.linspace(0.0, 1.0, steps)

        return np.outer(np.ones(steps), pt0) + np.outer(linear_steps, pt1-pt0)