# -*- coding: utf-8 -*-
"""
    lantz.drivers.newport.motionesp301
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers to control ESP300 and ESP301 motion controller 
    via USB or serial.

    For USB, one first have to install the windows driver from newport.

    :copyright: 2015, see AUTHORS for more details.
    :license: GPL, see LICENSE for more details.
    
    Source: Instruction Manual (Newport)
"""

import copy
import time

import numpy as np
# from lantz.serial import SerialDriver
from lantz.core import Action, Feat, MessageBasedDriver, ureg
from lantz.core.processors import convert_to
from pyvisa import constants


# Add generic units:
# ureg.define('unit = unit')
# ureg.define('encodercount = count')
# ureg.define('motorstep = step')


class ESP301(MessageBasedDriver):
    """ Newport ESP301 motion controller. It assumes all axes to have units mm

    :param scan_axes: Should one detect and add axes to the controller
    """

    DEFAULTS = {
        'COMMON': {'write_termination': '\r\n',
                   'read_termination': '\r\n', },
        'ASRL': {
            'timeout': 4000,  # ms
            'encoding': 'ascii',
            'data_bits': 8,
            'baud_rate': 19200,
            'parity': constants.Parity.none,
            'stop_bits': constants.StopBits.one,
            'flow_control': constants.VI_ASRL_FLOW_RTS_CTS,  # constants.VI_ASRL_FLOW_NONE,
        },
    }

    def initialize(self):
        super().initialize()
        self.detect_axis()

    @classmethod
    def via_usb(cls, port, name=None, **kwargs):
        """Connect to the ESP301 via USB. Internally this goes via serial"""
        cls.DEFAULTS = copy.deepcopy(cls.DEFAULTS)
        cls.DEFAULTS['ASRL'].update({'baud_rate': 921600})
        return cls.via_serial(port=port, name=name, **kwargs)

    @Action()
    def detect_axis(self):
        """ Find the number of axis available.
        
        The detection stops as soon as an empty controller is found.
        """
        self.axes = []
        i = 0
        scan_axes = True
        while scan_axes:
            try:
                i += 1
                id = self.query('%dID?' % i)
                axis = ESP301Axis(self, i, id)
                self.axes.append(axis)
            except:
                err = self.get_errors()
                if err == 37:  # Axis number missing
                    self.axes.append(None)
                elif err == 9:  # Axis number out of range
                    scan_axes = False
                elif err == 6:  # Axis number out of range, but wrong errorcode
                    scan_axes = False
                else:  # Dunno...
                    raise Exception(err)

    @Action()
    def get_errors(self):
        err = int(self.query('TE?'))
        return err

    @Feat(read_once=False)
    def position(self):
        return [axis.position for axis in self.axes]

    @Feat(read_once=False)
    def _position_cached(self):
        return [axis._position_cached for axis in self.axes]

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
            if not p is None:
                axis._set_position(p, wait=False)
        if wait_until_done:
            for p, axis in zip(pos, self.axes):
                if not p is None:
                    axis._wait_until_done()
                    axis.check_position(p)
            return self.position

        return pos

    @Action()
    def motion_done(self):
        for axis in self.axes: axis._wait_until_done()

    def finalize(self):
        for axis in self.axes:
            if axis is not None:
                del (axis)
        super().finalize()


# class ESP301GPIB( ESP301, GPIBVisaDriver):
#    """ Untested!
#    """
#    def __init__(self, scan_axes=True, resource_name= 'GPIB0::2::INSTR', *args, **kwargs):
#        # Read number of axes and add axis objects
#        self.scan_axes = scan_axes
#        super().__init__(resource_name=resource_name, *args, **kwargs)


class ESP301Axis(ESP301):
    def __init__(self, parent, num, id, *args, **kwargs):
        # super(ESP301Axis, self).__init__(*args, **kwargs)
        self.parent = parent
        self.num = num
        self.id = id
        self.wait_time = 0.01  # in seconds * Q_(1, 's')
        self.backlash = 0
        self.wait_until_done = True
        self.accuracy = 0.001  # in units reported by axis
        # Fill position cache:
        self.position

    def __del__(self):
        self.parent = None
        self.num = None

    def id(self):
        return self.id

    @Action()
    def on(self):
        """Put axis on"""
        self.parent.write('%dMO' % self.num)

    @Action()
    def off(self):
        """Put axis on"""
        self.parent.write('%dMF' % self.num)

    @Feat(values={True: '1', False: '0'})
    def is_on(self):
        """
        :return: True is axis on, else false
        """
        return self.parent.query('%dMO?' % self.num)

    @Action(units='mm')
    def define_home(self, val=0):
        """Remap current position to home (0), or to new position

        :param val: new position"""
        self.parent.write('%dDH%f' % (self.num, val))

    @Feat(units='mm', read_once=False)
    def _position_cached(self):
        return self.__position_cached

    @_position_cached.setter
    def _position_cached(self, pos):
        self.__position_cached = pos

    @Feat(units='mm')
    def position(self):
        self._position_cached = float(self.parent.query('%dTP?' % self.num)) * ureg.mm
        return self._position_cached

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
            # backlash = self.backlash.to('mm').magnitude
            backlash = convert_to('mm', on_dimensionless='ignore')(self.backlash).magnitude
            if (backlash < 0 and position > pos) or \
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
        self.parent.write('%dPA%f' % (self.num, pos))

    def check_position(self, pos):
        '''Check is stage is at expected position'''
        if np.isclose(self.position, pos, atol=self.accuracy):
            return True
        self.log_error('Position accuracy {} is not reached.'
                       'Expected: {}, measured: {}'.format(self.accuracy, pos, self._position_cached))
        return False

    @Feat(units='mm/s')
    def max_velocity(self):
        return float(self.parent.query('%dVU?' % self.num))

    @max_velocity.setter
    def max_velocity(self, velocity):
        self.parent.write('%dVU%f' % (self.num, velocity))

    @Feat(units='mm/s**2')
    def max_acceleration(self):
        return float(self.parent.query('%dAU?' % self.num))

    @max_acceleration.setter
    def max_acceleration(self, velocity):
        self.parent.write('%dAU%f' % (self.num, velocity))

    @Feat(units='mm/s')
    def velocity(self):
        return float(self.parent.query('%dVA?' % self.num))

    @velocity.setter
    def velocity(self, velocity):
        """
        :param velocity: Set the velocity that the axis should use when moving
        :return:
        """
        self.parent.write('%dVA%f' % (self.num, velocity))

    @Feat(units='mm/s**2')
    def acceleration(self):
        return float(self.parent.query('%dVA?' % self.num))

    @acceleration.setter
    def acceleration(self, acceleration):
        """
        :param acceleration: Set the acceleration that the axis should use when starting
        :return:
        """
        self.parent.write('%dAC%f' % (self.num, acceleration))

    @Feat(units='mm/s')
    def actual_velocity(self):
        return float(self.parent.query('%dTV' % self.num))

    @actual_velocity.setter
    def actual_velocity(self, val):
        raise NotImplementedError

    @Action()
    def stop(self):
        """Emergency stop"""
        self.parent.write(u'{0:d}ST'.format(self.num))

    @Feat(values={True: '1', False: '0'})
    def motion_done(self):
        while True:
            ret = self.parent.query('%dMD?' % self.num)
            if ret in ['1', '0']:
                break
            else:
                time.sleep(self.wait_time)
        return ret

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
    def units(self):
        ret = int(self.parent.query(u'{}SN?'.format(self.num)))
        vals = {0: 'encoder count',
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
        return vals[ret]

    # @units.setter
    # def units(self, val):
    #     self.parent.write('%SN%' % (self.num, val))

    def _wait_until_done(self):
        # wait_time = convert_to('seconds', on_dimensionless='warn')(self.wait_time)
        time.sleep(self.wait_time)
        while not self.motion_done:
            time.sleep(self.wait_time)  # wait_time.magnitude)


if __name__ == '__main__':
    import argparse
    import lantz.log

    parser = argparse.ArgumentParser(description='Test ESP301 driver')
    parser.add_argument('-p', '--port', type=str, default='1',
                        help='Serial port to connect to')

    args = parser.parse_args()
    lantz.log.log_to_socket(lantz.log.DEBUG)

    with ESP301.via_usb(port=args.port) as inst:
        # inst.initialize() # Initialize the communication with the power meter
        # Find the status of all axes:
        for axis in inst.axes:
            print('Axis {} Position {} is_on {} max_velocity {} velocity {}'.format(axis.num, axis.position,
                                                                                    axis.is_on, axis.max_velocity,
                                                                                    axis.velocity))
