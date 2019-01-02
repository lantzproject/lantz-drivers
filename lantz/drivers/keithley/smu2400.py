"""
    lantz.drivers.keithley.smu2400
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of the 2400 series Source Meter Unit

    Author: Alexandre Bourassa
    Date: 09/08/2016
"""


from lantz import Action, Feat, DictFeat, ureg
from lantz.messagebased import MessageBasedDriver

class SMU2400(MessageBasedDriver):

        DEFAULTS = {
            'COMMON': {
                'write_termination': '\n',
                'read_termination': '\n',
            }
        }

        @Feat(read_once=True)
        def idn(self):
            return self.query('*IDN?')


        @Feat(values={'current': 'CURR:DC', 'voltage': 'VOLT:DC', 'resistance':'RES'})
        def meas_config(self):
            """
            Configures the instrument to a specific setup for measurements on the specified function:
            current, voltage or resistance

            WARNING: This may reset some configurations, and this will turn on the output
            """
            return self.query(':CONF?').strip('"').split('"')[-1]

        @meas_config.setter
        def meas_config(self, value):
            self.write(':CONF:{}'.format(value))


        @Feat(values={False:'0', True:'1'})
        def output(self):
            return self.query(':OUTP:STAT?')

        @output.setter
        def output(self, value):
            return self.write(':OUTP:STAT {}'.format(value))


        @Feat(units='A', limits=(-1.05, 1.05,))
        def current_compliance(self):
            return self.query(':CURR:PROT?')

        @current_compliance.setter
        def current_compliance(self, value):
            return self.write(':CURR:PROT {}'.format(value))


        @Feat(units='V', limits=(-210., 210.,))
        def voltage_compliance(self):
            return self.query(':VOLT:PROT?')

        @voltage_compliance.setter
        def voltage_compliance(self, value):
            return self.write(':VOLT:PROT {}'.format(value))


        @Feat(units='V', limits=(-210., 210.,))
        def sense_voltage_range(self):
            return self.query(':SENS:VOLT:RANG?')

        @sense_voltage_range.setter
        def sense_voltage_range(self, value):
            return self.write(':SENS:VOLT:RANG {}'.format(value))


        @Feat(units='A', limits=(-1.05, 1.05,))
        def sense_current_range(self):
            return self.query(':SENS:CURR:RANG?')

        @sense_current_range.setter
        def sense_current_range(self, value):
            return self.write(':SENS:CURR:RANG {}'.format(value))


        @Feat(units='V', limits=(-210., 210.,))
        def source_voltage_range(self):
            return self.query(':SOUR:VOLT:RANG?')

        @source_voltage_range.setter
        def source_voltage_range(self, value):
            return self.write(':SOUR:VOLT:RANG {}'.format(value))


        @Feat(units='A', limits=(-1.05, 1.05,))
        def source_current_range(self):
            return self.query(':SOUR:CURR:RANG?')

        @source_current_range.setter
        def source_current_range(self, value):
            return self.write(':SOUR:CURR:RANG {}'.format(value))


        @Feat(units='A', limits=(-1.05, 1.05,))
        def source_current(self):
            return self.query(':SOUR:CURR?')

        @source_current.setter
        def source_current(self, value):
            return self.write(':SOUR:CURR {}'.format(value))


        @Feat(units='V', limits=(-210., 210.,))
        def source_voltage(self):
            return self.query(':SOUR:VOLT?')

        @source_voltage.setter
        def source_voltage(self, value):
            return self.write(':SOUR:VOLT {}'.format(value))


        @Feat(values={'current':'CURR', 'voltage':'VOLT', 'memory':'MEM'})
        def source_function(self):
            return self.query(':SOUR:FUNC?')

        @source_function.setter
        def source_function(self, value):
            return self.write(':SOUR:FUNC {}'.format(value))


        SENSE_FUNCTION = {'current':'CURR:DC', 'voltage':'VOLT:DC', 'resistance':'RES'}
        @DictFeat(values={'ON':'1', 'OFF':'0'}, keys=SENSE_FUNCTION)
        def sense_function(self, key):
            return self.query(':FUNC:STAT? "{}"'.format(key))

        @sense_function.setter
        def sense_function(self, key, value):
            value = 'OFF' if value=='0' else 'ON'
            return self.write(':SENS:FUNC:{} "{}"'.format(value, key))


        @Feat(values={'OFF': '0', 'ON': '1'})
        def sense_concurent(self):
            return self.query(':FUNC:CONC?')

        @sense_concurent.setter
        def sense_concurent(self, value):
            return self.write(':FUNC:CONC {}'.format(value))



        @Action()
        def reset(self):
            return self.write('*RST')

        @Action()
        def get_data(self):
            """
            Perform a read operation that returns a dictionary
            """
            ans = list(map(float, self.query(':READ?').split(',')))
            return {'voltage': ans[0], 'current': ans[1], 'resistance': ans[2], 'time': ans[3], 'status': ans[4]}
