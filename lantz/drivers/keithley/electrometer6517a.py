"""
    lantz.drivers.keithley.electrometer6517a
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of the electrometer model 6517A

    Author: Alexandre Bourassa
    Date: 10/10/2018
"""


#from lantz import Action, Feat, DictFeat, ureg
#from lantz.messagebased import MessageBasedDriver
from lantz.core import Action, Feat, DictFeat, ureg, MessageBasedDriver
import re

class Electrometer6517A(MessageBasedDriver):

        DEFAULTS = {
            'COMMON': {
                'write_termination': '\n',
                'read_termination': '\n',
                'timeout': 10000,
            }
        }

        STATUS_DICT = {'N':'Normal', 'Z':'Zero Check Enabled', 'O':'Overflow', 'U':'Underflow', 'R':'Reference (Rel)', 'L':'Out of Limit'}

        def parse_ASCII_data(self, data):
            status = '[NZOURL]'
            units =  'VDC|ADC|OHM|OHMCM|OHMSQ|%/V|COUL'
            pattern = r'([^{}*)({})({}),(.*),(.*)'.format(status,status,units)
            m = re.search(pattern, data)
            ans = dict()
            ans['reading'] = float(m.group(1))
            ans['status'] = self.STATUS_DICT[m.group(2)]
            ans['units'] = m.group(3)
            ans['time_stamp'] = m.group(4)
            ans['read_no'] = m.group(5)
            return ans

        @Feat(read_once=True)
        def idn(self):
            return self.query('*IDN?')

        @Feat(units='V')
        def voltage(self):
            return float(self.query(':SENSe:RESistance:MANual:VSOurce:AMPLitude?'))

        @voltage.setter
        def voltage(self, val):
            return self.write(':SENSe:RESistance:MANual:VSOurce:AMPLitude {}'.format(val))

        @Feat(values={False:'0', True:'1'})
        def output(self):
            return self.query(':SENSe:RESistance:MANual:VSOurce:OPERate?')

        @output.setter
        def output(self, val):
            return self.write(':SENSe:RESistance:MANual:VSOurce:OPERate {}'.format(val))

        @Action()
        def meas_current(self):
            ans = self.parse_ASCII_data(self.query(':MEAS:CURR?'))
            return ans['reading']

        @Feat(values={False:'0', True:'1'})
        def zero_check(self):
            return self.query(':SYST:ZCH?')

        @zero_check.setter
        def zero_check(self, val):
            return self.write(':SYST:ZCH {}'.format(val))

        @Feat(units='V')
        def voltage_range(self):
            return float(self.query('SOUR:VOLT:RANG?'))

        @voltage_range.setter
        def voltage_range(self, val):
            return self.write('SOUR:VOLT:RANG {}'.format(val))

        @Feat(units='V')
        def voltage_limit(self):
            return float(self.query('SOUR:VOLT:LIM?'))

        @voltage_limit.setter
        def voltage_limit(self, val):
            return self.write('SOUR:VOLT:LIM {}'.format(val))
