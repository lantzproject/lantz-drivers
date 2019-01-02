# -*- coding: utf-8 -*-
"""
    lantz.drivers.newport.motion axis
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    General class that implements the commands used for motion
    drivers

    :copyright: 2018, see AUTHORS for more details.
    :license: GPL, see LICENSE for more details.


"""

import time
import numpy as np

from lantz.feat import Feat
from lantz.action import Action
from lantz.driver import Driver
from pyvisa import constants
from lantz import Q_, ureg
from lantz.processors import convert_to

from .axis import MotionAxisSingle, MotionAxisMultiple

#  Add generic units:
# ureg.define('unit = unit')
# ureg.define('encodercount = count')
# ureg.define('motorstep = step')


class MotionControllerMultiAxis(Driver):
    """ Motion controller that can detect multiple axis

    """
    def initialize(self):
        super().initialize()

    @Feat()
    def idn(self):
        raise AttributeError('Not implemented')

    @Action()
    def detect_axis(self):
        """ Find the number of axis available.

        The detection stops as soon as an empty controller is found.
        """
        pass

    @Action()
    def get_errors(self):
        raise AttributeError('Not implemented')

    @Feat(read_once=False)
    def position(self):
        return [axis.position for axis in self.axes]

    @Feat(read_once=False)
    def _position_cached(self):
        return [axis.recall('position') for axis in self.axes]

    @position.setter
    def position(self, pos):
        """Move to position (x,y,...)"""
        return self._position(pos)

    @Action()
    def _position(self, pos, read_pos=None, wait_until_done=True):
        """Move to position (x,y,...)"""
        if read_pos is not None:
            self.log_error('kwargs read_pos for function _position is deprecated')

        for p, axis in zip(pos, self.axes):
            if p is not None:
                axis._set_position(p, wait=False)
        if wait_until_done:
            for p, axis in zip(pos, self.axes):
                if p is not None:
                    axis._wait_until_done()
                    axis.check_position(p)
            return self.position

        return pos

    @Action()
    def motion_done(self):
        for axis in self.axes:
            axis._wait_until_done()

    def finalize(self):
        for axis in self.axes:
            if axis is not None:
                del (axis)
        super().finalize()



class MotionControllerSingleAxis(MotionAxisSingle):
    """ Motion controller that can only has sinlge axis

    """
    def initialize(self):
        super().initialize()