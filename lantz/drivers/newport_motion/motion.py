# -*- coding: utf-8 -*-
"""
    lantz.drivers.newport.motion axis
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    General class that implements the commands used for several newport motion
    drivers

    :copyright: 2018, see AUTHORS for more details.
    :license: GPL, see LICENSE for more details.

    Source: Instruction Manual (Newport)

"""


from lantz.feat import Feat
from lantz.action import Action
from lantz.messagebased import MessageBasedDriver
from pyvisa import constants
from lantz import Q_, ureg
from lantz.processors import convert_to
from lantz.drivers.motion import MotionAxisMultiple, MotionControllerMultiAxis, BacklashMixing
import time
import numpy as np

#  Add generic units:
# ureg.define('unit = unit')
# ureg.define('encodercount = count')
# ureg.define('motorstep = step')


class MotionController():
    """ Newport motion controller. It assumes all axes to have units mm

    """
    print("newton_motion.MotionController is deprecated. Use lantz.drivers.motion.MotionControllerMultiAxis instead")


UNITS = {0: 'encoder count',
        1: 'motor step',
        2: 'millimeter',
        3: 'micrometer',
        4: 'inches',
        5: 'milli-inches',
        6: 'micro-inches',
        7: 'degree',
        8: 'gradian',
        9: 'radian',
        10: 'milliradian',
        11: 'microradian', }


class MotionAxis(MotionAxisMultiple, BacklashMixing):
    def __del__(self):
        self.parent = None
        self.num = None

    def query(self, command, *, send_args=(None, None), recv_args=(None, None)):
        return self.parent.query('{:d}{}'.format(self.num, command),
                                 send_args=send_args, recv_args=recv_args)

    def write(self, command, *args, **kwargs):
        return self.parent.write('{:d}{}'.format(self.num, command),
                                 *args, **kwargs)

    @Feat()
    def idn(self):
        return self.query('ID?')

    @Action()
    def on(self):
        """Put axis on"""
        self.write('MO')

    @Action()
    def off(self):
        """Put axis on"""
        self.write('MF')

    @Feat(values={True: '1', False: '0'})
    def is_on(self):
        """
        :return: True is axis on, else false
        """
        return self.query('MO?')

    @Action(units='mm')
    def define_home(self, val=0):
        """Remap current position to home (0), or to new position

        :param val: new position"""
        self.write('DH%f' % val)

    @Action()
    def home(self):
        """Execute the HOME command"""
        self.write('OR')

    @Feat(units='mm')
    def position(self):
        return self.query('TP?')

    @position.setter
    def position(self, pos):
        """
        Waits until movement is done if self.wait_until_done = True.

        :param pos: new position
        """
        if not self.is_on:
            self.log_error('Axis not enabled. Not moving!')
            return

        # First do move to extra position if necessary
        self._set_position(pos, wait=self.wait_until_done)


    def __set_position(self, pos):
        """
        Move stage to a certain position
        :param pos: New position
        """
        self.write('PA%f' % (pos))
        self.last_set_position = pos

    @Feat(units='mm/s')
    def max_velocity(self):
        return float(self.query('VU?'))

    @max_velocity.setter
    def max_velocity(self, velocity):
        self.write('VU%f' % (velocity))

    @Feat(units='mm/s**2')
    def max_acceleration(self):
        return float(self.query('AU?'))

    @max_acceleration.setter
    def max_acceleration(self, velocity):
        self.write('AU%f' % (velocity))

    @Feat(units='mm/s')
    def velocity(self):
        return float(self.query('VA?'))

    @velocity.setter
    def velocity(self, velocity):
        """
        :param velocity: Set the velocity that the axis should use when moving
        :return:
        """
        self.write('VA%f' % (velocity))

    @Feat(units='mm/s**2')
    def acceleration(self):
        return float(self.query('VA?'))

    @acceleration.setter
    def acceleration(self, acceleration):
        """
        :param acceleration: Set the acceleration that the axis should use
                             when starting
        :return:
        """
        self.write('AC%f' % (acceleration))

    @Feat(units='mm/s')
    def actual_velocity(self):
        return float(self.query('TV'))

    @actual_velocity.setter
    def actual_velocity(self, val):
        raise NotImplementedError

    @Action()
    def stop(self):
        """Emergency stop"""
        self.write('ST')

    @Feat(values={True: '1', False: '0'})
    def motion_done(self):
        return self.query('MD?')

    # Not working yet, see https://github.com/hgrecco/lantz/issues/35
    # @Feat(values={Q_('encodercount'): 0,
    #                     Q_('motor step'): 1,
    #                     Q_('millimeter'): 2,
    #                     Q_('micrometer'): 3,
    #                     Q_('inches'): 4,
    #                     Q_('milli-inches'): 5,
    #                     Q_('micro-inches'): 6,
    #                     Q_('degree'): 7,
    #                     Q_('gradian'): 8,
    #                     Q_('radian'): 9,
    #                     Q_('milliradian'): 10,
    #                     Q_('microradian'): 11})
    @Feat()
    def units(self):
        ret = int(self.query(u'SN?'))
        return UNITS[ret]

    @units.setter
    def units(self, val):
        # No check implemented yet
        self.write('%SN%' % (self.num, UNITS.index(val)))
        super().units = val

    def _wait_until_done(self):
        # wait_time = convert_to('seconds', on_dimensionless='warn')(self.wait_time)
        time.sleep(self.wait_time)
        while not self.motion_done:
            time.sleep(self.wait_time)
        return True
