from lantz.drivers.ni.daqmx import AnalogInputTask, VoltageInputChannel

from lantz.driver import Driver
from lantz.feat import Feat
from lantz import Q_

import numpy as np

class SA201(Driver):

    def __init__(self, input_ch, trigger_ch, acq_time=Q_('10 ms'), pts=1000):
        self.task = AnalogInputTask('SA201')
        self.task.add_channel(VoltageInputChannel(input_ch))
        self.task.configure_trigger_digital_edge_start(trigger_ch, edge='rising')
        self.acq_time = acq_time

        self.pts = self.pts
        return

    def initialize(self):
        pass

    @Feat()
    def scanned(self):
        rate = self.pts / self.acq_time
        clock_config = {
            'source': 'OnboardClock',
            'rate': rate.to('Hz').magnitude,
            'sample_mode': 'finite',
            'samples_per_channel': self.pts,
        }
        timeout = self.pts * 4 / rate
        self.task.configure_timing_sample_clock(**clock_config)
        self.task.start()
        data = self.task.read(samples_per_channel=self.pts, timeout=timeout)
        self.task.stop()
        data = data.flatten()
        return data.tolist()

    def finalize(self):
        self.task.clear()
        return

if __name__ == '__main__':
    input_ch = '/dev1/ai6'
    trig_ch = '/dev1/pfi3'
    fp = SA201(input_ch, trig_ch)
    fp.initialize()
    for _ in range(100):
        print(fp.peaks)
    fp.finalize()
