# -*- coding: utf-8 -*-
"""
    lantz.drivers.stanford.sg396
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of SG396 signal generator

    Author: Kevin Miao & Berk Diler
    Date: 12/15/2015 & 8/21/17
"""

import numpy as np
from lantz import Action, Feat, DictFeat, ureg
from lantz.messagebased import MessageBasedDriver
from collections import OrderedDict

class SG396(MessageBasedDriver):

        DEFAULTS = {
            'COMMON': {
                'write_termination': '\r\n',
                'read_termination': '\r\n',
            }
        }

        MODULATION_TYPE = OrderedDict([
            ('AM', 0),
            ('FM', 1),
            ('Phase',2),
            ('Sweep',3),
            ('Pulse',4),
            ('Blank',5),
            ('QAM',7),
            ('CPM',8),
            ('VSB',9)
        ])

        MODULATION_FUNCTION = OrderedDict([
            ('sine', 0),
            ('ramp', 1),
            ('triangle', 2),
            ('square', 3),
            ('noise', 4),
            ('external', 5)
        ])

        # Signal synthesis commands

        @Feat
        def lf_amplitude(self):
            """
            low frequency amplitude (BNC output)
            """
            return float(self.query('AMPL?'))

        @lf_amplitude.setter
        def lf_amplitude(self, value):
            self.write('AMPL{:.2f}'.format(value))

        @Feat
        def rf_amplitude(self):
            """
            RF amplitude (Type N output)
            """
            return float(self.query('AMPR?'))

        @rf_amplitude.setter
        def rf_amplitude(self, value):
            self.write('AMPR{:.2f}'.format(value))

        @Feat(values={True: '1', False: '0'})
        def lf_toggle(self):
            """
            low frequency output state
            """
            return self.query('ENBL?')

        @lf_toggle.setter
        def lf_toggle(self, value):
            self.write('ENBL{:s}'.format(value))

        @Feat(values={True: '1', False: '0'})
        def rf_toggle(self):
            """
            RF output state
            """
            return self.query('ENBR?')

        @rf_toggle.setter
        def rf_toggle(self, value):
            self.write('ENBR{:s}'.format(value))

        @Feat(units='Hz')
        def frequency(self):
            """
            signal frequency
            """
            return self.query('FREQ?')

        @frequency.setter
        def frequency(self, value):
            self.write('FREQ{:.2f}'.format(value))

        @Feat()
        def lf_offset(self):
            """
            low frequency offset voltage
            """
            return self.query('OFSL?')

        @lf_offset.setter
        def lf_offset(self, value):
            self.write('OFSL{:.2f}'.format(value))

        @Feat(units='degrees')
        def phase(self):
            """
            carrier phase
            """
            return self.query('PHAS?')

        @phase.setter
        def phase(self, value):
            self.write('PHAS{:.2f}'.format(value))

        @Action()
        def rel_phase(self):
            """
            sets carrier phase to 0 degrees
            """
            self.write('RPHS')

        @Feat(values={True: 1, False: 0})
        def mod_toggle(self):
            """
            Modulation State
            """
            return int(self.query('MODL?'))

        @mod_toggle.setter
        def mod_toggle(self, value):
            self.write('MODL {}'.format(value))

        @Feat(values=MODULATION_TYPE)
        def mod_type(self):
            """
            Modulation State
            """
            return int(self.query('TYPE?'))

        @mod_type.setter
        def mod_type(self, value):
            self.write('TYPE {}'.format(value))

        @Feat(values=MODULATION_FUNCTION)
        def mod_function(self):
            """
            Modulation Function
            """
            return int(self.query('MFNC?'))

        @mod_function.setter
        def mod_function(self, value):
            self.write('MFNC {}'.format(value))

        @Feat(units="Hz", limits=(0.1, 100.e3))
        def mod_rate(self):
            """
            Modulation Rate
            """
            return float(self.query('RATE?'))

        @mod_rate.setter
        def mod_rate(self, val):
            self.write('RATE {}'.format(val))

        @Feat(limits=(0., 100.))
        def AM_mod_depth(self):
            """
            AM Modulation Depth
            """
            return float(self.query('ADEP?'))

        @AM_mod_depth.setter
        def AM_mod_depth(self, val):
            self.write('ADEP {}'.format(val))

        @Feat(units="Hz", limits=(0.1, 8.e6))
        def FM_mod_dev(self):
            """
            FM Modulation Deviation
            """
            return float(self.query("FDEV?"))

        @FM_mod_dev.setter
        def FM_mod_setter(self, val):
            self.write('FDEV {}'.format(val))


