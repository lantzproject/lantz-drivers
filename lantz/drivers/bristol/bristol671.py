from lantz.driver import Driver
from lantz import Feat, Action

from telnetlib import Telnet

class Bristol671(Driver):

    def __init__(self, ip, port=23, timeout=1):
        super().__init__()
        self.con_args = [ip,port,timeout]

    def initialize(self):
        self.resource = Telnet(*self.con_args)
        self.clear_read_buffer()
    
    def clear_read_buffer(self, timeout=0.1):
        while self.read(timeout=timeout) != '':
            pass

    def finalize(self):
        self.resource.close()

    def write(self, cmd, write_termination='\r\n'):
        return self.resource.write(bytes(cmd+write_termination, 'ascii'))

    def read(self, read_termination='\r\n', timeout=1):
        byte_ans = self.resource.read_until(bytes(read_termination, 'ascii'), timeout)
        ans = byte_ans.decode('ascii')
        return ans.strip(read_termination)

    def query(self, cmd, write_termination='\r\n', read_termination='\r\n'):
        self.write(cmd, write_termination=write_termination)
        return self.read(read_termination=read_termination)

    @Feat()
    def idn(self):
        return self.query('*IDN?')

    @Feat(units='nm')
    def wavelength(self):
        return float(self.query(':MEAS:WAV?'))

    @Feat(units='THz')
    def frequency(self):
        return float(self.query(':MEAS:FREQ?'))

    @Feat(units='mW')
    def power(self):
        self.write(':UNIT:POW MW')
        return float(self.query(':MEAS:POW?'))
