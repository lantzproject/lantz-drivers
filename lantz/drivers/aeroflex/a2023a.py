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

    @Feat(read_once=True)
    def idn(self):
        """Instrument identification.
        """
        return self.parse_query('*IDN?',
                                format='{manufacturer:s},{model:s},{serialno:s},{softno:s}')

    @Feat(read_once=True)
    def fitted_options(self):
        """Fitted options.
        """
        return self.query('*OPT?').split(',')

    @Action()
    def reset(self):
        """Set the instrument functions to the factory default power up state.
        """
        self.write('*RST')

    @Action()
    def self_test(self):
        """Is the interface and processor are operating?
        """
        return self.query('*TST?') == '0'

    @Action()
    def wait(self):
        """Inhibit execution of an overlapped command until the execution of
        the preceding operation has been completed.
        """
        self.write('*WAI')

    @Action()
    def trigger(self):
        """Equivalent to Group Execute Trigger.
        """
        self.write('*TRG')

    @Feat()
    def status_byte(self):
        """Status byte, a number between 0-255.
        """
        return int(self.query('*STB?'))

    @Feat()
    def service_request_enabled(self):
        """Service request enable register.
        """
        return int(self.query('*SRE?'))

    @service_request_enabled.setter
    def service_request_enabled(self, value):
        self.query('*SRE {0:d}'.format(value))

    @Feat()
    def event_status_reg(self):
        """Standard event enable register.
        """
        return int(self.query('*ESR?'))

    @event_status_reg.setter
    def event_status_reg(self, value):
        self.query('*ESR {0:d}'.format(value))

    @Feat()
    def event_status_enabled(self):
        """Standard event enable register.
        """
        return int(self.query('*ESR?'))

    @event_status_enabled.setter
    def event_status_enabled(self, value):
        self.query('*ESR {0:d}'.format(value))

    @Action()
    def clear_status(self):
        self.write('*CLS')

    @Feat(units='Hz')
    def frequency(self):
        """Carrier frequency.
        """
        return self.parse_query('CFRQ?',
                                format=':CFRQ:VALUE {0:f};{_}')

    @frequency.setter
    def frequency(self, value):
        self.write('CFRQ:VALUE {0:f}HZ'.format(value))

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

    @Feat(values={True: 'ENABLED', False: 'DISABLED'})
    def rflimit_enabled(self):
        return self.query('*RFLV:LIMIT?')

    @rflimit_enabled.setter
    def rflimit_enabled(self, value):
        self.query('RFLV:LIMIT:{}'.format(value))

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
            inst.phase = 0
            print(inst.phase)
            inst.phase = 30
            print(inst.phase)
            inst.phase = 60
            print(inst.phase)
