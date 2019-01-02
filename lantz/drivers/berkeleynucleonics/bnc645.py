from lantz.messagebased import MessageBasedDriver
from lantz import Feat, Q_

class BNC645(MessageBasedDriver):

    DEFAULTS = {
        'COMMON': {
            'write_termination': '\n',
            'read_termination': '\n',
        },
    }

    # @Feat(units='V')
    # def amplitude(self):
    #     value = self.query("VOLT?")
    #     return float(value)
    #
    # @amplitude.setter
    # def amplitude(self, value):
    #     self.write("VOLT {}".format(value))
    #     return

    @Feat()
    def amplitude(self):
        self.write("VOLT:UNIT DBM")
        value = self.query("VOLT?")
        return float(value)

    @amplitude.setter
    def amplitude(self, value):
        self.write("VOLT:UNIT DBM")
        self.write("VOLT {}".format(value))
        return

    @Feat(units='Hz')
    def frequency(self):
        value = self.query("FREQ?")
        return float(value)

    @frequency.setter
    def frequency(self, value):
        self.write("FREQ {:1.8e}".format(value))
        return

    @Feat(values={True: '1', False: '0'})
    def output(self):
        value = self.query("OUTP?")
        return value

    @output.setter
    def output(self, value):
        self.write("OUTP {}".format(value))
        return
