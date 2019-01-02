# -*- coding: utf-8 -*-
"""
    lantz.drivers.newport.motion axis
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    General class that implements the commands used for several smaract motion
    drivers using the ASCII mode (via serial or serial via USB).

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

formats = {'one_param': ''}

class SCU(MessageBasedDriver, MotionControllerMultiAxis):
    """ Driver for SCU controller with multiple axis

    """
    DEFAULTS = {
                'COMMON': {'write_termination': '\n',
                           'read_termination': '\n', },
                'ASRL': {
                    'timeout': 100,  # ms
                    'encoding': 'ascii',
                    'data_bits': 8,
                    'baud_rate': 9600,
                    'parity': constants.Parity.none,
                    'stop_bits': constants.StopBits.one,
                    #'flow_control': constants.VI_ASRL_FLOW_NONE,
                    'flow_control': constants.VI_ASRL_FLOW_XON_XOFF,  # constants.VI_ASRL_FLOW_NONE,
                    },
                }

    def initialize(self):
        super().initialize()
        self.detect_axis()

    def query(self, command, *, send_args=(None, None), recv_args=(None, None)):
        return MotionControllerMultiAxis.query(self, ':{}'.format(command),
                                 send_args=send_args, recv_args=recv_args)

    def write(self, command, *args, **kwargs):
        return MotionControllerMultiAxis.write(self,':{}'.format(command),
                                 *args, **kwargs)

    @Feat()
    def idn(self):
        return self.parse_query('I', format='I{:s}')

    @Action()
    def detect_axis(self):
        """ Find the number of axis available.

        The detection stops as soon as an empty controller is found.
        """
        pass


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
