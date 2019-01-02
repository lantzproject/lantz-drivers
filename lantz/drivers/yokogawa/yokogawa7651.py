# -*- coding: utf-8 -*-

from lantz import Feat, Action
from lantz.messagebased import MessageBasedDriver

class Yokogawa7651(MessageBasedDriver):

    DEFAULTS = {
        'COMMON': {
            'write_termination': '\r\n',
            'read_termination': '\r\n',
        },
    }

    STATUS_KEYS = [
        'CAL switch',
        'IC memory card',
        'Calibration mode',
        'Output',
        'Output unstable',
        'Communication error',
        'Program execution',
        'Program under execution',
    ]

    @Feat()
    def status(self):
        """
        Gets status bits
        """
        value = self.query('OC')
        bits = [bool(int(v)) for v in bin(int(value[5:]))[2:].zfill(8)]
        return {k: v for k, v in zip(self.STATUS_KEYS, bits)}

    @Action()
    def trigger(self):
        """
        Executes actions queued by a trigger
        """
        self.write('E')
        return

    @Feat()
    def output_value(self):
        """
        Returns output state
        """
        value = self.query('OD')
        return float(value[4:])

    @output_value.setter
    def output_value(self, value):
        self.write('S{:e}'.format(value))
        self.trigger()
        return

    @Feat()
    def output_toggle(self):
        return self.status['Output']

    @output_toggle.setter
    def output_toggle(self, state):
        cmd = 'O1' if state else 'O0'
        self.write(cmd)
        self.trigger()
        return

    @Feat()
    def stable(self):
        return not self.status['Output unstable']
