"""

    lantz.drivers.rigol.dg1022
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of Rigol DG1022 function generator with 2 channels. More or
    less based around on the Ag33522a driver from Berk Diler.

    Manual available from: https://www.rigolna.com/products/waveform-generators/dg1000/

    Author: Peter Mintun

    Date: 12/11/2017

"""


import numpy as np
import lantz
from lantz import Action, Feat, DictFeat, ureg
from collections import OrderedDict
from lantz.messagebased import MessageBasedDriver

class DG1022(MessageBasedDriver):

    DEFAULTS = {
        'COMMON': {
            'write_termination': '\n',
            'read_termination': '\n',
        }
    }

    CHANNELS = OrderedDict([(1, 1),
                           (2,2)])

    TOGGLE = OrderedDict([('on', 'ON'),
                          ('off', 'OFF')])

    WAVEFORMS = OrderedDict([('arbitrary', 'ARB'),
                             ('dc', 'DC'),
                             ('harmonic', 'HARM'),
                             ('noise', 'NOIS'),
                             ('pulse', 'PULS'),
                             ('ramp', 'RAMP'),
                             ('sine', 'SIN'),
                             ('square', 'SQU'),
                             ('triangle', 'TRI'),
                             ('user', 'USER')])

    @Feat(read_once=True)
    def idn(self):
        return self.query('*IDN?')

    @Action()
    def reset(self):
        return self.write('*RST')

    @Feat()
    def error(self):
        msg = self.query("SYST:ERR?")
        return msg.split(',') #error code, error message

    @DictFeat(keys = CHANNELS, units="Hz", limits=(1e-6, 25e6))
    def frequency(self,channel):
        """
        Returns the frequency of the specified channel, in Hertz.
        """
        return float(self.query('SOUR{}:FREQ?'.format(channel)))

    @frequency.setter
    def frequency(self,channel,value):
        """
        Sets the frequency of the specified channel, to value. Note that this
        is not smart enough to keep track of the different bandwidth constraints
        on different types of waveforms, so see the manual accordingly.
        """
        return self.write('SOUR{}:FREQ {:1.6f}'.format(channel,value))

    @DictFeat(keys=CHANNELS, values=WAVEFORMS)
    def function(self,channel):
        """
        Returns the function of the specified channel from the options
        enumerated in WAVEFORMS.
        """
        result = self.query('SOUR{}:APPL?'.format(channel))[1:-1]
        return result.split(',')[0]

    @function.setter
    def function(self,channel,value):
        """
        Returns the function of the specified channel to value (specified in
        WAVEFORMS).
        """
        return self.write('SOUR{}:APPL:{}'.format(channel, value))

    @DictFeat(keys = CHANNELS, values = TOGGLE)
    def output(self,channel):
        """
        Reads the output state of the specified channel.
        """
        return self.query('OUTP{}?'.format(channel))

    @output.setter
    def output(self,channel,val):
        """
        Sets the output state of the specified channel to val.
        """
        return self.write('OUTP{} {}'.format(channel,val))

    @DictFeat(keys=CHANNELS, units="V", limits=(-10.,10.))
    def voltage_low(self,channel):
        """
        Queries the low voltage level for the specified channel.
        """
        return float(self.query("SOUR{}:VOLT:LOW?".format(channel)))

    @voltage_low.setter
    def voltage_low(self,channel,value):
        """
        Sets the high voltage level for the specified channel.
        """
        return self.write("SOUR{}:VOLT:LOW {:1.6f}".format(channel, value))

    @DictFeat(keys=CHANNELS, units="V", limits=(-10.,10.))
    def voltage_high(self,channel):
        """
        Queries the high voltage level for the specified channel.
        """
        return float(self.query("SOUR{}:VOLT:HIGH?".format(channel)))

    @voltage_high.setter
    def voltage_high(self,channel,value):
        """
        Sets the high voltage level for the specified channel.
        """
        return self.write("SOUR{}:VOLT:HIGH {:1.6f}".format(channel, value))

    @DictFeat(keys = CHANNELS, units = "V", limits=(0., 20.))
    def voltage_amplitude(self,channel):
        """
        Queries the peak-to-peak voltage amplitude of the specified output
        channel.
        """
        return float(self.query("SOUR{}:VOLT?".format(channel)))

    @voltage_amplitude.setter
    def voltage_amplitude(self,channel,value):
        """
        Sets the peak-to-peak voltage amplitude of the specified output channel.
        """
        return self.write("SOUR{}:VOLT {:1.6f}".format(channel,value))

    @DictFeat(keys=CHANNELS, units="V", limits=(-10., 10.))
    def voltage_offset(self, channel):
        """
        Queries the offset voltage of the specified output channel.
        """
        return float(self.query("SOUR{}:VOLT:OFFS?".format(channel)))

    @voltage_offset.setter
    def voltage_offset(self, channel, value):
        """
        Sets the offset voltage of the specified output channel.
        """
        self.write("SOUR{}:VOLT:OFFS {:1.6f}".format(channel, value))


if __name__ == '__main__':


    # note: if you don't see your device, it may not work over USB 3.0?
    addr = 'USB0::0x1AB1::0x0642::DG1ZA192902819::INSTR'

    try:
        inst = DG1022(addr)
        inst.initialize()

        inst.reset()

        print('Identification:{}'.format(inst.idn))
        print('Error:{}'.format(inst.error))


    except:

        print('Could not find instrument, check connection/address!')

    # code to check various parameters from supported channels
    for channel in inst.CHANNELS.keys():

        inst.frequency[channel] = 1e-6
        print('Channel {} frequency: {}'.format(channel, inst.frequency[channel]))
        inst.frequency[channel] = 20e6
        print('Channel {} frequency: {}'.format(channel, inst.frequency[channel]))

        print('Channel {} function: {}'.format(channel, inst.function[channel]))
        inst.function[channel] = 'square'
        print('Channel {} function: {}'.format(channel, inst.function[channel]))

        inst.output[channel] = 'off'
        print('Channel {} output:{}'.format(channel, inst.output[channel]))
        inst.output[channel] = 'on'
        print('Channel {} output:{}'.format(channel, inst.output[channel]))
        inst.output[channel] = 'off'
        print('Channel {} output:{}'.format(channel, inst.output[channel]))

        print('Channel {} low voltage:{}'.format(channel, inst.voltage_low[channel]))
        inst.voltage_low[channel] = -1.0
        print('Channel {} low voltage:{}'.format(channel, inst.voltage_low[channel]))

        print('Channel {} high voltage:{}'.format(channel, inst.voltage_high[channel]))
        inst.voltage_high[channel] = 1.0
        print('Channel {} high voltage:{}'.format(channel, inst.voltage_high[channel]))

        print('Channel {} voltage amplitude:{}'.format(channel, inst.voltage_amplitude[channel]))
        print('Channel {} voltage offset:{}'.format(channel, inst.voltage_offset[channel]))

        inst.voltage_amplitude[channel] = 5.0
        inst.voltage_offset[channel] = 0.0

        print('Channel {} voltage amplitude:{}'.format(channel, inst.voltage_amplitude[channel]))
        print('Channel {} voltage offset:{}'.format(channel, inst.voltage_offset[channel]))
        print('Channel {} low voltage:{}'.format(channel, inst.voltage_low[channel]))
        print('Channel {} high voltage:{}'.format(channel, inst.voltage_high[channel]))
