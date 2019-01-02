# -*- coding: utf-8 -*-

from lantz.messagebased import MessageBasedDriver
from lantz import Feat

class PM100D(MessageBasedDriver):

    DEFAULTS = {
        'COMMON': {
            'read_termination': '\n',
            'write_termination': '\n',
        },
    }

    @Feat(read_once=True)
    def idn(self):
        return self.query('*IDN?')

    @Feat(units='W')
    def power(self):
        return float(self.query('MEAS:POWER?'))

    @Feat(units='nm')
    def correction_wavelength(self):
        return float(self.query('SENSE:CORRECTION:WAVELENGTH?'))

    @correction_wavelength.setter
    def correction_wavelength(self, wavelength):
        self.write('SENSE:CORRECTION:WAVELENGTH {}'.format(wavelength))

    @Feat()
    def correction_wavelength_range(self):
        cmd = 'SENSE:CORRECTION:WAVELENGTH? {}'
        cmd_vals = ['MIN', 'MAX']
        return tuple(float(self.query(cmd.format(cmd_val))) for cmd_val in cmd_vals)
