# -*- coding: utf-8 -*-
"""
    lantz.drivers.aa.aotf
    ~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers for an AOTF Controller


    Implementation Notes
    --------------------

    There are currently two (disconnected) ways of setting the power for each
    line: powerdb and power.

    Sources::

        - MDSnC Manual

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

#TODO: Implement calibrated power.

from lantz.core import MessageBasedDriver
from lantz.core.mfeats import BoolFeat, BoolDictFeat, QuantityDictFeat


class MDSnC(MessageBasedDriver):
    """MDSnC synthesizer for AOTF.nC
    """

    CHANNELS = list(range(8))

    DRIVER_TRUE = 1
    DRIVER_FALSE = 0

    #: Enable the main ouput.
    main_enabled = BoolFeat(None, 'I{}')

    #: Enable a single channel.
    enabled = BoolDictFeat(None, 'L{key}O{value}', keys=CHANNELS)

    #: RF frequency for a given channel.
    frequency = QuantityDictFeat(None, 'L{key}F{value}', keys=CHANNELS, units='Hz')

    #: Power for a given channel (in db).
    powerdb = QuantityDictFeat(None, 'L{key}D{value}', keys=CHANNELS)

    #: Power for a given channel (in digital units).
    power = QuantityDictFeat(None, 'L{key}P{value:04d}', keys=CHANNELS, limits=(0, 1023, 1))


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
    with MDSnC.from_serial_port(args.port) as inst:
        if args.interactive:
            from lantz.ui.app import start_test_app
            start_test_app(inst)
        else:
            from time import sleep
            print("init")
            freq = 130
            inst.power(4,10)
            sleep(0.2)
            inst.enabled(4,1)
            sleep(1.2)
            inst.enabled(4,0)
            sleep(1.2)
            inst.enabled(4,1)


