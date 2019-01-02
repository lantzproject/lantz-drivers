# some stuff
"""

    lantz.drivers.agilent.AG33522a
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Implementation of 33522a AWG with 2 channels

    The ascii commands: https://ecee.colorado.edu/~mathys/ecen1400/pdf/references/Agilent33500_FunctionGenerator.pdf

    Author: Berk Diler
    
    Date: 8/16/2017
    
"""


import numpy as np
import lantz
from lantz import Action, Feat, DictFeat, ureg
from collections import OrderedDict
from lantz.messagebased import MessageBasedDriver

class AG33522A(MessageBasedDriver):
    
    DEFAULTS = {
        'COMMON': {
            'write_termination': '\n',
            'read_termination': '\n',
        }
    }

    CHANNELS = OrderedDict([(1, 1),
                           (2,2)])

    TOGGLE = OrderedDict([("ON", 1),
                          ("OFF", 0)])

    WAVEFORMS = OrderedDict([('sine', "SIN"),
                             ('square', "SQU"),
                             ('triangle', "TRI"),
                             ('ramp', "RAMP"),
                             ('pulse', 'PULS'),
                             ('ps random noise', "PRBS"),
                             ('noise', 'NOIS'),
                             ('arbitrary', 'ARB'),
                             ('dc', "DC")])
    
    @Feat(read_once=True)
    def idn(self):
        return self.query('*IDN?')

    @Action()
    def reset(self):
        self.write("*RST")

    @Feat()
    def error(self):
        answ = self.query("SYST:ERR?")
        if answ != '+0,"No error"':
            return answ
        else:
            return

    @DictFeat(keys = CHANNELS, units="Hz", limits=(1e-6, 20e6))
    def frequency(self,channel):
        """
        Frequency of the channel
        """
        return float(self.query('SOUR{}:FREQ?'.format(channel)))

    @frequency.setter
    def frequency(self,channel,value):
        self.write('SOUR{}:FREQ {:1.6f}'.format(channel,value))

    @DictFeat(keys = CHANNELS, values = TOGGLE)
    def output(self,channel):
        """
        Output of the channel
        """
        return float(self.query('OUTP{}?'.format(channel)))

    @output.setter
    def output(self,channel,val):
        self.write('OUTP{} {}'.format(channel,val))

    @DictFeat(keys = CHANNELS, units = "V", limits=(-10., 10.))
    def voltage(self,channel):
        """
        Output voltage of the channel
        """
        return float(self.query("SOUR{}:VOLT?".format(channel)))

    @voltage.setter
    def voltage(self,channel,value):
        self.write("SOUR{}:VOLT {:1.6f}".format(channel,value))

    @DictFeat(keys=CHANNELS, units="V", limits=(-10., 10.))
    def offset(self, channel):
        """
        Output voltage of the channel
        """
        return float(self.query("SOUR{}:VOLT:OFFS?".format(channel)))

    @offset.setter
    def offset(self, channel, value):
        self.write("SOUR{}:VOLT:OFFS {:1.6f}".format(channel, value))

    @DictFeat(keys=CHANNELS, units="V", limits=(-10.,10.))
    def lower_limit(self,channel):
        """
        Lower voltage limit of the channel
        """
        return float(self.query("SOUR{}:VOLT:LIM:LOW?".format(channel)))

    @lower_limit.setter
    def lower_limit(self,channel,value):
        self.write("SOUR{}:VOLT:LIM:LOW {:1.6f}".format(channel, value))

    @DictFeat(keys=CHANNELS, units="V", limits=(-10.,10.))
    def high_limit(self,channel):
        """
        High voltage limit of the channel
        """
        return float(self.query("SOUR{}:VOLT:LIM:HIGH?".format(channel)))

    @high_limit.setter
    def high_limit(self,channel,value):
        self.write("SOUR{}:VOLT:LIM:HIGH {:1.6f}".format(channel, value))

    @DictFeat(keys = CHANNELS, values=TOGGLE)
    def limit(self,channel):
        """
        limit of the channel
        """
        return float(self.query('SOUR{}:VOLT:LIM:STAT?'.format(channel)))

    @limit.setter
    def limit(self,channel, value):
        self.write('SOUR{}:VOLT:LIM:STAT {}'.format(channel,value))

    @DictFeat(keys=CHANNELS, values=WAVEFORMS)
    def function(self,channel):
        """
        Function of the channel
        """
        return self.query('SOUR{}:FUNC?'.format(channel))

    @function.setter
    def function(self,channel,value):
        self.write('SOUR{}:FUNC {}'.format(channel, value))