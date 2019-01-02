"""
    lantz.drivers.tektronix.awg5014c
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Drivers for the AWG5014C using RAW SOCKETS

    Authors: Alexandre Bourassa
    Date: 20/04/2016
"""
import numpy as _np

from lantz import Feat, DictFeat, Action
from lantz.feat import MISSING
from lantz.errors import InstrumentError
from lantz.messagebased import MessageBasedDriver

import ftplib as _ftp
import re as _re
import os as _os
import time as _t


from lantz.drivers.tektronix.awg5014c_tools import AWG_File_Writer, create_wfm, iee_block_to_array, array_to_ieee_block, Sequence
import lantz.drivers.tektronix.awg5014c_constants as _cst

class AWG5014C(MessageBasedDriver):
    """E8364B Network Analyzer
    """

    DEFAULTS = {'COMMON': {'write_termination': '\r\n',
                           'read_termination': '\r\n'}}

    def __init__(self, resource_name, *args, **kwargs):
        super(AWG5014C, self).__init__(resource_name, *args, **kwargs)
        self.ip = _re.findall("[0-9]+.[0-9]+.[0-9]+.[0-9]+", resource_name)[0]
        # self.ftp = _ftp.FTP(ip)
        # self.ftp.login()

    def finalize(self):
        pass

    @Feat(read_once=True)
    def idn(self):
        return self.query('*IDN?')

    @Action()
    def get_waveform_data(self, name):
        self.write('WLIS:WAV:DATA? "{}"'.format(name))
        data = self.resource.read_raw()
        return iee_block_to_array(data)

    @Action()
    def set_waveform_data(self, name, analog, marker1, marker2, start_index=None, size=None):
        """ Sets the data for waveform <name>.
            analog should be an array of float and marker 1 and 2 an array of bool or 0/1
            analog, marker1 and marker2 should have the same dimensions
        """
        data = array_to_ieee_block(analog, marker1, marker2)
        cmd = bytes('WLIS:WAV:DATA "{}",'.format(name), encoding='ascii')
        if not start_index is None:
            cmd += bytes('{},'.format(start_index), encoding='ascii')
            if not size is None:
                cmd += bytes('{},'.format(size), encoding='ascii')
        term = bytes(self.resource.write_termination, encoding='ascii')

        cmd += data + term
        self.log_debug('Writing {!r}', cmd)
        self.resource.write_raw(cmd+data+term)

    @Action()
    def create_new_waveform(self, name, size, type='REAL'):
        """ Create a new waveform with a given name and size (in number of points).
            type can be either REAL or INT, but only REAL is supported for now
        """
        self.write('WLIS:WAV:NEW "{}" {}'.format(name, size, type))

    @Action()
    def delete_waveform(self, name):
        """Delete wfm <name>.  If <name>=='ALL', deletes all user defined waveform"""
        if name == 'ALL': self.write('WLIS:WAV:DEL ALL')
        else: self.write('WLIS:WAV:DEL "{}"'.format(name))



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
    def force_jump(self, line_number):
        self.write("SEQUENCE:JUMP:IMMEDIATE {}".format(line_number))

    @Action()
    def trigger(self):
        self.write("*TRG")

    # ----------------------------------------------------
    # Source
    # ----------------------------------------------------
    @Action()
    def load_waveform(self, filename, drive="MAIN"):
        """This clear the user defined wlist and loads either a WFM, SEQ or PAT to it"""
        if not drive in self.VALID_DRIVE: raise Exception("Invalid drive!")
        self.write('SOURCE1:FUNCTION:USER "{}","{}"'.format(filename, drive))

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


# -----------------------------------
# DEBUGING AND TESTING
# -----------------------------------

def test_awg_file(awg):
    a = AWG_File_Writer()

    # Add waveform
    analog, m1, m2 = generate_test_sequence1()
    a.add_waveform('test', analog, m1, m2)
    analog, m1, m2 = generate_test_sequence2()
    a.add_waveform('hey', analog, m1, m2)

    # Add sub-sequence
    s = a.add_subseq("pySeq")
    s.add_line(wfm=("hey","hey","hey",""), repeat_count= 2)
    s.add_line(wfm=("test", "test", "test", ""), repeat_count=3)
    s.add_line(wfm=("hey", "hey", "hey", ""), repeat_count=4)

    # Add main sequence lines
    a.add_sequence_line(wfm=("test", "hey", "test", ""), use_sub_seq=False, sub_seq_name="", repeat_count=100,
                        wait_for_trigger=False, jump_target=0, goto_target=0)
    a.add_squence_line(use_sub_seq=True, sub_seq_name="pySeq", repeat_count=1)

    # Add some more records
    a.add_record("RUN_MODE", _cst.ERunMode.RunMode_SEQUENCE, 2)
    a.add_record(_cst.Commands.CS_SAMPLING_RATE, 500e6, 2)

    with open("test.awg", "wb") as f:
        f.write(a.get_bytes())
    awg.upload_file('test.awg', 'test.awg')
    awg.load_awg_file('test.awg')


def generate_test_sequence1():
    """Generate a test sequence with two pulse
     one in between sequence and one within
    """
    #Create the wfm
    m1 = _np.zeros(1024, dtype=_np.int32)
    m2 = _np.ones(1024, dtype=_np.int32)
    m2[0::2] = _np.zeros(512)
    analog = _np.zeros(1024)
    m1[-1] = 1
    m1[1] = 1
    return analog, m1, m2

def generate_test_sequence2():
    """Generate a test sequence with two pulse
     one in between sequence and one within
    """
    #Create the wfm
    m1 = _np.ones(1024, dtype=_np.int32)
    m2 = _np.zeros(1024, dtype=_np.int32)
    analog = _np.random.rand(1024)
    return analog, m1, m2




if __name__=='__main__':
    awg = AWG5014C('TCPIP0::192.168.1.104::4444::SOCKET')
    awg.initialize()