"""
    lantz.drivers.tektronix.awg5000
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Drivers for the Tektronix 5000 series AWG

    Authors: Alexandre Bourassa, Kevin Miao
    Date: September 14, 2016
"""

import numpy as np
import re
from enum import Enum
import ftplib as _ftp
import os as _os
import time as _t

from lantz.messagebased import MessageBasedDriver
from lantz import Feat, DictFeat, Action


class AWGState(Enum):
    stopped = 0
    trigger_wait = 1
    running = 2


_ch_markers = [(ch, m) for ch in range(1, 5) for m in range(1, 3)]

class AWG5000(MessageBasedDriver):

    DEFAULTS = {
        'COMMON': {
            'write_termination': '\n',
            'read_termination': '\n',
            'timeout': 10000,
        },
    }

    def __init__(self, resource_name, ftp_ip=None, *args, **kwargs):
        """If ftp_ip is None, it will attempt to figure out the ftp ip from the resources name
        """
        super().__init__(resource_name, *args, **kwargs)
        if ftp_ip is None:
            self.ip = re.findall('[0-9]+.[0-9]+.[0-9]+.[0-9]+', resource_name)
        else:
            self.ip = ftp_ip
        return

    def initialize(self):
        super().initialize()

        #Start from the ftp directory
        self.cd('\\')
        self.cd('ftp')

    @Feat(read_once=True)
    def idn(self):
        return self.query('*IDN?')

    @Feat(values={item.name: item.value for item in AWGState})
    # @Feat()
    def toggle_run(self):
        # return AWGState(int(self.query('AWGC:RST?')))
        return int(self.query('AWGC:RST?'))

    @toggle_run.setter
    def toggle_run(self, state):
        if state or state == AWGState.running:
            cmd = 'RUN'
        elif not state or state == AWGState.stopped:
            cmd = 'STOP'
        else:
            raise ValueError('invalid run state: {}'.format(state))
        self.write('AWGC:{}:IMM'.format(cmd))

    @DictFeat(keys=range(1, 5), values={True: '1', False: '0'})
    def toggle_output(self, channel):
        return self.query('OUTP{}:STAT?'.format(channel))

    @toggle_output.setter
    def toggle_output(self, channel, state):
        self.write('OUTP{}:STAT {}'.format(channel, state))

    @Action()
    def toggle_all_outputs(self, state):
        for channel in range(1, 5):
            self.toggle_output[channel] = state

    @DictFeat(units='V', keys=_ch_markers)
    def marker_amplitude(self, ch_m):
        ch, m = ch_m
        return float(self.query('SOUR{}:MARK{}:VOLT:AMPL?'.format(ch, m)))

    @marker_amplitude.setter
    def marker_amplitude(self, ch_m, value):
        ch, m = ch_m
        self.write('SOUR{}:MARK{}:VOLT:AMPL {}V'.format(ch, m, value))
        return

    @DictFeat(units='V', keys=_ch_markers)
    def marker_high(self, ch_m):
        ch, m = ch_m
        return float(self.query('SOUR{}:MARK{}:VOLT:HIGH?'.format(ch, m)))

    @marker_high.setter
    def marker_high(self, ch_m, value):
        ch, m = ch_m
        self.write('SOUR{}:MARK{}:VOLT:HIGH {}V'.format(ch, m, value))
        return

    @DictFeat(units='V', keys=_ch_markers)
    def marker_low(self, ch_m):
        ch, m = ch_m
        return float(self.query('SOUR{}:MARK{}:VOLT:LOW?'.format(ch, m)))

    @marker_low.setter
    def marker_low(self, ch_m, value):
        ch, m = ch_m
        self.write('SOUR{}:MARK{}:VOLT:LOW {}V'.format(ch, m, value))
        return

    @DictFeat(units='V', keys=_ch_markers)
    def marker_offset(self, ch_m):
        ch, m = ch_m
        return float(self.query('SOUR{}:MARK{}:VOLT:OFFS?'.format(ch, m)))

    @marker_offset.setter
    def marker_offset(self, ch_m, value):
        ch, m = ch_m
        self.write('SOUR{}:MARK{}:VOLT:OFFS {}V'.format(ch, m, value))
        return

    @DictFeat(limits=(1, 2 ** 16))
    def seq_loop_count(self, line):
        return int(self.query('SEQUENCE:ELEMENT{}:LOOP:COUNT?'.format(line)))

    @seq_loop_count.setter
    def seq_loop_count(self, line, count):
        self.write('SEQUENCE:ELEMENT{}:LOOP:COUNT {}'.format(line, count))

    @DictFeat(values={True: '1', False: '0'})
    def seq_loop_infinite(self, line):
        return self.query('SEQUENCE:ELEMENT{}:LOOP:INFINITE?'.format(line))

    @seq_loop_infinite.setter
    def seq_loop_infinite(self, line, infinite_loop):
        self.write('SEQUENCE:ELEMENT{}:LOOP:INFINITE {}'.format(line, infinite_loop))

    @Action()
    def jump_to_line(self, line):
        self.write('SEQ:JUMP:IMM {}'.format(line))

    @Action()
    def trigger(self):
        self.write('*TRG')

    @DictFeat()
    def waveform(self, key):
        index, channel = key
        return self.query('SEQ:ELEM{}:WAV{}?'.format(index, channel))

    @waveform.setter
    def waveform(self, key, value):
        index, channel = key
        self.write('SEQ:ELEM{}:WAV{} {}'.format(index, channel, value))


    # ----------------------------------------------------
    # Hard Drive navigation method
    # ----------------------------------------------------
    VALID_DRIVE = {"MAIN", "FLOP", "NET1", "NET2", "NET3"}

    @Action()
    def cd(self, dir):
        self.write('MMEM:CDIR "{}"'.format(dir))

    @Action()
    def ls(self, verbose=True):
        #Query the current directory and the content
        dir = self.query("MMEM:CDIR?").strip('"')
        content = self.query("MMEM:CAT?").split(',"')
        used, avail = map(int, content.pop(0).split(","))

        dirs = list()
        files = list()
        for item in content:
            item = item.strip('"')
            name, isDir, size = item.split(',')
            if isDir=='DIR': dirs.append(name)
            else           : files.append((name, size))

        # Build and print an answer (or return it
        if verbose:
            spaces_size = 30
            ans =  "{} ({:.2f}% full):\r\n".format(dir, (used / (used + avail)))
            for d in dirs: ans += '\t|_ '+d+(' '*(spaces_size-len(d)))+'DIR\n'
            for f in files: ans += '\t|_ '+f[0]+(' '*(spaces_size-len(f[0])))+f[1]+'\n'
            print(ans)
        else:
            return (dir, used, avail), dirs, files

    @Action()
    def mkdir(self, dir_name, drive="MAIN"):
        if not drive in self.VALID_DRIVE: raise Exception("Invalid drive!")
        self.write(':MMEM:MDIR "{}", "{}"'.format(dir_name, drive))

    @Action()
    def select_drive(self, drive):
        if not drive in self.VALID_DRIVE: raise Exception("Invalid drive!")
        self.write(':MMEM:MSIS "{}"'.format(drive))

    @Action()
    def get_current_drive(self):
        print(self.query(':MMEM:MSIS?'))

    #This might not work
    @Action()
    def mv(self, source_file_path, dest_file_path, source_drive="MAIN", dest_drive="MAIN"):
        if not source_drive in self.VALID_DRIVE: raise Exception("Invalid source drive!")
        if not dest_drive in self.VALID_DRIVE: raise Exception("Invalid destination drive!")
        self.write(':MMEM:MOVE "{}","{}","{}","{}"'.format(source_file_path, source_drive, dest_file_path, dest_drive))

    # This might not work
    @Action()
    def cp(self, source_file_path, dest_file_path, source_drive="MAIN", dest_drive="MAIN"):
        if not source_drive in self.VALID_DRIVE: raise Exception("Invalid source drive!")
        if not dest_drive in self.VALID_DRIVE: raise Exception("Invalid destination drive!")
        self.write(':MMEM:COPY "{}","{}","{}","{}"'.format(source_file_path, source_drive, dest_file_path, dest_drive))

    def upload_file(self, local_filename, remote_filename, print_progress=True):
        self.ftp = _ftp.FTP(self.ip)
        self.ftp.login()
        if print_progress:
            FTP_Upload(self.ftp,local_filename, remote_filename)
        else:
            self.ftp.storbinary('STOR ' + remote_filename, open(local_filename, 'rb'), blocksize=1024)
        self.ftp.quit()

    @Action()
    def load_awg_file(self, filename):
        self.write('AWGCONTROL:SRESTORE "{}"'.format(filename))



class FTP_Upload():
    def __init__(self, ftp, local_filename, remote_filename):

        block_size = 1024
        total_size = _os.path.getsize(local_filename)
        self.written_size = 0
        self.last_time = _t.time()
        self.last_percent = 0

        def callback(block):
            self.written_size += block_size
            time = _t.time()
            percent = (self.written_size / total_size)*100
            #print(time - self.last_time > 1,percent - self.last_percent  > 0.1)
            if time - self.last_time > 1 and percent - self.last_percent  > 0.1:
                self.last_time = time
                self.last_percent = percent
                print('{:.2f}%'.format(percent))
        print('Uploading "{}" to remote destination "{}"'.format(local_filename, remote_filename))
        ftp.storbinary('STOR ' + remote_filename, open(local_filename, 'rb'), blocksize=block_size, callback=callback)


if __name__ == '__main__':
    test()
