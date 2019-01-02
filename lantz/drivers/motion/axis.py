# -*- coding: utf-8 -*-
"""
    lantz.drivers.newport.motion axis
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    General class that implements the commands used for motion
    drivers

    :copyright: 2018, see AUTHORS for more details.
    :license: GPL, see LICENSE for more details.


"""


from lantz.feat import Feat
from lantz.action import Action
from lantz.driver import Driver
from lantz import Q_
from lantz.processors import convert_to
import time
import numpy as np

#  Add generic units:
# ureg.define('unit = unit')
# ureg.define('encodercount = encodercount')
# ureg.define('motorstep = motorstep')


class MotionAxisSingle(Driver):
    def __init__(self, *args, **kwargs):
        self.wait_time = 0.01  # in seconds * Q_(1, 's')
        self.wait_until_done = True
        self.accuracy = 0.001  # in units reported by axis
        self._units = 'mm'

    @Feat()
    def idn(self):
        return self.query('ID?')

    @Feat()
    def position(self):
        raise NotImplementedError

    @position.setter
    def position(self, pos):
        """
        Waits until movement is done if self.wait_until_done = True.

        :param pos: new position
        """
        self._set_position(pos, wait=self.wait_until_done)

    @Action(units=['mm', None])
    def _set_position(self, pos, wait=None):
        """
        Move to an absolute position, taking into account backlash.

        When self.backlash is to a negative value the stage will always move
         from low to high values. If necessary, a extra step with length
         self.backlash is set.

        :param pos: New position in mm
        :param wait: wait until stage is finished
        """

        # First do move to extra position if necessary

        self.__set_position(pos)
        if wait:
            self._wait_until_done()
            self.check_position(pos)

    def __set_position(self, pos):
        """
        Move stage to a certain position
        :param pos: New position
        """
        self.write('PA%f' % (pos))

    @Action(units='mm')
    def check_position(self, pos):
        '''Check is stage is at expected position'''
        if np.isclose(self.position, pos, atol=self.accuracy):
            return True
        self.log_error('Position accuracy {} is not reached.'
                       'Expected: {}, measured: {}'.format(self.accuracy,
                                                           pos,
                                                           self.position))
        return False


    @Feat(values={True: '1', False: '0'})
    def motion_done(self):
        raise NotImplementedError

    @Feat()
    def units(self):
        return self._units

    @units.setter
    def units(self, units):
        super().update_units(self._units, units)
        self._units = units

    def _wait_until_done(self):
        wait_time = convert_to('seconds', on_dimensionless='ignore')(self.wait_time)
        time.sleep(wait_time)
        while not self.motion_done:
            time.sleep(wait_time)
        return True


class MotionAxisMultiple(MotionAxisSingle):
    def __init__(self, parent, num, id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.num = num
        self._idn = id

    def __del__(self):
        self.parent = None
        self.num = None

    def query(self, command, *, send_args=(None, None), recv_args=(None, None)):
        return self.parent.query('{:d}{}'.format(self.num, command),
                                 send_args=send_args, recv_args=recv_args)

    def write(self, command, *args, **kwargs):
        return self.parent.write('{:d}{}'.format(self.num, command),
                                 *args, **kwargs)

class BacklashMixing():
    '''Adds functionality to a motionaxis: blacklash correction'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backlash = 0

    @Action(units=['mm', None])
    def _set_position(self, pos, wait=None):
        """
        Move to an absolute position, taking into account backlash.

        When self.backlash is to a negative value the stage will always move
         from low to high values. If necessary, a extra step with length
         self.backlash is set.

        :param pos: New position in mm
        :param wait: wait until stage is finished
        """

        # First do move to extra position if necessary
        if self.backlash:
            position = self.position.magnitude
            backlash = convert_to(self.units, on_dimensionless='ignore'
                                   )(self.backlash).magnitude
            if (backlash < 0 and position > pos) or\
               (backlash > 0 and position < pos):

                self.log_info('Using backlash')
                self.__set_position(pos + backlash)
                self._wait_until_done()

        # Than move to final position
        self.__set_position(pos)
        if wait:
            self._wait_until_done()
            self.check_position(pos)

    def __set_position(self, pos):
        """
        Move stage to a certain position
        :param pos: New position
        """
        self.write('PA%f' % (pos))
        self.last_set_position = pos