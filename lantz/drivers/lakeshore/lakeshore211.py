from lantz import Feat
from lantz.messagebased import MessageBasedDriver

class Lakeshore211(MessageBasedDriver):

    DEFAULTS = {
        'COMMON': {
            'write_termination': '\r\n',
            'read_termination': '\r\n',
        }
    }

    @Feat(units='Kelvin')
    def temperature(self):
        return float(self.query('KRDG?'))
