"""
    lantz.drivers.keithley.smu2400
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of the 2400 series Source Meter Unit

    Author: Alexandre Bourassa
    Date: 09/08/2016
"""


from lantz import Action, Feat, DictFeat, ureg
from lantz.messagebased import MessageBasedDriver
import time as _t

class QOSIM900(MessageBasedDriver):

        DEFAULTS = {
            'COMMON': {
                'write_termination': '\n',
                'read_termination': '\n',
            }
        }

        AMP_CHS = {0:3, 1:4, 2:5, 3:6, 4:7, 5:8}
        SIM922_ch = 1

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._buffered_adc_gain = None


        def write_to_card(self, channel, cmd):
            s = "SNDT {}, '{}'".format(channel, cmd)
            return self.write(s)

        def read_to_card(self, channel):
            n = int(self.query('NINP? {}'.format(channel)))
            ans = self.query("RAWN? {}, {}".format(channel, n))
            return ans.strip()

        def query_to_card(self, channel, cmd, delay=0.1):
            self.write_to_card(channel, cmd)
            _t.sleep(delay)
            return self.read_to_card(channel)

        @DictFeat(units='K', keys=[1,2])
        def temperature(self, ch):
            return float(self.query_to_card(self.SIM922_ch, 'TVAL? {}'.format(ch), delay=0.5))

        @DictFeat(keys=list(AMP_CHS.keys()), limits=(0, 25e-6, 25e-6/65535), units='A')
        def bias_current(self, key):
            return float(25e-6*int(self.query_to_card(self.AMP_CHS[key], '+B?'))/65535)*ureg.A

        @bias_current.setter
        def bias_current(self, key, val):
            return self.write_to_card(self.AMP_CHS[key], '+B{};'.format(int(65535*val/25e-6)))

        @DictFeat(keys=list(AMP_CHS.keys()),limits=(0,2.55,0.01), units='s')
        def reset_event_duration(self, key):
            return (int(self.query_to_card(self.AMP_CHS[key], '+D?'))/100.0)*ureg.s

        @reset_event_duration.setter
        def reset_event_duration(self, key, val):
            return self.write_to_card(self.AMP_CHS[key], '+D{};'.format(int(100*val)))

        @DictFeat(keys=list(AMP_CHS.keys()), values={True: '1', False: '0'})
        def autoreset_enable(self, key):
            return self.query_to_card(self.AMP_CHS[key], '+E?')

        @autoreset_enable.setter
        def autoreset_enable(self, key, val):
            return self.write_to_card(self.AMP_CHS[key], '+E{};'.format(val))

        @Action()
        def reset_bias(self, key):
            if not key in list(self.AMP_CHS.keys()): raise Exception('Specified <key> not in channel list.  Please check AMP_CH')
            return self.write_to_card(self.AMP_CHS[key], '+F;')

        @Action()
        def autobias(self, key):
            if not key in list(self.AMP_CHS.keys()): raise Exception('Specified <key> not in channel list.  Please check AMP_CH')
            return self.write_to_card(self.AMP_CHS[key], '+G;')

        @Action()
        def set_adc_gain(self, key, state='low'):
            if not key in list(self.AMP_CHS.keys()): raise Exception('Specified <key> not in channel list.  Please check AMP_CH')
            if not state in ['low','high']: raise Exception("<state> can only be 'low' or 'high'")
            self._buffered_adc_gain = state
            return self.write_to_card(self.AMP_CHS[key], '+C{};'.format(int(state=='high')))

        @DictFeat(keys=list(AMP_CHS.keys()), units='V')
        def adc_voltage(self, key):
            if not self._buffered_adc_gain in ['low','high']: raise Exception('adc_gain unknown, please set using <inst>.set_adc_gain(channel, state)')
            else:
                gfactor = (5.0 if self._buffered_adc_gain=='low' else 1.1)
                return float(gfactor*int(self.query_to_card(self.AMP_CHS[key], '+C?'))/65535)*ureg.V

        @DictFeat(keys=list(AMP_CHS.keys()), limits=(0, 25e-6, 25e-6/65535), units='A')
        def mem_bias_current(self, key):
            return float(25e-6*int(self.query_to_card(self.AMP_CHS[key], '+H?'))/65535)*ureg.A

        @mem_bias_current.setter
        def mem_bias_current(self, key, val):
            """DO NOT CALL THIS FUNCTION REPEATEDLY.  THE MEMORY AS A 100,000 WRITE LIFETIME
            """
            print('WARNING: DO NOT CALL THIS FUNCTION REPEATEDLY.  THE MEMORY AS A 100,000 WRITE LIFETIME')
            return self.write_to_card(self.AMP_CHS[key], '+H{};'.format(int(65535*val/25e-6)))

        @Action()
        def set_bias_to_mem(self, key):
            if not key in list(self.AMP_CHS.keys()): raise Exception('Specified <key> not in channel list.  Please check AMP_CH')            
            return self.write_to_card(self.AMP_CHS[key], '+H;')

        @DictFeat(keys=list(AMP_CHS.keys()) ,read_once=True)
        def card_idn(self, key):
            return self.query_to_card(self.AMP_CHS[key], '+A?')

        @Feat(read_once=True)
        def idn(self):
            return self.query('*IDN?')

        @Action()
        def reset(self):
            return self.write('*RST')
