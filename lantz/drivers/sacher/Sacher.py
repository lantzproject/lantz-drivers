#Sacher_playground.py
"""
Make sure you're in the lantz32 environment to run this code properly
"""

import visa
import types
import ctypes
import sys
import numpy as np
import logging
from ctypes.wintypes import DWORD
from ctypes.wintypes import WORD
import ctypes.wintypes
import time
import os

from lantz.foreign import LibraryDriver
from lantz import Feat

directory = os.path.dirname(os.path.realpath(__file__))

DeviceName = b'EPOS'
ProtocolStackName = b'MAXON_RS232'
InterfaceName = b'RS232'


"""
    ok before I dive into this giant Sacher class thing let me just list here all the functions that are being defined in this class:

    These are the important ones:
    1) __init__(self, name, address, reset=False)
    2) open(self)
    3) initialize(self)
    4) get_offset(self)
    5) get_motor_position(self)
    6) do_get_wavelength(self)
    7) set_new_offset(self, new_offset)
    8) set_coeffs(self, a, b, c, min_wl, max_wl)
    9) do_set_wavelength(self, wavelength)
    10) set_target_position(self, target, absolute, immediately)

    And then there are these random ones:
    11) get_bit(self, byteval,idx)
    12) _u32todouble(self, uinput)
    13) _doubletou32(dinput)
    14) __del__(self)
    15) close(self)
    16) get_motor_current(self)
    17) find_home(self)
    18) restore(self)
    19) fine_tuning_steps(self, steps)
    20) is_open(self)
    21) clear_fault(self)

    They're labeled as #1, #2, ..., so you can find them with some ctrl+f
    """


class Sacher_EPOS(LibraryDriver):
    LIBRARY_NAME = 'EposCmd.dll'
    LIBRARY_PREFIX = 'VCS_'
#1)
    def __init__(self, name, address, reset=False):
        super().__init__()
        self._port_name = address
        self._is_open = False
        self._HPM = True
        self.open()
        self.initialize()
    """
    This is the special "__init__" function that gets runs automatically
    """

#2)
    def open(self):
        self.lib.OpenDevice.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(DWORD)]
        self.lib.OpenDevice.restype = ctypes.wintypes.HANDLE
        buf = ctypes.pointer(DWORD(0))
        ret = ctypes.wintypes.HANDLE()
        ret = self.lib.OpenDevice(DeviceName, ProtocolStackName, InterfaceName, self._port_name, buf)
        self._keyhandle = ret
        if int(buf.contents.value) >= 0:
            self._is_open = True
            self._keyhandle = ret
        return

#3)
    """
    This uses u32todouble three times, for the three coefficients

    Okay here's the important part:
    self._coefA = CastedObjectData[0]

    self._doubleA = self._u32todouble(self._coefA)
    self._doubleB = self._u32todouble(self._coefB)
    self._doubleC = self._u32todouble(self._coefC)
    self._currentwl = self._doubleA*(self._offset)**2.0 + self._doubleB*self._offset + self._doubleC

    """
    def initialize(self):
        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        BaudRate = DWORD(38400)
        Timeout = DWORD(100)
        ret = self.lib.SetProtocolStackSettings(self._keyhandle,BaudRate,Timeout,ctypes.byref(buf))
        if ret == 0:
            errbuf = ctypes.create_string_buffer(64)
            raise ValueError(errbuf.value)
        buf = ctypes.wintypes.DWORD(0)
        ret = self.lib.ClearFault(self._keyhandle,nodeID,ctypes.byref(buf))
        if ret == 0:
            errbuf = ctypes.create_string_buffer(64)
            self.lib.GetErrorInfo(buf, errbuf, WORD(64))
            raise ValueError(errbuf.value)
        buf = ctypes.wintypes.DWORD(0)
        plsenabled = ctypes.wintypes.DWORD(0)
        ret = self.lib.GetEnableState(self._keyhandle,nodeID,ctypes.byref(plsenabled),ctypes.byref(buf))
        if ret == 0:
            errbuf = ctypes.create_string_buffer(64)
            self.lib.GetErrorInfo(buf, errbuf, WORD(64))
            raise ValueError(errbuf.value)
        if int(plsenabled.value) != 0:
            logging.warning(__name__ + ' EPOS motor enabled, disabling before proceeding.')
            ret = self.lib.SetDisableState(self._keyhandle,nodeID,ctypes.byref(buf))
            if int(ret) != 0:
                logging.warning(__name__ + ' EPOS motor successfully disabled, proceeding')
            else:
                logging.error(__name__ + ' EPOS motor was not successfully disabled!')
        buf = ctypes.wintypes.DWORD(0)
        Counts = WORD(512) # incremental encoder counts in pulses per turn
        PositionSensorType = WORD(4)
        ret = self.lib.SetEncoderParameter(self._keyhandle,nodeID,Counts,PositionSensorType,ctypes.byref(buf))

        # Get operation mode, check if it's 1 -- this is "profile position mode"
        buf = ctypes.wintypes.DWORD(0)
        pMode = ctypes.pointer(ctypes.c_int8())
        self.lib.GetOperationMode.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.POINTER(ctypes.c_int8), ctypes.POINTER(ctypes.wintypes.DWORD)]
        self.lib.GetOperationMode.restype = ctypes.wintypes.BOOL
        ret = self.lib.GetOperationMode(self._keyhandle, nodeID, pMode, ctypes.byref(buf))
        # if mode is not 1, make it 1
        if pMode.contents.value != 1:
            self.lib.SetOperationMode.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.c_int8, ctypes.POINTER(ctypes.wintypes.DWORD)]
            self.lib.SetOperationMode.restype = ctypes.wintypes.BOOL
            pMode_setting = ctypes.c_int8(1)
            ret = self.lib.SetOperationMode(self._keyhandle, nodeID, pMode_setting, ctypes.byref(buf))
        self.lib.GetPositionProfile.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        self.lib.GetPositionProfile.restype = ctypes.wintypes.BOOL
        pProfileVelocity = ctypes.pointer(ctypes.wintypes.DWORD())
        pProfileAcceleration = ctypes.pointer(ctypes.wintypes.DWORD())
        pProfileDeceleration = ctypes.pointer(ctypes.wintypes.DWORD())
        ret = self.lib.GetPositionProfile(self._keyhandle, nodeID, pProfileVelocity, pProfileAcceleration, pProfileDeceleration,ctypes.byref(buf))

        #print(pProfileVelocity.contents.value, pProfileAcceleration.contents.value, pProfileDeceleration.contents.value)

        if (int(pProfileVelocity.contents.value) > int(11400) or int(pProfileAcceleration.contents.value) > int(60000) or int(pProfileDeceleration.contents.value) > int(60000)):
            self.lib.GetPositionProfile.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD)]
            self.lib.GetPositionProfile.restype = ctypes.wintypes.BOOL
            pProfileVelocity = ctypes.wintypes.DWORD(429)
            pProfileAcceleration = ctypes.wintypes.DWORD(429)
            pProfileDeceleration = ctypes.wintypes.DWORD(429)
            logging.warning(__name__ + ' GetPositionProfile out of bounds, resetting...')
            ret = self.lib.SetPositionProfile(self._keyhandle, nodeID, pProfileVelocity, pProfileAcceleration, pProfileDeceleration,ctypes.byref(buf))

        self._offset = self.get_offset()

        """DC - These are hardcoded values I got from the LabVIEW program -- I don't think any documentation exists on particular object indices"""

        """Coefficient A"""
        self.lib.GetObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        self.lib.GetObject.restype = ctypes.wintypes.BOOL
        StoredPositionObject = ctypes.wintypes.WORD(8204)
        StoredPositionObjectSubindex = ctypes.c_uint8(1)
        StoredPositionNbBytesToRead = ctypes.wintypes.DWORD(4)
        ObjectData = ctypes.c_void_p()
        ObjectDataArray = (ctypes.c_uint32*1)()
        ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_uint32))
        StoredPositionNbBytesRead = ctypes.pointer(ctypes.wintypes.DWORD(0))
        ret = self.lib.GetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToRead, StoredPositionNbBytesRead, ctypes.byref(buf))
        # Cast the object data to uint32
        CastedObjectData = ctypes.cast(ObjectData, ctypes.POINTER(ctypes.c_uint32))
        self._coefA = CastedObjectData[0]

        """Coefficient B"""
        self.lib.GetObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        self.lib.GetObject.restype = ctypes.wintypes.BOOL
        StoredPositionObject = ctypes.wintypes.WORD(8204)
        StoredPositionObjectSubindex = ctypes.c_uint8(2)
        StoredPositionNbBytesToRead = ctypes.wintypes.DWORD(4)
        ObjectData = ctypes.c_void_p()
        ObjectDataArray = (ctypes.c_uint32*1)()
        ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_uint32))
        StoredPositionNbBytesRead = ctypes.pointer(ctypes.wintypes.DWORD(0))
        ret = self.lib.GetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToRead, StoredPositionNbBytesRead, ctypes.byref(buf))
        # Cast the object data to uint32
        CastedObjectData = ctypes.cast(ObjectData, ctypes.POINTER(ctypes.c_uint32))
        self._coefB = CastedObjectData[0]

        """Coefficient C"""
        self.lib.GetObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        self.lib.GetObject.restype = ctypes.wintypes.BOOL
        StoredPositionObject = ctypes.wintypes.WORD(8204)
        StoredPositionObjectSubindex = ctypes.c_uint8(3)
        StoredPositionNbBytesToRead = ctypes.wintypes.DWORD(4)
        ObjectData = ctypes.c_void_p()
        ObjectDataArray = (ctypes.c_uint32*1)()
        ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_uint32))
        StoredPositionNbBytesRead = ctypes.pointer(ctypes.wintypes.DWORD(0))
        ret = self.lib.GetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToRead, StoredPositionNbBytesRead, ctypes.byref(buf))
        # Cast the object data to uint32
        CastedObjectData = ctypes.cast(ObjectData, ctypes.POINTER(ctypes.c_uint32))
        self._coefC = CastedObjectData[0]

        """Coefficient D"""
        self.lib.GetObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        self.lib.GetObject.restype = ctypes.wintypes.BOOL
        StoredPositionObject = ctypes.wintypes.WORD(8204)
        StoredPositionObjectSubindex = ctypes.c_uint8(4)
        StoredPositionNbBytesToRead = ctypes.wintypes.DWORD(4)
        ObjectData = ctypes.c_void_p()
        ObjectDataArray = (ctypes.c_uint32*1)()
        ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_uint32))
        StoredPositionNbBytesRead = ctypes.pointer(ctypes.wintypes.DWORD(0))
        ret = self.lib.GetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToRead, StoredPositionNbBytesRead, ctypes.byref(buf))
        # Cast the object data to uint32
        CastedObjectData = ctypes.cast(ObjectData, ctypes.POINTER(ctypes.c_uint32))
        self._coefD = CastedObjectData[0]

        """
        print('coefficients are %s %s %s %s' % (self._coefA, self._coefB, self._coefC, self._coefD))
        This gives the coefficients in some weird form, they're not what you expect them to be
        """

        self._doubleA = self._u32todouble(self._coefA)
        self._doubleB = self._u32todouble(self._coefB)
        self._doubleC = self._u32todouble(self._coefC)
        firstHalf = np.int16(self._coefD >> 16)
        secondHalf = np.int16(self._coefD & 0xffff)
        # Set the minimum and maximum wavelengths for the motor
        self._minwl = float(firstHalf)/10.0
        self._maxwl = float(secondHalf)/10.0
        # print 'first %s second %s' % (firstHalf, secondHalf)
        # This returns '10871' and '11859' for the Sacher, which are the correct
        # wavelength ranges in Angstroms
        #print 'Now calculate the current wavelength position:'
        self._currentwl = self._doubleA*(self._offset)**2.0 + self._doubleB*self._offset + self._doubleC
        #print('Current wavelength: %.3f nm' % self._currentwl)
        print('initializing done')
        print("")
        return True



#4)
    def get_offset(self):
        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        self.lib.GetObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        self.lib.GetObject.restype = ctypes.wintypes.BOOL
        #DC - These are hardcoded values I got from the LabVIEW program -- I don't think any documentation exists on particular object indices
        StoredPositionObject = ctypes.wintypes.WORD(8321)
        StoredPositionObjectSubindex = ctypes.c_uint8(0)
        StoredPositionNbBytesToRead = ctypes.wintypes.DWORD(4)
        ObjectData = ctypes.c_void_p()
        ObjectDataArray = (ctypes.c_uint32*1)()
        ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_int32))
        StoredPositionNbBytesRead = ctypes.pointer(ctypes.wintypes.DWORD(0))
        ret = self.lib.GetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToRead, StoredPositionNbBytesRead, ctypes.byref(buf))
        # Cast the object data to uint32
        CastedObjectData = ctypes.cast(ObjectData, ctypes.POINTER(ctypes.c_int32))
        if ret == 0:
            logging.error(__name__ + ' Could not read stored position from Sacher EPOS motor')
        print('motor offset value is: %s' % CastedObjectData[0])
        return CastedObjectData[0]


#5)
    def get_motor_position(self):
        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        pPosition = ctypes.pointer(ctypes.c_long())
        self.lib.GetPositionIs.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.wintypes.DWORD)]
        self.lib.GetPositionIs.restype = ctypes.wintypes.BOOL
        ret = self.lib.GetPositionIs(self._keyhandle, nodeID, pPosition, ctypes.byref(buf))
        print('motor position value is: %s' % pPosition.contents.value)
        return pPosition.contents.value

#6)
    @Feat()
    def wavelength(self):
        self._offset = self.get_offset()
        self._motor_position = self.get_motor_position()
        self._currentwl1 = self._doubleA*(self._offset)**2.0 + self._doubleB*self._offset + self._doubleC
        self._currentwl2 = self._doubleA*(self._motor_position)**2.0 + self._doubleB*self._motor_position + self._doubleC
        print('Current wavelength according to offset: %.3f nm' % self._currentwl1)
        print('Current wavelength according to motor position: %.3f nm' % self._currentwl2)
        return self._currentwl1

    """
    And now we move on to setting things
    """
    @wavelength.setter
    def wavelength(self, wavelength):
        """
        Here's the basic procedure:
        1) Convert the desired target wavelength into a motor position, keeping in mind that we're using the offset as the motor position
        x is what the motor position should be
        2) Calculate difference between the target position and the stored offset
        3) Prompt some confirmation before we crash this plane
        4) Then actually move the motor
        """
        current_wavelength = self.wavelength
        current_offset = self.get_offset()

        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        x = (-1.0*self._doubleB + np.sqrt(self._doubleB**2.0 - 4.0*self._doubleA*(self._doubleC - wavelength))) / (2.0*self._doubleA)
        wavelength_to_pos = int(round(x))
        diff_wavelength_offset = wavelength_to_pos - int(self._offset)

        print('')
        print("The current wavelength, as according to the stored offset, is: %s" % current_wavelength)
        print("You're about to set the wavelength to: %s" % wavelength)
        print("This means moving the motor by %s steps" % diff_wavelength_offset)
        print("Where currently, the stored offset is: %s" % current_offset)
        # confirm = str(input("Is this ok? (y/n)"))
        #
        # if confirm == 'y':
        #     print('Ok then, setting wavelength...')
        #     print('')
        # else:
        #     print("ok then, shutting the whole thing down!")
        #     sys.exit(-1)

        if self._HPM and diff_wavelength_offset < 0:
            self.set_target_position(diff_wavelength_offset - 10000, False, True)
            self.set_target_position(10000, False, True)
        else:
            self.set_target_position(diff_wavelength_offset, False, True)

        self.set_new_offset(current_offset + diff_wavelength_offset)
        current_offset = self.get_offset()
        print("Now the stored offset is: %s" % current_offset)

        return

#7)
    def set_new_offset(self, new_offset):
        """
        This is NOT using the function "self.lib.MoveToPosition"
        So there's no literal motor movement is going on here
        It's just storing a value in some sort of saved memory on the instrument itself
        """
        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        self.lib.SetObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        self.lib.SetObject.restype = ctypes.wintypes.BOOL
        StoredPositionObject = ctypes.wintypes.WORD(8321)
        StoredPositionObjectSubindex = ctypes.c_uint8(0)
        StoredPositionNbBytesToWrite = ctypes.wintypes.DWORD(4)
        ObjectDataArray = (ctypes.c_uint32*1)(new_offset)
        ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_uint32))
        StoredPositionNbBytesWritten = ctypes.pointer(ctypes.wintypes.DWORD(0))
        ret = self.lib.SetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToWrite, StoredPositionNbBytesWritten, ctypes.byref(buf))
        if ret == 0:
            logging.error(__name__ + ' Could not write stored position from Sacher EPOS motor')
        return

#8)
    def set_coeffs(self, a, b, c, min_wl, max_wl):
        print('')
        print("setting coefficients...")
        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        self.lib.SetObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        self.lib.SetObject.restype = ctypes.wintypes.BOOL
        d = (min_wl << 16) + max_wl
        StoredPositionObject = ctypes.wintypes.WORD(8204)

        for subidx, coeff in enumerate([a, b, c]):
            print(subidx, coeff)
            StoredPositionObjectSubindex = ctypes.c_uint8(subidx + 1)
            StoredPositionNbBytesToWrite = ctypes.wintypes.DWORD(4)
            ObjectDataArray = (ctypes.c_uint32*1)(self._doubletou32(coeff))
            ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_uint32))
            StoredPositionNbBytesWritten = ctypes.pointer(ctypes.wintypes.DWORD(0))
            ret = self.lib.SetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToWrite, StoredPositionNbBytesWritten, ctypes.byref(buf))

        StoredPositionObjectSubindex = ctypes.c_uint8(4)
        StoredPositionNbBytesToWrite = ctypes.wintypes.DWORD(4)
        ObjectDataArray = (ctypes.c_uint32*1)(d)
        ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_uint32))
        StoredPositionNbBytesWritten = ctypes.pointer(ctypes.wintypes.DWORD(0))
        ret = self.lib.SetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToWrite, StoredPositionNbBytesWritten, ctypes.byref(buf))

        print('Coefficients are %s %s %s' % (self._doubleA, self._doubleB, self._doubleC))

        if ret == 0:
            logging.error(__name__ + ' Could not write stored position from Sacher EPOS motor')
        return


#9)
    def set_target_position(self, target, absolute, immediately):
        """
        This is the function that actually moves the motor
        Since the motor position this thing reads can't be trusted, we're only doing relative movements and not absolute ones
        This means the "absolute" argument should always be set as "false"

        "target" is the target motor position, but be very careful what you want to set this to depending on whether you're doing an absolute or relative movement

        In the "absolute" category,
        True starts an absolute movement, False starts a relative movement
        Since the absolute position can't be trusted at all, we should always do "False", the relative movement

        In the "immediately" category,
        True starts immediately, False waits to end of last positioning
        We typically do True for this without any real issues

        The actual money function is "self.lib.MoveToPosition"
        """

        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        ret = self.lib.SetEnableState(self._keyhandle,nodeID,ctypes.byref(buf))
        pTarget = ctypes.c_long(target)
        pAbsolute = ctypes.wintypes.BOOL(absolute)
        pImmediately = ctypes.wintypes.BOOL(immediately)
        self.lib.MoveToPosition.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.c_long, ctypes.wintypes.BOOL, ctypes.wintypes.BOOL, ctypes.POINTER(ctypes.wintypes.DWORD)]
        self.lib.MoveToPosition.restype = ctypes.wintypes.BOOL
        ret = self.lib.MoveToPosition(self._keyhandle, nodeID, pTarget, pAbsolute, pImmediately, ctypes.byref(buf))
        steps_per_second = 14494.0 # hardcoded, estimated roughly, unused now
        nchecks = 0
        while nchecks < 1000:
            self._motor_position = self.get_motor_position()
            self._offset = self.get_offset()
            pMovementState = ctypes.pointer(ctypes.wintypes.BOOL())
            self.lib.GetMovementState.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.POINTER(ctypes.wintypes.BOOL), ctypes.POINTER(ctypes.wintypes.DWORD)]
            self.lib.GetMovementState.restype = ctypes.wintypes.BOOL
            ret = self.lib.GetMovementState(self._keyhandle, nodeID, pMovementState, ctypes.byref(buf))
            if pMovementState.contents.value == 1:
                break
            nchecks = nchecks + 1
            time.sleep(0.01)
        ret = self.lib.SetDisableState(self._keyhandle,nodeID,ctypes.byref(buf))
        return ret

















































#11)
    @staticmethod
    def get_bit(byteval, idx):
    # def get_bit(self, byteval,idx):
        return ((byteval&(1<< idx ))!=0)
    """
    We take the two input numbers "byteval" and "idx" and do bitwise operations with them
    but it's not clear what the purpose of these bitwise operations are
    I also don't know what the @staticmethod decorator is supposed to be doing
    """

#12)
    @staticmethod
    def _u32todouble(uinput):
    # def _u32todouble(self, uinput):

        # get sign of number
        sign = Sacher_EPOS.get_bit(uinput,31)
        if sign == False:
            mantissa_sign = 1
        elif sign == True:
            mantissa_sign = -1
        exp_mask =  0b111111
        #print 'uin u is %d' % uinput
        #print 'type uin %s' % type(uinput)
        #print 'binary input is %s' % bin(long(uinput))
        # get sign of exponent
        if Sacher_EPOS.get_bit(uinput,7) == False:
            exp_sign = 1
        elif Sacher_EPOS.get_bit(uinput,7) == True:
            exp_sign = -1

        #print 'exp extract %s' % bin(int(uinput & exp_mask))
        #print 'exp conv %s' % (exp_sign*int(uinput & exp_mask))
        #print 'sign of exponent %s' % self.get_bit(uinput,7)
        #print 'binary constant is %s' % bin(int(0b10000000000000000000000000000000))
        mantissa_mask = 0b01111111111111111111111100000000
        # mantissa_mask = 0b0111111111111111111111110000000


        #print 'mantissa extract is %s' % bin((uinput & mantissa_mask) >> 8)
        mantissa = 1.0/1000000.0*float(mantissa_sign)*float((uinput & mantissa_mask) >> 8)
        #print 'mantissa is %.12f' % mantissa
        # print(1 if Sacher_EPOS.get_bit(uinput,31) else 0, mantissa, 1 if Sacher_EPOS.get_bit(uinput,7) else 0, uinput & exp_mask)
        output = mantissa*2.0**(float(exp_sign)*float(int(uinput & exp_mask)))
        #print 'output is %s' % output
        return output
    """
    ok dc gave some slight explanations here
    This function implements the "really weird/non-standard U32 to floating point conversion in the sacher VIs"
    It'd be gr8 if I knew what U32's were
    unsigned 32 bit something something?
    ah whatever
    Also I'm seeing mantissas and masks, this is bad
    """

#13)
    @staticmethod
    def _doubletou32(dinput):
        mantissa_bit = 0 if int(dinput / abs(dinput)) > 0 else 1
        exp_bit = 1 if -1 < dinput < 1 else 0

        b = np.ceil(np.log10(abs(dinput)))
        a = dinput / 10 ** b
        if dinput < 0:
            a = -a
        # print('a:\t{}\tb:\t{}'.format(a, b))

        d = np.log2(10) * b
        d_ = np.ceil(d)
        c = a * 2 ** (d - d_)
        # print('c:\t{}\td_:{}\toriginal:\t{}'.format(c, d_, c * 2 ** d_))

        return (int(mantissa_bit) << 31) + (int(c * 1e6) << 8) + (int(exp_bit) << 7) + int(abs(d_))

    """
    I think this was a new function that we made

    There might be a labview VI that does this correctly
    """

#14)
    def __del__(self):
        # execute disconnect
        self.close()
        return
    """
    this might be the only self explanatory one
    it disconnects
    """

#15)
    def close(self):
        print('closing EPOS motor.')

        self.lib.CloseDevice.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(DWORD)]
        self.lib.CloseDevice.restype = ctypes.wintypes.BOOL
        buf = ctypes.pointer(DWORD(0))
        ret = ctypes.wintypes.BOOL()

        ret = self.lib.CloseDevice(self._keyhandle, buf)

        #print 'close device returned %s' % buf

        if int(buf.contents.value) >= 0:
            self._is_open = False
        else:
            logging.error(__name__ + ' did not close Sacher EPOS motor correctly.')
        return
    """
    Apparently this closes the EPOS motor
    I don't know what "opening" and "closing" the motor means though
    and yeah also these random variables don't make any sense to me
    """


#16)
    def get_motor_current(self):
        nodeID = ctypes.wintypes.WORD(0)
        self.lib.GetCurrentIs.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.wintypes.DWORD)]
        self.lib.GetCurrentIs.restype = ctypes.wintypes.BOOL

        motorCurrent = ctypes.c_uint8(0)
        buf = ctypes.wintypes.DWORD(0)
        ret = self.lib.GetCurrentIs(self._keyhandle, nodeID, ctypes.byref(motorCurrent), ctypes.byref(buf))
        return motorCurrent.value

    """
    Not sure what this is doing yet
    """


#17)
    def find_home(self):
        nodeID = ctypes.wintypes.WORD(0)
        self.lib.FindHome.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.POINTER(ctypes.wintypes.DWORD)]
        self.lib.FindHome.restype = ctypes.wintypes.BOOL

        buf = ctypes.wintypes.DWORD(0)
        ret = self.lib.FindHome(self._keyhandle, nodeID, ctypes.c_uint8(35), ctypes.byref(buf))
        print('Homing: {}'.format(ret))
        return ret

    """
    Not sure what this is doing yet
    """


#18)
    def restore(self):
        nodeID = ctypes.wintypes.WORD(0)
        self.lib.FindHome.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.POINTER(ctypes.wintypes.DWORD)]
        self.lib.FindHome.restype = ctypes.wintypes.BOOL
        buf = ctypes.wintypes.DWORD(0)
        ret = self.lib.Restore(self._keyhandle, nodeID, ctypes.byref(buf))
        print('Restore: {}'.format(ret))
        return ret

    """
    Not sure what this is doing yet
    """



#19)
    def fine_tuning_steps(self, steps):
        current_motor_pos = self.get_motor_position()
        self._offset = self.get_offset()
        self.set_target_position(steps, False, True)
        new_motor_pos = self.get_motor_position()
        #print('New motor position is %s' % new_motor_pos)
        #print 'new offset is %s' % (new_motor_pos-current_motor_pos+self._offset)
        self.set_new_offset(new_motor_pos-current_motor_pos+self._offset)

    """
    Not sure what this is doing yet
    """

#20)
    def is_open(self):
        return self._is_open

#21)
    def clear_fault(self):
        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        ret = self.lib.ClearFault(self._keyhandle,nodeID,ctypes.byref(buf))
        print('clear fault buf %s, ret %s' % (buf, ret))
        if ret == 0:
            errbuf = ctypes.create_string_buffer(64)
            self.lib.GetErrorInfo(buf, errbuf, WORD(64))
            raise ValueError(errbuf.value)
    """
    Not sure what this is doing yet
    """




"""
We're done with the Sacher_EPOS() class at this point
"""
