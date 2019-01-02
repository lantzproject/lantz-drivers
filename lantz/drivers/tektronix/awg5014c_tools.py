"""
    spyre.Tools.wfm_writer.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tool to write waveform in a .WFM format

    Authors: Alexandre Bourassa, Kevin Miao
    Date: 20/04/2016
"""

import struct
import numpy as _np
from datetime import datetime as _dt
import time as _t
import sys

def array_to_ieee_block(analog, marker1, marker2, prepend_length=True):
    """
        Produces a little-endian 4-byte floating point + 1-byte marker representation of analog
        :param analog: Array of numpy float32
        :param marker1: Array of numpy int8
        :param marker2: Array of numpy int8
        :return: Byte Stream in the WFM format
    """
    num_bytes = 5 * len(analog)
    num_digit = len(str(num_bytes))
    if not marker1.dtype==_np.int8: marker1 = _np.asarray(marker1, dtype=_np.int8)
    if not marker2.dtype==_np.int8: marker2 = _np.asarray(marker2, dtype=_np.int8)
    if not analog.dtype == _np.float32: analog = _np.asarray(analog, dtype=_np.float32)

    points = _np.zeros(len(analog), dtype='<f4, i1')
    points['f1'] = (marker1 + ((marker2)<<1))<<6
    points['f0'] = analog

    #Makes sure that the byteordering is 'little'
    if not sys.byteorder == 'little': points = points.newbyteorder('<')
    bin_all = points.tobytes()

    if prepend_length:  return bytes('#{:d}{:d}'.format(num_digit, num_bytes), encoding='ascii') + bin_all
    else             :  return bin_all

def iee_block_to_array(block):
    """
    Decodes an iee block into three arrays
    :param block: iee formatted block
    :return: analog, marker1, marker2
    """
    block = block.rstrip()

    #Check for a '#'
    if block[0:1] != b'#': raise ValueError("Argument is not a iee formatted block")

    #Check for that there is the correct number of bytes
    num_digit = int(block[1:2])
    num_bytes = int(block[2:2+num_digit])
    block = block[2 + num_digit:]
    if len(block) != num_bytes: raise ValueError("Argument is not a iee formatted block")

    n_points = int(num_bytes/5)
    array = struct.unpack('<'+'fB'*n_points, block)
    analog = _np.array(array[::2])
    marker = _np.array(array[1::2])
    print(marker)
    marker1 = _np.right_shift(_np.bitwise_and(marker, 64), 6)
    marker2 = _np.right_shift(marker, 7)
    return analog, marker1, marker2

class AWG_Record(object):
    def __init__(self, name, data, data_type=None):
        self.name = name
        self.data = data
        if data_type is None:
            if type(data) == str:       self.data_type = 'char'
            elif type(data) == float:   self.data_type = 'double'
            elif type(data) == bytes :  self.data_type = 'bytes'
            else:                       self.data_type = 'short'
        else:
            if not data_type in ['char', 'double', 'long', 'short', 'bytes']: raise Exception("Invalid data type!")
            self.data_type= data_type

    def _get_format_str(self, data, type):
        if type == 'char':      return '%ds'%(len(data)+1)
        elif type == 'double':  return 'd'
        elif type == 'long':    return 'l'
        elif type == 'short':   return 'h'
        elif type == 'bytes':   return '%ds'%(len(data))
        else:   raise Exception("Invalid data type!")

    def _get_length(self, data, type):
        if   type == 'char':   return len(data) + 1
        elif type == 'bytes':  return len(data)
        elif type == 'double': return 8
        elif type == 'long':   return 4
        elif type == 'short':  return 2
        else :raise Exception("Invalid data type!")

    def get_bytes(self):
        fmt = '<ii'+self._get_format_str(self.name, 'char')+self._get_format_str(self.data, self.data_type)
        name_l = self._get_length(self.name, 'char')
        data_l = self._get_length(self.data, self.data_type)
        if self.data_type == 'char':   data = bytes(self.data, encoding='ascii')
        else                       :   data = self.data
        return struct.pack(fmt, name_l, data_l, bytes(self.name, encoding='ascii'), data)


class AWG_File_Writer(object):
    def __init__(self):
        self.records = ([],[],[],[],[],[],[],)
        self.add_record("MAGIC", 5000, 1)
        self.add_record("VERSION", 1, 1)
        self.wfm  = list()
        self.n_seq_lines = 0

    def add_record(self, name, data, group, data_type=None):
        group -= 1
        if not group in range(7): raise Exception("Invalid group!")
        self.records[group].append(AWG_Record(name, data, data_type=data_type))

    def add_waveform(self, name, analog, marker1, marker2):
        if len(self.wfm)>=32000: raise Exception("Maximum 32000 waveform in .AWG file...")
        if len(analog)<250:
            print("WARNING: The AWG will use the software sequencer because this waveform has less than 250 points")
        data = array_to_ieee_block(analog, marker1, marker2, prepend_length=False)
        t = _dt.now()
        tm = [t.year, t.month, t.weekday(), t.day, t.hour, t.minute, t.second, t.microsecond // 1000]
        self.wfm.append(name)
        N = len(self.wfm)
        self.add_record("WAVEFORM_NAME_{}".format(N), name, 5)
        self.add_record("WAVEFORM_TYPE_{}".format(N), 2, 5)
        self.add_record("WAVEFORM_LENGTH_{}".format(N), len(analog), 5, data_type='long')
        self.add_record("WAVEFORM_TIMESTAMP_{}".format(N), struct.pack('<' + 'h' * 8, *tm), 5, data_type='bytes')
        self.add_record("WAVEFORM_DATA_{}".format(N), data, 5)

    def add_sequence_line(self, wfm=("", "", "", ""), use_sub_seq = False, sub_seq_name="",
                          repeat_count=0, wait_for_trigger=False, jump_target=0, goto_target=0):
        if self.n_seq_lines >= 8000: raise Exception("Maximum 8000 lines for main sequence in .AWG file...")
        N = self.n_seq_lines + 1
        if not (len(wfm) == 4): raise Exception("There should be 4 entries in the wfm tuples")
        if not 65536 >= repeat_count >= 0: raise Exception("Maximum of 65536 for repeat_count")
        if not use_sub_seq and wfm[0] == wfm[1] == wfm[2] == wfm[3] == "": raise Exception("At least one channel must have non-empty wfm")
        if use_sub_seq and sub_seq_name=="": raise Exception("sub_seq_name is empty")

        self.add_record('SEQUENCE_WAIT_{}'.format(N), wait_for_trigger, 6)
        self.add_record('SEQUENCE_LOOP_{}'.format(N), repeat_count, 6, data_type='long')
        self.add_record('SEQUENCE_JUMP_{}'.format(N), jump_target, 6)
        self.add_record('SEQUENCE_GOTO_{}'.format(N), goto_target, 6)

        # Add the wfm / subseq

        if use_sub_seq:
            wfm = ("", "", "", "")
        else:
            sub_seq_name = ""

        for i in range(len(wfm)):
            if not use_sub_seq:
                if wfm[i] != "": self.add_record("SEQUENCE_WAVEFORM_NAME_CH_{}_{}".format(i + 1, N), wfm[i], 6)
        self.add_record("SEQUENCE_IS_SUBSEQ_{}".format(N), int(use_sub_seq), 6, data_type='long')
        self.add_record("SEQUENCE_SUBSEQ_NAME_{}".format(N), sub_seq_name, 6)
        self.n_seq_lines += 1

    def add_subseq(self, name):
        ss = Sub_Sequence(name)
        self.records[6].append(ss)
        return ss


    def get_bytes(self):
        ans = list()
        for i in range(len(self.records)):
            group_list = self.records[i]
            if not i == 6:
                ans.extend([entry.get_bytes() for entry in group_list])
            else:
                # Special treatement for subseq group
                subseq_number, cummul_line = 1, 0
                for ss in group_list:
                    if len(ss.lines) != 0:
                        ans += ss.get_bytes(subseq_number,cummul_line)
                        subseq_number += 1
                        cummul_line += len(ss.lines)

        return b''.join(ans)

class Sub_Sequence(object):
    def __init__(self, name):
        self.name = name
        self.lines = list()

    def add_line(self, wfm=("", "", "", ""), repeat_count=1):
        if not 65536 >= repeat_count >= 0: raise Exception("Maximum of 65536 for repeat_count")
        if not (len(wfm) == 4): raise Exception("There should be 4 entries in the wfm tuples")
        if wfm[0] == wfm[1] == wfm[2] == wfm[3] == "": raise Exception("At least one channel must have non-empty wfm")

        self.lines.append([repeat_count, wfm])
        # line = list()
        # n = len(self.lines + 1)
        # line.append(AWG_Record("SUBSEQ_LOOP_{}_{}_{}".format(n,self.o,n), , data_type=data_type))

    def get_bytes(self, subseq_number, cummul_line):
        ans = b''
        u = cummul_line + 1
        o = subseq_number
        t = _dt.now()
        tm = [t.year, t.month, t.weekday(), t.day, t.hour, t.minute, t.second, t.microsecond // 1000]
        rec = [
            AWG_Record("SUBSEQ_NAME_{}".format(o), self.name),
            AWG_Record("SUBSEQ_TIMESTAMP_{}".format(o), struct.pack('<' + 'h' * 8, *tm), data_type='bytes'),
            AWG_Record("SUBSEQ_LENGTH_{}".format(o), len(self.lines), data_type='long')
        ]
        n = 1
        for line in self.lines:
            rec.append(AWG_Record("SUBSEQ_LOOP_{}_{}_{}".format(n,o,u), line[0], data_type='long'))
            wfm = line[1]
            for i in range(len(wfm)):
                    if wfm[i] != "":
                        rec.append(AWG_Record("SUBSEQ_WAVEFORM_NAME_CH_{}_{}_{}_{}".format(i + 1, n, o, u), wfm[i]))
            n += 1
            u += 1
        for entry in rec:
            ans += entry.get_bytes()
        return ans

# -----------------------------------
# DEPRECATED
# -----------------------------------

def create_wfm(analog, marker1, marker2, clock=None):
    """
        Generate the byte stream for a WFM file given 3 arrays (analog, marker1 and marker2)
        :param analog: Array of float
        :param marker1: Array of bool (or 1/0)
        :param marker2: Array of bool (or 1/0)
        :param clock: The clock speed that the waveform should be run at
        :return: Byte Stream in the WFM format
    """
    if not (len(analog) == len(marker1) == len(marker2)):
        raise ValueError('Mismatched analog and marker lengths')
    if max(analog) > 1.0 or min(analog) < -1.0:
        raise ValueError('analog values out of range')

    header = b'MAGIC 1000\r\n'
    trailer = bytes('CLOCK {:1.10E}\r\n'.format(clock), encoding='ascii') if clock is not None else b''
    body =  array_to_iee_block(analog, marker1, marker2)

    return b''.join((header, body, trailer))

class Sequence(object):
    def __init__(self):
        self.seq = []

    def add_line(self, ch1_wfm="", ch2_wfm="", ch3_wfm="", ch4_wfm="", repeat_count=0, wait_for_trigger=False, logic_jump_target=0, finished_goto=0):
        """
        This defines a new sequence line to be added to this SEQ file
        :param ch1_wfm: wfm (or pat) file to be used for CH1 on this line.
        :param ch2_wfm: wfm (or pat) file to be used for CH2 on this line.
        :param ch3_wfm: wfm (or pat) file to be used for CH3 on this line.
        :param ch4_wfm: wfm (or pat) file to be used for CH4 on this line.
        :param repeat_count: Repeat count for the line.  0 is infinity
        :param wait_for_trigger: Specify whether or not to wait for a trigger before running the wfm
        :param logic_jump_target: Line number where to jump upon EVENT IN input or FORCE EVENT triggers.
                                  0 is Off, -1 is next, and -2 is Table-jump
        :param finished_goto: Line to go after current line. 0 is Next. Maximum 8000.
        :return:
        """
        wait_for_trigger = 1 if bool(wait_for_trigger) else 0
        line = '"{}","{}","{}","{}",{},{},{},{},{}\r\n'.format(ch1_wfm, ch2_wfm, ch3_wfm, ch4_wfm,int(repeat_count),
                                                           wait_for_trigger, 0, int(logic_jump_target), finished_goto)
        self.seq.append(line)

    def verify_line(self, line):
        line = line.strip()
        args = line.split(",")
        print(line)
        print(args)
        if len(args) != 9: raise Exception("The number of paramter in the line <{}> is incorrect".format(line))
        if args[0]==args[1]==args[2]==args[3]=="": raise Exception("At least one channel must have non-empty wfm")
        if not 0<=int(args[4])<=65536: raise Exception("Invalid repeat_counts (must be 0 for infinity or [1,65536])")
        if not args[5] in ["0","1"]: raise Exception("wait_for_trigger must be 0 or 1")
        if not args[6] == "0": raise Exception("goto_one is not implemented and therefore must be set to 0")
        if not -2<=int(args[7])<=len(self.seq): raise Exception("Invalid logic_jump_target argument (must be in [-2, N] where N is the number of line in the sequence)")
        if not 0<=int(args[8])<=len(self.seq): raise Exception("Invalid finnished_goto argument (must be in [0, N] where N is the number of line in the sequence)")

    def get_str(self):
        s = "MAGIC 3004A\r\nLINES {}".format(len(self.seq))
        if len(self.seq)>8000: raise Exception("More than 8000 lines may not work...")
        for line in self.seq:
            self.verify_line(line)
            s+= line
        return s

    def get_bytes(self):
        return bytes(self.get_str() ,encoding='ascii')
