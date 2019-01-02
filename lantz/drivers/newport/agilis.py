# -*- coding: utf-8 -*-
"""
    lantz.drivers.newport.agilis
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of Agilis UC8/UC2 piezo controller

    Authors: Kevin Miao, Alexandre Bourassa
    Date: 12/14/2015

"""

from lantz import Action, Feat, DictFeat
from lantz.messagebased import MessageBasedDriver

from pyvisa.constants import Parity, StopBits

import time

class Agilis(MessageBasedDriver):

    comm_delay = 0.2

    DEFAULTS = {
        'ASRL': {
            'write_termination': '\r\n',
            'read_termination': '\r\n',
            'baud_rate': 921600,
            'parity': Parity.none,
            'stop_bits': StopBits.one,
            'timeout': None,
        }
    }

    # We need a synchronous decorator (or something to slow down function calls)
    # most commands need ~1s to complete, while select commands may need up to
    # 2 minutes
    def write(self, *args, **kwargs):
        super(Agilis, self).write(*args, **kwargs)
        time.sleep(self.comm_delay)
        return

    @Action()
    def reset(self):
        """
        Reset controller
        """
        self.write('RS')
        return

    #@Feat(values={1, 2, 3, 4})
    @Feat()
    def channel(self):
        retval = self.query('CC?')
        return int(retval.lstrip('CC'))

    @channel.setter
    def channel(self, value):
        """
        Set channel
        """
        self.write('CC{}'.format(value))

    @Feat()
    def delay(self, axis):
        return self.query('{}DL?'.format(axis))

    @delay.setter
    def delay(self, axis, value):
        self.write('{}DL{}'.format(axis, value))

    @Feat()
    def jog(self, axis):
        return self.query('{}JA?'.format(axis))

    @Action()
    def jog(self, axis, value):
        self.write('{}JA{}'.format(axis, value))

    @Action()
    def measure_position(self, axis):
        return self.query('{}MA'.format(axis))

    @Action()
    def move_to_limit(self, axis, value):
        self.write('{}MV{}'.format(axis, value))

    @Action()
    def move_to_limit(self, axis, value):
        while not self.limit_status[axis]:
            self.jog(axis, value)
        self.jog(axis, 0)

    @Action()
    def relative_move(self, axis, steps):
        self.write('{}PR{}'.format(axis, steps))

    @DictFeat()
    def step_amplitude(self, axis):
        val1 = self.query('{}SU-?'.format(axis))
        val2 = self.query('{}SU+?'.format(axis))
        stripped = '{}SU'.format(axis)
        return (val1.lstrip(stripped), val2.lstrip(stripped))


    @step_amplitude.setter
    def step_amplitude(self, axis, amplitude):
        if amplitude < 0:
            sign = '-'
        elif amplitude > 0:
            sign = '+'
        else:
            raise ValueError('amplitude cannot be 0')
        self.write('{}SU{}{:d}'.format(axis, sign, abs(amplitude)))

    @Action()
    def move(self, axis, value, mode):
        raise NotImplementedError

    @Feat()
    def limit_status(self):
        """
        PH0 if neither limit reached
        PH1 if only axis 1
        PH2 if only axis 2
        PH3 if both
        """
        retval = self.query('PH')
        self.log_debug(retval)
        code = int(retval.lstrip('PH'))
        status = {1: False, 2: False}
        status[1] = True if code & 1 else False
        status[2] = True if (code >> 1) & 1 else False
        return status

    @DictFeat()
    def status(self, axis):
        return self.query('{}TS'.format(axis))

    @Action()
    def stop(self, axis):
        self.write('{}ST'.format(axis))

    @Action()
    def zero(self, axis):
        self.write('{}ZP'.format(axis))

    @DictFeat()
    def steps(self, axis):
        retval = self.query('{}TP?'.format(axis))
        return int(retval.lstrip('{}TP'.format(axis)))

    @Feat()
    def version(self):
        return self.query('VE').strip()

    @Action()
    def calibrate(self, axis):
        self.zero(axis)
        self.step_amplitude[axis] = 50
        if self.limit_status[axis]:
            self.relative_move(axis, 100)
        if self.limit_status[axis]:
            self.relative_move(axis, -100)
        self.move_to_limit(axis, -3)
        self.step_amplitude[axis] = 50
        self.zero(axis)
        self.relative_move(axis, 100)
        self.move_to_limit(axis, 3)
        return self.steps[axis]

def main():
    import logging
    import sys
    from lantz.log import log_to_screen
    log_to_screen(logging.CRITICAL)
    res_name = sys.argv[1]
    fmt_str = "{:<20}|{:>20}"
    axis = 1
    with Agilis(res_name) as inst:
        inst.channel = 1
        print(fmt_str.format("Device version", inst.version))
        print(fmt_str.format("Current channel", inst.channel))
        amplitudes = inst.step_amplitude[axis]
        print(fmt_str.format("- Step amplitude", amplitudes[0]))
        print(fmt_str.format("+ Step amplitude", amplitudes[1]))
        print(inst.calibrate(1))
        print(inst.calibrate(2))
        inst.channel = 2
        print(inst.calibrate(1))
        print(inst.calibrate(2))

if __name__ == '__main__':
    main()
