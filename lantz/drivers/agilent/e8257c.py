# some stuff
"""

    lantz.drivers.agilent.e8257c
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Implementation of E8257C signal generator
    
    Author: Thomas Kiely
    
    Date: 6/16/2016
    
"""


import numpy as np
import lantz
from lantz import Action, Feat, DictFeat, ureg
from lantz.messagebased import MessageBasedDriver

class E8257C(MessageBasedDriver):
    
    DEFAULTS = {
        'COMMON': {
            'write_termination': '\n',
            'read_termination': '\n',
        }
    }
    
    @Feat(read_once=True)
    def idn(self):
        return self.query('*IDN?')

    @Feat(units='V')
    def lf_amplitude(self):
        """
        low frequency ampitude (BNC output)
        """
        return float(self.query('LFO:AMPL?'))
    
    @lf_amplitude.setter
    def lf_amplitude(self,value):
        self.write('LFO:AMPL {:.2f}'.format(value))
        
    @Feat()
    def rf_amplitude(self):
        """
        RF amplitude (Type N output)
        units are in dBm
        """
        return float(self.query('POW:AMPL?'))
    
    @rf_amplitude.setter
    def rf_amplitude(self,value):
        self.write('POW:AMPL {:.2f}'.format(value))
    
    @Feat(values={True: 1, False: 0})
    def lf_toggle(self):
        """
        enable or disable low frequency output
        """
        return float(self.query('LFO:STAT?'))

    @lf_toggle.setter
    def lf_toggle(self,value):
        self.write('LFO:STAT {:s}'.format(value))
    
    @Feat(values={True: '1', False: '0'})
    def rf_toggle(self):
        """
        enable or disable RF output
        """
        return self.query('OUTP:STAT?')
    
    @rf_toggle.setter
    def rf_toggle(self,value):
        self.write('OUTP:STAT {:s}'.format(value))
    
    @Feat(units='Hz')
    def rf_frequency(self):
        """
        signal frequency
        units are in hertz
        """
        return float(self.query('FREQ?'))
    
    @rf_frequency.setter
    def rf_frequency(self,value):
        self.write('FREQ {:.2f}'.format(value))
    
    @Feat(units='Hz')
    def lf_frequency(self):
        """
        signal frequency 0.5Hz-1MHz
        """
        return float(self.query('LFO:FUNC:FREQ?'))
    
    @lf_frequency.setter
    def lf_frequency(self,value):
        self.write('LFO:FUNC:FREQ {:.2f}'.format(value))
    
    #ALL EXCEPT MODEL UNR
    #@Feat(values={1,2})
    #def pll_loop_filter_mode(self):
    #    """
    #    sets PLL bandwidth to optimize phase noise
    #    1 optimizes below 10kHz, 2 optimizes above 10kHz
    #    """
    #    return float(self.query('FREQ:SYNT?'))
    #
    #@pll_loop_filter_mode.setter
    #def pll_loop_filter_mode(self,value):
    #    self.write('FREQ:SYNT {}'.format(value))
    
    @Feat()
    def rf_offset(self): #not entirely sure if this is rf
        """
        RF offset
        units are dB
        """
        return float(self.query('POW:OFFS?'))
    
    @rf_offset.setter
    def rf_offset(self,value):
        self.write('POW:OFFS {:.2f}'.format(value))
    
    @Feat(units='radians')
    def phase(self):
        """
        carrier phase
        from -Pi to Pi
        """
        return float(self.query('PHAS?'))
    
    @phase.setter
    def phase(self,value):
        self.write('PHAS {:.2f}'.format(value))
    
    @Action()
    def ref_phase(self):
        """
        sets current output phase as a zero reference
        """
        self.write('PHAS:REF')

    @Feat(values={True: 1, False: 0})
    def mod_toggle(self):
        """
        Modulation State
        """
        return float(self.query('OUTP:MOD?'))
        
    @mod_toggle.setter
    def mod_toggle(self, value):
        self.write('OUTP:MOD {}'.format(value))

#   ONLY WITH OPTION 002/602    
#    @Feat()
#    def mod_type(self):
#        """
#        Modulation State
#        """
#        return self.query('RAD:CUST:MOD:TYPE?')
#
#    @mod_type.setter
#    def mod_type(self, value):
#        self.write('RAD:CUST:MOD:TYPE {}'.format(value))