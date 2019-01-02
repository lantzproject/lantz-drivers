# -*- coding: utf-8 -*-
"""
    lantz.drivers.newport.motionsmc100
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers to control SMC100 controller

    :copyright: 2018, see AUTHORS for more details.
    :license: GPL, see LICENSE for more details.

    Source: Instruction Manual (Newport)

"""


from lantz.feat import Feat
from lantz.action import Action
import pyvisa
from pyvisa import constants

from lantz import Q_, ureg
from lantz.processors import convert_to
from lantz.messagebased import MessageBasedDriver

from lantz.drivers.newport_motion.motion import MotionAxis
from lantz.drivers.motion import MotionControllerMultiAxis

import time
import numpy as np

ERRORS = {"@": "",
          "A": "Unknown message code or floating point controller address.",
          "B": "Controller address not correct.",
          "C": "Parameter missing or out of range.",
          "D": "Execution not allowed.",
          "E": "home sequence already started.",
          "I": "Execution not allowed in CONFIGURATION state.",
          "J": "Execution not allowed in DISABLE state.",
          "H": "Execution not allowed in NOT REFERENCED state.",
          "K": "Execution not allowed in READY state.",
          "L": "Execution not allowed in HOMING state.",
          "M": "Execution not allowed in MOVING state.",
          }

positioner_errors = {
    0b1000000000: '80 W output power exceeded',
    0b0100000000: 'DC voltage too low',
    0b0010000000: 'Wrong ESP stage',
    0b0001000000: 'Homing time out',
    0b0000100000: 'Following error',
    0b0000010000: 'Short circuit detection',
    0b0000001000: 'RMS current limit',
    0b0000000100: 'Peak current limit',
    0b0000000010: 'Positive end of run',
    0b0000000001: 'Negative end of run',
                    }
controller_states = {
    '0A': 'NOT REFERENCED from reset.',
    '0B': 'NOT REFERENCED from HOMING.',
    '0C': 'NOT REFERENCED from CONFIGURATION.',
    '0D': 'NOT REFERENCED from DISABLE.',
    '0E': 'NOT REFERENCED from READY.',
    '0F': 'NOT REFERENCED from MOVING.',
    '10': 'NOT REFERENCED ESP stage error.',
    '11': 'NOT REFERENCED from JOGGING.',
    '14': 'CONFIGURATION.',
    '1E': 'HOMING commanded from RS-232-C.',
    '1F': 'HOMING commanded by SMC-RC.',
    '28': 'MOVING.',
    '32': 'READY from HOMING.',
    '33': 'READY from MOVING.',
    '34': 'READY from DISABLE.',
    '35': 'READY from JOGGING.',
    '3C': 'DISABLE from READY.',
    '3D': 'DISABLE from MOVING.',
    '3E': 'DISABLE from JOGGING.',
    '46': 'JOGGING from READY.',
    '47': 'JOGGING from DISABLE.',
                    }


class SMC100(MessageBasedDriver, MotionControllerMultiAxis):
    """ Newport SMC100 motion controller. It assumes all axes to have units mm


    Example:
    import numpy as np
    import lantz
    import visa
    import lantz.drivers.pi.piezo as pi
    from lantz.drivers.newport_motion import SMC100
    from pyvisa import constants
    rm = visa.ResourceManager('@py')
    lantz.messagebased._resource_manager = rm
    ureg = lantz.ureg
    try:
        lantzlog
    except NameError:
        lantzlog = lantz.log.log_to_screen(level=lantz.log.DEBUG)
        lantz.log.log_to_socket(level=lantz.log.DEBUG)
        
    import time
    import numpy as np
    import warnings
    #warnings.filterwarnings(action='ignore')
    print(lantz.messagebased._resource_manager.list_resources())
    stage = SMC100('ASRL/dev/ttyUSB0::INSTR')
    stage.initialize()
    axis0 = stage.axes[0]
    print('Axis id:' + axis0.idn)
    print('Axis position: {}'.format(axis0.position))
    axis0.keypad_disable()
    axis0.position += 0.1 * ureg.mm
    print('Errors: {}'.format(axis0.get_errors()))
    stage.finalize()
    """

    DEFAULTS = {
                'COMMON': {'write_termination': '\r\n',
                           'read_termination': '\r\n', },
                'ASRL': {
                    'timeout': 100,  # ms
                    'encoding': 'ascii',
                    'data_bits': 8,
                    'baud_rate': 57600,
                    'parity': constants.Parity.none,
                    'stop_bits': constants.StopBits.one,
                    #'flow_control': constants.VI_ASRL_FLOW_NONE,
                    'flow_control': constants.VI_ASRL_FLOW_XON_XOFF,  # constants.VI_ASRL_FLOW_NONE,
                    },
                }

    def __init__(self, *args, **kwargs):
        self.motionaxis_class = kwargs.pop('motionaxis_class', MotionAxisSMC100)
        super().__init__(*args, **kwargs)

    def initialize(self):
        super().initialize()

        # Clear read buffer
        self.clear_read_buffer()

        self.detect_axis()

    @Action()
    def clear_read_buffer(self):
        '''Read all data that was still in the read buffer and discard this'''
        try:
            while True:
                self.read()
        except pyvisa.errors.VisaIOError:
            pass  # readbuffer was empty already

    @Action()
    def detect_axis(self):
        """ Find the number of axis available.

        The detection stops as soon as an empty controller is found.
        """
        self.axes = []
        i = 0
        scan_axes = True
        while scan_axes:
            i += 1
            try:
                idn = self.query('%dID?' % i)
            except pyvisa.errors.VisaIOError:
                scan_axes = False
            else:
                if idn == '':
                    scan_axes = False
                else:
                    axis = self.motionaxis_class(self, i, idn)
                    self.axes.append(axis)

            

    
class MotionAxisSMC100(MotionAxis):
    def query(self, command, *, send_args=(None, None),
              recv_args=(None, None)):
        respons = super().query(command, send_args=send_args,
                                recv_args=recv_args)
        # check for command:
        if not respons[:3] == '{:d}{}'.format(self.num, command[:2]):
            self.log_error('Axis {}: Expected to return command {} instead of'
                           '{}'.format(self.num, command[:3], respons[:3]))
        return respons[3:]

    def write(self, command, *args, **kwargs):
        super().write(command, *args, **kwargs)
        return self.get_errors()

    @Feat(units='mm')
    def software_limit_positive(self):
        '''Make sure that software limits are tighter than hardware limits,
        else the stage will go to not reference mode'''
        return self.query('SR?')

    @software_limit_positive.setter
    def software_limit_positive(self, val):
        return self._software_limit_setter(val, limit='positive')

    @Feat(units='mm')
    def software_limit_negative(self):
        return self.query('SL?')

    @software_limit_negative.setter
    def software_limit_negative(self, val):
        return self._software_limit_setter(val, limit='negative')

    def _software_limit_setter(self, val, limit='positive'):
        self.enter_config_state()
        if limit == 'positive':
            ret = self.write('SR{}'.format(val))
        elif limit == 'negative':
            ret = self.write('SL{}'.format(val))
        else:
            self.log_error("Limit {} not in ('postive', 'negative')."
                           "".format(limit))
        self.leave_and_save_config_state()
        return ret

    @Action()
    def enter_config_state(self):
        return self.write('PW1')

    @Action()
    def leave_and_save_config_state(self):
        '''Takes up to 10s, controller is unresposive in that time'''
        super().write('PW0')
        start = time.time()
        # do-while loop
        cont = True
        while cont:
            try:
                self.status
            except ValueError:
                if (time.time() - start > 10):
                    self.log_error('Controller was going to CONFIGURATION '
                                   'state but it took more than 10s. Trying '
                                   'to continue anyway')
                    cont = False
                else:
                    time.sleep(0.001)
            else:
                cont = False

    @Action()
    def on(self):
        """Put axis on"""
        pass
        self.write('MM1')

    @Action()
    def off(self):
        """Put axis off"""
        pass
        self.write('MM0')

    @Action()
    def get_errors(self):
        ret = self.query('TE?')
        err = ERRORS.get(ret, 'Error {}. Lookup in manual: https://www.newpor'
                         't.com/medias/sys_master/images/images/h11/he1/91171'
                         '82525470/SMC100CC-SMC100PP-User-s-Manual.pdf'
                         ''.format(ret))
        if err:
            self.log_error('Axis {} error: {}'.format(self.num, err))
        return err

    @Feat()
    def status(self):
        '''Read and parse controller and axis status. This gives usefull error
        messages'''
        res = self.query('TS?')
        positioner_error = [val for key, val in positioner_errors.items() if
                            int(res[:4], base=16) & key == key]
        controller_state = controller_states[res[-2:]]
        return positioner_error, controller_state

    @Feat(values={True: '1', False: '0'})
    def is_on(self):
        """
        :return: True is axis on, else false
        """
        return '1'
        # return self.query('MM?')

    @Action()
    def home(self):
        super().home()
        self._wait_until_done()

    def _wait_until_done(self):
        er, st = self.status
        if st == 'MOVING.':
            time.sleep(self.wait_time)
            return self._wait_until_done()
        elif st[:5] == 'READY':
            return True
        else:
            self.log_error('Not reached position. Controller state: {} '
                           'Positioner errors: {}'
                           ''.format(st, ','.join(er)))
            return False

    @Feat()
    def motion_done(self):
        if self.status[1][:5] == 'READY':
            return True
        return False

    @Action()
    def keypad_disable(self):
        return self.write('JD')


if __name__ == '__main__':
    import argparse
    import lantz.log

    parser = argparse.ArgumentParser(description='Test SMC100 driver')
    parser.add_argument('-p', '--port', type=str, default='1',
                        help='Serial port to connect to')

    args = parser.parse_args()
    lantzlog = lantz.log.log_to_screen(level=lantz.log.INFO)
    lantz.log.log_to_socket(lantz.log.DEBUG)

    import lantz
    import visa
    import lantz.drivers.newport_motion
    sm = lantz.drivers.newport_motion.SMC100
    rm = visa.ResourceManager('@py')
    lantz.messagebased._resource_manager = rm

    print(lantz.messagebased._resource_manager.list_resources())

    with sm(args.port) as inst:
    #with sm.via_serial(port=args.port) as inst:
        inst.idn
        # inst.initialize() # Initialize the communication with the power meter
        # Find the status of all axes:
        #for axis in inst.axes:
        #    print('Axis {} Position {} is_on {} max_velocity {} velocity {}'.format(axis.num, axis.position,
        #                                                                            axis.is_on, axis.max_velocity,
        #                                                                            axis.velocity))
