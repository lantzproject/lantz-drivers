# -*- coding: utf-8 -*-

import os

from lantz import Feat
from lantz.foreign import LibraryDriver
from ctypes import c_char_p
from time import sleep

class FF(LibraryDriver):

    lib_path = os.path.join(os.environ['PROGRAMFILES'], 'Thorlabs\\Kinesis')
    lib_name = 'Thorlabs.MotionControl.FilterFlipper.dll'


    LIBRARY_NAME = os.path.join(lib_path, lib_name)
    LIBRARY_PREFIX = ''

    COM_DELAY = 0.2

    def __init__(self, serial_no, *args, **kwargs):
        """
        serial_no: unique device identifier; found on the label of the device
        """
        self.prev_path = os.environ['PATH']
        os.environ['PATH'] = '{}{}{}'.format(self.lib_path, os.pathsep, self.prev_path)
        super(FF, self).__init__(*args, **kwargs)
        os.environ['PATH'] = self.prev_path
        self.serial_no = c_char_p(str(serial_no).encode('ascii'))
        retval = self.lib.FF_Open(self.serial_no)
        if retval:
            raise RuntimeError('Could not initialize device: error {}'.format(retval))
        return

    @Feat()
    def position(self):
        return self.lib.FF_GetPosition(self.serial_no)

    @position.setter
    def position(self, value):
        self.lib.FF_MoveToPosition(self.serial_no, value)
        return

if __name__ == '__main__':
    import logging
    import sys
    from lantz.log import log_to_screen
    import numpy as np
    log_to_screen(logging.CRITICAL)
    serial_no = sys.argv[1]
    with FF(serial_no) as inst:
        print(inst.position)
        inst.position = 1
        print(inst.position)
        sleep(1)
        inst.position = 2
