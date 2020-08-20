# -*- coding: utf-8 -*-
"""
    lantz.drivers.rigol.ds1204b
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers to control an oscilloscope.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.

    Source: programming guide: http://int.rigol.com/File/TechDoc/20150909/DS1000B%20Programming%20Guide.pdf
"""
import numpy as np

#from lantz import Feat, DictFeat, Action
#from lantz.messagebased import MessageBasedDriver
from lantz.core import Action, Feat, DictFeat, MessageBasedDriver

from collections import OrderedDict


class DS1204B(MessageBasedDriver):

    WAVEFORM_FORMATS = OrderedDict([
                   ('word', 'WORD'),
                   ('byte', 'BYTE'),
                   ('ascii', 'ASCII')
                   ])

    AVERAGES = OrderedDict([
                 (2, 2),
                 (4, 4),
                 (8, 8),
                 (16, 16),
                 (32, 32),
                 (64, 64),
                 (128, 128),
                 (256, 256),
    ])

    CHANNELS = OrderedDict([
                ('1', '1'),
                ('2', '2'),
                ('3', '3'),
                ('4', '4'),
                ('MATH', 'MATH'),
    ])

    DEFAULTS = {
        'COMMON': {
            'write_termination': '\n',
            'read_termination': '\n',
        }
    }

    @Feat()
    def idn(self):
        """
        Returns instrument identity
        """
        return self.query('*IDN?')

    @Action()
    def get_waveform_data(self, channel=None):
        """
        Returns waveform data.
        """
        msg = ':WAV:DATA?'

        if channel:

            msg += ' CHAN{}'.format(channel)

        data = self.resource.query_binary_values(msg, datatype='B')
        return np.fromiter(data, dtype='uint8')

    @Action()
    def get_waveform_trace(self, channel=None):
        """
        Returns waveform x and y traces, with units.
        """
        result_string = self.query(':WAV:PRE?')
        frmt, typ, points, count, x_inc, x_or, x_ref, y_inc, y_or, y_ref = result_string.split(',')

        x_inc = float(x_inc)
        x_or = float(x_or)
        y_inc = float(y_inc)
        y_or = float(y_or)
        x_ref = int(x_ref)
        y_ref = int(y_ref)

        raw = self.get_waveform_data(channel=channel)
        raw = raw.astype(np.int8, copy=False)

        t_i = (np.arange(raw.size, dtype='float') - x_ref) * x_inc + x_or
        y_i = np.empty(raw.size, dtype='float')

        y_i = (raw - y_ref) * y_inc + y_or

        return t_i, y_i


    @Feat(values=WAVEFORM_FORMATS)
    def waveform_format(self):
        """
        Reads format for waveform return data.
        """
        return self.query(':WAV:FORM?')

    @Feat()
    def waveform_preamble(self):
        """
        Queries waveform preamble.

        Preamble contents:
        Format: BYTE - 0, WORD - 1, ASCII - 2
        Type: Normal - 0, PEAK_DETECT - 1, AVERAGE - 2
        Count: # of averages (1 in non-averaging modes)
        Xinc: TimeScale / 50
        Xor: relative time of trigger points
        Xref: X reference
        Yinc: Y unit voltage
        Yor: vertical offset relative to yref
        Yref: y reference point
        """
        result_string = self.query(':WAV:PRE?')
        format, type, points, count, xinc, xor, xref, yinc, yor, yref = result_string.split(',')
        return format, type, points, count, xinc, xor, xref, yinc, yor, yref


    @Feat(values=AVERAGES)
    def averages(self):
        """
        Queries the number of averages used.
        """
        return int(self.query(':ACQ:AVER?'))

    @averages.setter
    def averages(self, n_avg):
        """
        Sets the number of averages used.
        """
        return self.write(':ACQ:AVER {}'.format(n_avg))





if __name__ == '__main__':
    ip_addr = '192.168.1.109'

    inst = DS1204B('TCPIP::{}::INSTR'.format(ip_addr))
    inst.initialize()

    # with DS1204B('TCPIP::{}::INSTR'.format(ip_addr)) as inst:
    #     print(inst.idn)
