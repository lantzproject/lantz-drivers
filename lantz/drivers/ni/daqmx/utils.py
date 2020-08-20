"""
    lantz.drivers.ni.daqmx.utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    These are simple implementation of commons functionalities.

    Author: Alexandre Bourassa
    Date: 04/08/2017
"""
from lantz import Driver
from lantz.driver import Feat
from lantz.drivers.ni.daqmx import DigitalOutputTask, DigitalOutputChannel
import numpy as np

class DigitalSwitch(Driver):

    def __init__(self, ch):
        self.ch = ch

    def initialize(self):
        self.task = DigitalOutputTask()
        self.task.add_channel(DigitalOutputChannel(self.ch))
        clock_config = {
            'source': 'OnboardClock',
            'rate': 10000,
            'sample_mode': 'finite',
            'samples_per_channel': 100,
        }
        self.state = False

    def finalize(self):
        self.task.clear()

    @Feat(values={True:True, False:False})
    def state(self):
        return self._state

    @state.setter
    def state(self, _state):
        if _state:
            state_pts = np.ones(100)
        else:
            state_pts = np.zeros(100)
        with self.task as task:
            self.task.write(state_pts)
        self._state = _state
        return

    # @Feat()
    # def output(self, state):
    #     if state:
    #         state_pts = np.ones(100)
    #     else:
    #         state_pts = np.zeros(100)
    #     with self.task as task:
    #         self.task.write(state_pts)
