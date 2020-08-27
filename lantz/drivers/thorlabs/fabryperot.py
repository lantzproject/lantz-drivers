"""
    lantz.drivers.thorlab.fabryperot
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of Fabry Perot using the daq

    Author: Alexandre Bourassa
    Date: 4/17/2019
"""

import numpy as np
from lantz.core import Action, Driver, Feat, Q_

from lantz.drivers.ni.daqmx import AnalogInputTask, DigitalOutputChannel, DigitalOutputTask, VoltageInputChannel


def peakdet(arr, delta=0.1):
    mintab, maxtab = list(), list()
    arr = np.asarray(arr)
    x = np.arange(len(arr))
    if delta <= 0:
        return maxtab, mintab
    mn, mx = np.Inf, -np.Inf
    mnpos, mxpos = np.NaN, np.NaN
    lookformax = True
    for idx in range(len(arr)):
        this = arr[idx]
        if this > mx:
            mx = this
            mxpos = x[idx]
        if this < mn:
            mn = this
            mnpos = x[idx]
        if lookformax:
            if this < mx - delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[idx]
                lookformax = False
        else:
            if this > mn + delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[idx]
                lookformax = True
    return np.array(maxtab), np.array(mintab)


class FabryPerot(Driver):

    def __init__(self, ch, sw_ch, active_trig_ch, passive_trig_ch=None):

        self._points = 1000
        self._period = Q_(10, 'ms')
        self._selectivity = 0.1
        self.ch = ch
        self.sw_ch = sw_ch
        self.active_trig_ch = active_trig_ch
        self.passive_trig_ch = passive_trig_ch

        self._single_mode = True
        self._peak_locations = list()
        self._trace = np.zeros(self.points)
        self._sw_state = False
        self._trig_ch = self.passive_trig_ch

        self.acq_task = AnalogInputTask('fp_readout')
        self.sw_task = DigitalOutputTask('fp_sw_task')
        return

    def setup_sw_task(self):
        self.sw_task.clear()
        self.sw_task = DigitalOutputTask('fp_sw_task')
        self.sw_task.add_channel(DigitalOutputChannel(self.sw_ch))
        clock_config = {
            'source': 'OnboardClock',
            'rate': 10000,
            'sample_mode': 'finite',
            'samples_per_channel': 100,
        }

    def setup_task(self):
        self.acq_task.clear()
        self.acq_task = AnalogInputTask('fp_readout')
        self.acq_task.add_channel(VoltageInputChannel(self.ch))
        if not self._trig_ch is None:
            self.acq_task.configure_trigger_digital_edge_start(self._trig_ch, edge='rising')

        rate = self.points / self.period
        clock_config = {
            'source': 'OnboardClock',
            'rate': rate.to('Hz').magnitude,
            'sample_mode': 'finite',
            'samples_per_channel': self._points,
        }
        self.acq_task.configure_timing_sample_clock(**clock_config)

    def initialize(self):
        self.setup_sw_task()
        self.setup_task()

    def finalize(self):
        self.sw_task.clear()
        self.acq_task.clear()

    @Feat(values={True: True, False: False})
    def active_mode(self):
        return self._sw_state

    @active_mode.setter
    def active_mode(self, state):
        state_pts = np.ones(100) if state else np.zeros(100)
        self.sw_task.write(state_pts)
        self._sw_state = state

        # Switch trigger channel
        self._trig_ch = self.active_trig_ch if state else self.passive_trig_ch
        self.setup_task()
        return

    @Feat()
    def selectivity(self):
        return self._selectivity

    @selectivity.setter
    def selectivity(self, val):
        self._selectivity = val

    @Feat(units='ms')
    def period(self):
        return self._period

    @period.setter
    def period(self, val):
        self._period = val
        self.setup_task()

    @Feat()
    def points(self):
        return self._points

    @points.setter
    def points(self, val):
        self._points = val
        self.setup_task()

    @Feat()
    def single_mode(self):
        return bool(self._single_mode)

    @Action()
    def peak_locations(self):
        return self._peak_locations

    @Action()
    def peak_magnitudes(self):
        return self._peak_magnitudes

    @Action()
    def trace(self):
        return self._trace

    @Action()
    def refresh(self):
        self.acq_task.start()
        data = self.acq_task.read(samples_per_channel=self.points).flatten()
        self.acq_task.stop()
        data = data.flatten()

        # remove spurious edge signals
        # display_data = np.array(data)

        # normalize signal
        data /= np.max(data)

        # Peak Detection
        peak_info, valley_info = peakdet(data, delta=self._selectivity)
        if not peak_info.size:
            self._single_mode = False
            self._peak_locations = list()
            self._trace = np.zeros(self.points)
            return
        peak_locations = peak_info[:, 0]
        peak_magnitudes = peak_info[:, 1]

        # normalize peak magnitudes
        peak_magnitudes /= np.max(peak_magnitudes)

        # TODO Are these really necessary
        xvar = 0.1
        yvar = 0.1

        # Filter peaks
        filtered_locations = list()
        for peak_location in peak_locations:
            if np.sum(np.abs(peak_locations - peak_location) > xvar * len(peak_locations)):
                filtered_locations.append(peak_location)

        # Convert peak location to ms
        peak_locations = np.array(filtered_locations) * self.period.to('ms').m / self.points

        # Cut the begining and end to prevent wrap arounds
        peak_magnitudes = peak_magnitudes[peak_locations > 0.05 * self.period.to('ms').m]
        peak_locations = peak_locations[peak_locations > 0.05 * self.period.to('ms').m]
        peak_magnitudes = peak_magnitudes[peak_locations < 0.95 * self.period.to('ms').m]
        peak_locations = peak_locations[peak_locations < 0.95 * self.period.to('ms').m]

        self._single_mode = len(peak_locations) < 4 and np.var(peak_magnitudes) < yvar
        self._peak_locations = peak_locations
        self._peak_magnitudes = peak_magnitudes
        self._trace = data
        return

# class Fabry_Perot(DigitalSwitch):
#     @Action()
#     def passive_mode(self):
#         self.output(False)

#     @Action()
#     def active_mode(self):
#         self.output(True)
