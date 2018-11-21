# -*- coding: utf-8 -*-
"""
    lantz.drivers.aeroflex.a2023a
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers for an signal generator.


    Sources::

        - Aeroflex 2023a Manual.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import enum

from lantz.core import Feat, Action, MessageBasedDriver
from lantz.core.mfeats import BoolFeat, QuantityFeat, QuantityDictFeat, EnumFeat


class A2023a(MessageBasedDriver):
    """Aeroflex Test Solutions 2023A 9 kHz to 1.2 GHz Signal Generator.
    """

    DEFAULTS = {'ASRL': {'write_termination': '\n',
                         'read_termination': chr(256)}}

    #: Carrier frequency.
    frequency = QuantityFeat(('CFRQ?', ':CFRQ:VALUE {0:f};{_}'),
                             'CFRQ:VALUE {0:f}HZ', units='Hz')

    #: RF amplitude.
    amplitude = QuantityFeat(('RFLV?', ':RFLV:UNITS {_};TYPE {_};VALUE {0:f};INC {_};<status>'),
                             'RFLV:VALUE {0:f}V', units='V')

    #: Offset amplitude.
    offset = QuantityFeat(('RFLV:OFFS?', ':RFLV:OFFS:VALUE {0:f};{_}'),
                          'RFLV:OFFS:VALUE {0:f}', units='V')

    #: Enable or disable the RF output
    output_enabled = BoolFeat('OUTPUT?', 'OUTPUT:{}', 'ENABLED', 'DISABLED')

    #: Phase offset
    phase = QuantityFeat(('CFRQ?', ':CFRQ:VALUE {:f}; INC {_};MODE {_}'), 'CFRQ:PHASE {}', units='degree')

    #: Get internal or external frequency standard.
    class FREQUENCY_STANDARD(enum):
        INT = 'INT'
        EXT10DIR = 'EXT10DIR'
        EXTIND = 'EXTIND'
        EXT10IND = 'EXT10IND'
        INT10OUT = 'INT10OUT'

    #: Set RF output level max.
    rflimit = QuantityFeat('RFLV:LIMIT?', 'RFLV:LIMIT {}')

    def remote(self, value):
        if value:
            self.write('^A')
        else:
            self.write('^D')

    @Action(units='ms')
    def expose(self, exposure_time=1):
        self.write('EXPOSE {}'.format(exposure_time))

    @Feat(values={True: 'on', False: 'off'})
    def time(self):
        # TODO: ??
        self.write('')
        return self.read()

    @time.setter
    def time(self, value):
        self.write("vlal ".format(value))

    def local_lockout(self, value):
        if value:
            self.write('^R')
        else:
            self.write('^P')

    def software_handshake(self, value):
        if value:
            self.write('^Q')
        else:
            self.write('^S')


if __name__ == '__main__':
    import argparse
    import lantz.log

    parser = argparse.ArgumentParser(description='Test Kentech HRI')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=str, default='17',
                        help='Serial port to connect to')

    args = parser.parse_args()
    lantz.log.log_to_socket(lantz.log.DEBUG)
    with A2023a.from_serial_port(args.port) as inst:
        if args.interactive:
            from lantz.ui.app import start_test_app
            start_test_app(inst)
        else:
            print(inst.idn)
            inst.fstd = "EXT10DIR"
            print(inst.fstd)
            print(inst.freq)
            inst.freq = 41.006
            print(inst.rflevel)
            inst.rflevel = -13
            inst.phase=0
            print(inst.phase)
            inst.phase=30
            print(inst.phase)
            inst.phase=60
            print(inst.phase)

