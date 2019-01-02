import ctypes
import time
from io import BytesIO
import struct
import numpy as np

from lantz.foreign import LibraryDriver
from lantz import Feat, DictFeat, Action

TTREADMAX = 131072
FIFOFULL = 0x0003

t2_wraparound = 210698240

class PH300(LibraryDriver):

    LIBRARY_NAME = 'phlib64.dll'
    LIBRARY_PREFIX = 'PH_'

    def __init__(self, device_idx):
        super().__init__()
        self.device_idx = device_idx
        return

    def call(self, func_name, *args):
        err = getattr(self.lib, func_name)(*args)
        if not err:
            return
        else:
            s = ctypes.create_string_buffer(50)
            self.lib.GetErrorString(s,err)
            raise Exception(s.value.decode('ascii'))

    def initialize(self):
        serial = ctypes.create_string_buffer(8)
        self.call('OpenDevice', self.device_idx, serial)
        self.call('Initialize', self.device_idx, 2)
        features = ctypes.c_int()
        self.call('GetFeatures', self.device_idx, ctypes.byref(features))
        return

    @DictFeat(keys=(0, 1))
    def count_rate(self, channel):
        rate = ctypes.c_int()
        self.call('GetCountRate', self.device_idx, channel, ctypes.byref(rate))
        return rate.value

    @Feat()
    def resolution(self):
        resolution = ctypes.c_double(0.0)
        self.call('GetResolution', self.device_idx, ctypes.byref(resolution))
        return resolution.value

    @Action()
    def set_input_cfd(self, channel, level, zero_cross):
        self.call('SetInputCFD', self.device_idx, channel, level, zero_cross)
        return

    @Action()
    def set_sync_div(self, sync_div):
        self.call('SetSyncDiv', self.device_idx, sync_div)
        return

    @Action()
    def set_binning(self, binning):
        self.call('SetBinning', self.device_idx, binning)
        return

    @Action()
    def set_offset(self, offset):
        self.call('SetOffset', self.device_idx, offset)
        return

    @Action(units=('ms'))
    def start_measurement(self, measurement_time):
        self.call('StartMeas', self.device_idx, int(measurement_time))
        return

    @Action()
    def stop_measurement(self):
        self.call('StopMeas', self.device_idx)
        return

    @Feat()
    def elapsed_measurement_time(self):
        elapsed = ctypes.c_double(0.0)
        self.call('GetElapsedMeasTime', self.device_idx, ctypes.byref(elapsed))
        return elapsed.value

    @Feat()
    def flags(self):
        flags = ctypes.c_uint()
        self.call('GetFlags', self.device_idx, ctypes.byref(flags))
        return flags.value

    @Action()
    def read_fifo(self, nvalues=TTREADMAX):
        databuf = BytesIO()
        buf = (ctypes.c_uint * nvalues)()
        n_to_read = ctypes.c_uint(nvalues)
        n_read = ctypes.c_uint(0)
        while 1:
            if self.flags & FIFOFULL:
                break
            retcode = self.lib.ReadFiFo(self.device_idx, ctypes.byref(buf), n_to_read, ctypes.byref(n_read))
            if retcode < 0:
                break
            if n_read.value:
                databuf.write(bytes(buf)[:n_read.value * 4])
            else:
                break
        databuf.seek(0)
        return databuf

    @Action()
    def read_timestamps(self, nvalues=TTREADMAX):
        databuf = self.read_fifo(nvalues=nvalues)
        c1 = list()
        c2 = list()
        overflow_time = 0
        resolution = self.resolution
        while 1:
            chunk = databuf.read(4)
            if not chunk:
                break
            chunk = struct.unpack('<I', chunk)[0]
            time = chunk & 0x0FFFFFFF
            channel = (chunk & 0xF0000000) >> 28
            if channel == 0xF:
                markers = time & 0xF
                if not markers:
                    overflow_time += t2_wraparound
                else:
                    truetime = overflow_time + time
            else:
                if channel > 4:
                    raise RuntimeError('invalid channel encountered: {}'.format(channel))
                else:
                    # truetime = (overflow_time + time) / 1e12 * resolution
                    truetime = (overflow_time + time) * resolution
                    if channel >= 1:
                        c2.append(truetime)
                    else:
                        c1.append(truetime)
        return c1, c2

    def finalize(self):
        self.call('CloseDevice', self.device_idx)
        return
