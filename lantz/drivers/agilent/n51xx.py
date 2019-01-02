from lantz.messagebased import MessageBasedDriver
from lantz import Feat, DictFeat, Action, ureg

from collections import OrderedDict

#from lantz import Q_

import socket
import warnings


class N51xx(MessageBasedDriver):
    """
    Lantz driver for interfacing with AR SG6000 vector signal generator.

    Includes testing code, which should work out of the box assuming you give
    it the correct IP address.

    Author: P. Mintun
    Date: 8/31/2016
    Version: 0.1
    """

    DEFAULTS = {
        'COMMON': {
            'write_termination': '\n',
            'read_termination': '\n',
        }
    }

    ON_OFF_VALS = OrderedDict([
                    ('on', 1),
                    ('off', 0),
    ])

    freq_limits = (1e5,6e9)
    power_limits = (-200,15)


    @Feat()
    def idn(self):
        """
        Identifiies the instrument.
        """
        return self.query('*IDN?')


    @Feat(values=ON_OFF_VALS)
    def rf_toggle(self):
        """
        Enable or disable RF output
        """
        value = int(self.query('OUTP:STAT?'))
        print(value)
        return value

    @rf_toggle.setter
    def rf_toggle(self,value):
        self.write('OUTP:STAT {}'.format(value))
        #if value != self.rf_toggle:
        #    self.write('OUTP:STAT {}'.format(value))
        return

    @Feat(units='Hz', limits=freq_limits)
    def frequency(self):
        """
        RF output frequency, in Hz.
        """
        return self.query('SOUR:FREQ:CW?')

    @frequency.setter
    def frequency(self, frequency):
        """
        RF output frequency, in Hz.
        """
        return self.write('SOUR:FREQ:CW {}Hz'.format(frequency))

    @Feat(limits=power_limits)
    def power(self):
        """
        RF output power, in dBm.
        """
        return self.query('SOUR:POW?')

    @power.setter
    def power(self, value):
        """
        Sets RF output power, in dBm.
        """
        print('Will not set power - IQ modulator in use!')
        return
        #value = 5.5 # set for using IQ modulator
        #return self.write('SOUR:POW {}DBM'.format(value))

    @Feat(units='radians',limits=(-3.14,3.14))
    def phase(self):
        """
        Returns RF signal carrier phase in radians
        """
        return self.query('SOUR:PHAS?')

    @phase.setter
    def phase(self, radians):
        """
        Sets RF signal carrier phase in degrees
        """
        return self.write('SOUR:PHAS {}RAD'.format(radians))

    @Feat(limits=(-200,30))
    def power_limit(self):
        """
        Returns the user set output limit of the signal generator, in dBm.
        """
        #print('For some reason, this command doesn\'t seem to work...')
        return self.write('SOUR:POW:USER:MAX?')

    @power_limit.setter
    def power_limit(self, max_dBm):
        """
        Sets the maximum output of the signal generator in dBm.
        """
        self.write('SOUR:POW:USER:ENAB 0')
        return self.write('SOUR:POW:USER:MAX {}'.format(max_dBm))






if __name__ == '__main__':
    address = '192.168.1.102'
    inst_num = 'inst0'

    with N51xx('TCPIP0::{}::{}::INSTR'.format(address, inst_num)) as inst:
        print('Identification: {}'.format(inst.idn))

        inst.power_limit = 0.0
        print('Power limit:{}dBm'.format(inst.power_limit))

        print('RF output settings')
        print('RF on?:{}'.format(inst.rf_toggle))
        print('Output frequency: {}'.format(inst.frequency))
        inst.frequency = 1e6
        print('Output frequency: {}'.format(inst.frequency))
        inst.frequency = 2.87e9
        print('Output frequency: {}'.format(inst.frequency))

        print('Output power: {}dBm'.format(inst.power))
        inst.power = -10.0
        print('Output power: {}dBm'.format(inst.power))
        inst.power = 0.0
        print('Output power: {}dBm'.format(inst.power))
        inst.power = -10.0
        print('Output power: {}dBm'.format(inst.power))

        print('Phase:{}'.format(inst.phase))
        inst.phase = 3.14159/2.0
        print('Phase:{}'.format(inst.phase))
        inst.phase = 0.0
        print('Phase:{}'.format(inst.phase))


        inst.rf_toggle = 1
        print('RF on?:{}'.format(inst.rf_toggle))
        inst.rf_toggle = 0
        print('RF on?:{}'.format(inst.rf_toggle))
