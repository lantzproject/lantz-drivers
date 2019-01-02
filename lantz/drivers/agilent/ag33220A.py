from lantz.messagebased import MessageBasedDriver
from lantz import Feat, DictFeat, Action

#from lantz import Q_

import socket
import warnings

class Ag33220A(MessageBasedDriver):
    """
    Lantz driver for interfacing with Aiglent 33220A function generator.

    Includes testing code, which should work out of the box assuming you give
    it the correct IP address.

    Author: P. Mintun
    Date: 10/21/2016
    Version: 0.1
    """

    DEFAULTS = {
        'COMMON': {
            'write_termination': '\n',
            'read_termination': '\n',
        }
    }

    function_dict = {
        'sine': 'SIN',
        'square': 'SQU',
        'ramp': 'RAMP',
        'pulse': 'PULS',
        'noise': 'NOIS',
        'DC': 'DC',
        'user': 'USER'
    }

    @Feat()
    def idn(self):
        """
        Identifiies the instrument.
        """
        return self.query('*IDN?')

    @Feat(values=function_dict)
    def function(self):
        """
        Returns the selected output function.
        """
        return self.query('FUNC?')

    @function.setter
    def function(self, func_type):
        """
        Sets the output function.
        """
        return self.write('FUNC {}'.format(func_type))

    @Feat()
    def frequency(self):
        """
        Queries the output frequency of the function generator.
        """
        return float(self.query('FREQ?'))

    @frequency.setter
    def frequency(self, Hz):
        """
        Sets the output frequency of the function generator (in Hz).
        """
        return self.write('FREQ {}'.format(Hz))

    @Feat(values={'on': 1, 'off': 0})
    def output_toggle(self):
         """
         Returns whether or not the output is on or off.
         """
         return int(self.query('OUTP?'))

    @output_toggle.setter
    def output_toggle(self, on_off):
        """
        Sets the output to be either on, or off.
        """
        return self.write('OUTP {}'.format(on_off))

    @Feat(limits=(0.01,10))
    def voltage(self):
        """
        Returns the amplitude voltage setting.
        """
        return float(self.query('VOLT?'))

    @voltage.setter
    def voltage(self, volts):
        """
        Sets the amplitude voltage setting to volts.
        """
        return self.write('VOLT {}'.format(volts))

    @Feat()
    def voltage_offset(self):
        """
        Returns the DC offset voltage, in volts.
        """
        return float(self.query('VOLT:OFFS?'))

    @voltage_offset.setter
    def voltage_offset(self, V_dc):
        """
        Sets the DC offset voltage to be V_dc, in volts.
        """
        return self.write('VOLT:OFFS {}'.format(V_dc))

    # special commands for pulse mode
    @Feat()
    def pulse_width(self):
        """
        Returns the pulse width in nanoseconds.
        """
        return float(self.query('FUNC:PULS:WIDT?'))

    @pulse_width.setter
    def pulse_width(self, sec):
        """
        Sets the pulse width in seconds.
        """
        return self.write('FUNC:PULS:WIDT {}'.format(sec))

    # special functions for square waves
    @Feat()
    def square_duty_cycle(self):
        """
        Returns the duty cycle of a square wave output, in percent.
        """
        return float(self.query('FUNC:SQU:DCYC?'))

    @square_duty_cycle.setter
    def square_duty_cycle(self, duty_cycle):
        """
        Sets the square wave duty cycle to be duty_cycle.
        """
        return self.write('FUNC:SQU:DCYC {}'.format(duty_cycle))


if __name__ == '__main__':
    address = 'xxx.yyy.zzz.aaa'
    inst_num = 'instYY'

    print('Need to set IP address and inst_num!')

    with Ag33220A('TCPIP0::{}::{}::INSTR'.format(address, inst_num)) as inst:
        print('Identification: {}'.format(inst.idn))

        print('Function: {}'.format(inst.function))
        inst.function = 'sine'
        print('Function: {}'.format(inst.function))
        inst.function = 'pulse'
        print('Function: {}'.format(inst.function))
        inst.function = 'square'
        print('Function: {}'.format(inst.function))


        print('Frequency:{}Hz'.format(inst.frequency))
        inst.frequency = 1000.0
        print('Frequency:{}Hz'.format(inst.frequency))
        inst.frequency = 20000.0
        print('Frequency:{}Hz'.format(inst.frequency))


        print('Output:{}'.format(inst.output_toggle))
        inst.output_toggle = 'off'
        print('Output:{}'.format(inst.output_toggle))
        inst.output_toggle = 'on'
        print('Output:{}'.format(inst.output_toggle))

        print('Amplitude voltage:{}V'.format(inst.voltage))
        inst.voltage = 2.5
        print('Amplitude voltage:{}V'.format(inst.voltage))
        inst.voltage = 5.0
        print('Amplitude voltage:{}V'.format(inst.voltage))

        print('Offset voltage:{}'.format(inst.voltage_offset))
        inst.voltage_offset = 2.1
        print('Offset voltage:{}'.format(inst.voltage_offset))
        inst.voltage_offset = 2.5
        print('Offset voltage:{}'.format(inst.voltage_offset))

        inst.function = 'pulse'
        print('Pulse width:{}s'.format(inst.pulse_width))
        inst.pulse_width = 50e-9
        print('Pulse width:{}s'.format(inst.pulse_width))
        inst.pulse_width = 20e-9
        print('Pulse width:{}s'.format(inst.pulse_width))

        inst.function = 'square'
        print('Duty cycle:{}'.format(inst.square_duty_cycle))
        inst.square_duty_cycle = 25.0
        print('Duty cycle:{}'.format(inst.square_duty_cycle))
        inst.square_duty_cycle = 50.0
        print('Duty cycle:{}'.format(inst.square_duty_cycle))
