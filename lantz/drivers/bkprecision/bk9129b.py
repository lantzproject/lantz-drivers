from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver

class BK9129b(MessageBasedDriver):

    DEFAULTS = {
        'ASRL': {
            'write_termination': '\n',
            'read_termination': '\n',
            'timeout': 1000,
        }
    }

    @Feat()
    def idn(self):
        return self.query('*IDN?')

    @Action()
    def remote(self):
        self.write('SYST:REM')

    @Action()
    def local(self):
        self.write('SYST:LOC')

    @Feat()
    def channel(self):
        return int(self.query('INST?').lstrip('CH'))

    @channel.setter
    def channel(self, value):
        self.write('INST CH{}'.format(value))

    @DictFeat(units='A')
    def current(self, ch):
        return self.query('MEAS:CURR?')

    @DictFeat(units='V')
    def voltage(self, ch):
        return self.query('MEAS?')

    @voltage.setter
    def voltage(self, value):
        self.write('')

    @Feat(units='V')
    def voltage_limit(self):
        return self.query('VOLT:LIMIT?')

    @voltage_limit.setter
    def voltage_limit(self, value):
        self.write('VOLT:LIMIT {:1.2f}'.format(value))

    @Feat(values={False: 0, True: 1})
    def state(self):
        return int(self.query('CHAN:OUTP?'))

    @state.setter
    def state(self, value):
        self.write('CHAN:OUTP {:d}'.format(value))

def main():
    import logging
    import sys
    from lantz.log import log_to_screen
    import numpy as np
    log_to_screen(logging.CRITICAL)
    res_name = sys.argv[1]
    with BK9129b(res_name) as inst:
        print(inst.idn)
        inst.remote()
        inst.channel = 2
        print(inst.channel)
        print(inst.current[1])
        print(inst.voltage[1])
        inst.state = True
        print(inst.state)
        inst.voltage_limit = 1.23
        print(inst.voltage_limit)


if __name__ == '__main__':
    main()
