"""
    lantz.drivers.ni.daqmx.utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    These are simple implementation of commons functionalities.

    Author: Alexandre Bourassa
    Date: 04/08/2017
"""
from lantz import Driver
from lantz.driver import Action
from lantz.drivers.ni.daqmx import DigitalOutputTask, DigitalOutputChannel
import numpy as np

class DigitalSwitch(Driver):

    def __init__(self, ch='/dev1/po.0'):
        super().__init__()
        self.task = DigitalOutputTask()
        self.task.add_channel(DigitalOutputChannel(ch))
        clock_config = {
            'source': 'OnboardClock',
            'rate': 10000,
            'sample_mode': 'finite',
            'samples_per_channel': 100,
        }

    @Action()
    def output(self, state):
    	if state:
    		state_pts = np.ones(100)
    	else:
    		state_pts = np.zeros(100)
        with self.task as task:
            self.task.write(state_pts)