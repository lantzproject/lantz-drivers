# sacher_epos.py, python wrapper for sacher epos motor
# David Christle <christle@uchicago.edu>, August 2014
#

"""
This is the actual version that works
But only in the lab32 virtual environment
"""

#from instrument import Instrument
import visa
import types
import numpy
#import qt

import ctypes
import numpy as np
import logging
#from instrument import Instrument
from ctypes.wintypes import DWORD
from ctypes.wintypes import WORD
import ctypes.wintypes
import time

"""
okay so we import a bunch of random stuff
I always forget what ctypes is for but I'll worry about it later
"""

#from subprocess import Popen, PIPE
#from multiprocessing.managers import BaseManager
#import atexit
#import os

#python32_dir = "C:\\Users\\Alex\\Miniconda3\\envs\\lab32"

#assert os.path.isdir(python32_dir)
#os.chdir(python32_dir)

#derp = "C:\\Users\\Alex\\Documents\\wow_such_code"

#assert os.path.isdir(derp)
#os.chdir(derp)

#p = Popen([python32_dir + "\\python.exe", derp + "\\delegate.py"], stdout=PIPE, cwd=derp)

#atexit.register(p.terminate)

#port = int(p.stdout.readline())
#authkey = p.stdout.read()

#print(port, authkey)

#m = BaseManager(address=("localhost", port), authkey=authkey)
#m.connect()

# tell manager to expect an attribute called LibC
#m.register("SacherLasaTeknique")

# access and use libc
#libc = m.SacherLasaTeknique()
#print(libc.vcs())

#eposlib = ctypes.windll.eposcmd



eposlib = ctypes.windll.LoadLibrary('C:\\Users\\Carbro\\Desktop\\Charmander\\EposCmd.dll')

DeviceName = b'EPOS'
ProtocolStackName = b'MAXON_RS232'
InterfaceName = b'RS232'

"""
Max on
Max off
but anyway it looks like ctypes is the thing that's talking to the epos dll
"""


HISTCHAN = 65536
TTREADMAX = 131072
RANGES = 8

MODE_HIST = 0
MODE_T2 = 2
MODE_T3 = 3

FLAG_OVERFLOW = 0x0040
FLAG_FIFOFULL = 0x0003

# in mV
ZCMIN = 0
ZCMAX = 20
DISCRMIN = 0
DISCRMAX = 800

# in ps
OFFSETMIN = 0
OFFSETMAX = 1000000000

# in ms
ACQTMIN = 1
ACQTMAX = 10*60*60*1000

# in mV
PHR800LVMIN = -1600
PHR800LVMAX = 2400

"""
wooooooo a bunch a variables and none of them are explained
way to go dc you da real champ
"""


class Sacher_EPOS():

    """
    ok before I dive into this giant Sacher class thing let me just list here all the functions that are being defined in this class:
    check(self)
        before
        wreck(self)

    ok but actually:
    __init__(self, name, address, reset=False)
    __del__(self)
    get_bit(self, byteval,idx)
    _u32todouble(self, uinput)
    open(self)
    close(self)
    get_offset(self)
    fine_tuning_steps(self, steps)
    set_new_offset(self, new_offset)
    get_motor_position(self)
    set_target_position(self, target, absolute, immediately)
    do_get_wavelength(self)
    do_set_wavelength(self, wavelength)
    is_open(self)
    clear_fault(self)
    initialize(self)

    The last one is really long
    And also damn there are 16 of them
    I'll comment about them as I go through them
    """

    def __init__(self, name, address, reset=False):
        # Instrument.__init__(self, name, tags=['physical'])
        # self._port_name = str(address)
        self._port_name = address
        self._is_open = False
        self._HPM = True

        # self.add_parameter('wavelength',
        #     flags = Instrument.FLAG_GETSET,
        #     type = types.FloatType,
        #     units = 'nm',
        #     minval=1070.0,maxval=1180.0)

        # self.add_function('open')
        # self.add_function('close')
        # self.add_function('fine_tuning_steps')
        # self.add_function('get_motor_position')
        # self.add_function('set_target_position')
        #try:
        self.open()
        self.initialize()
        #except:
        #    logging.error('Error loading Sacher EPOS motor. In use?')
    """
    I mean to me this really seems like the initialize function
    so I wonder what initialize(self) is doing
    At any rate there doesn't seem to be a lot going on here
    """


    def __del__(self):
        # execute disconnect
        self.close()
        return
    """
    this might be the only self explanatory one
    it disconnects
    """

    @staticmethod
    def get_bit(byteval, idx):
    # def get_bit(self, byteval,idx):
        return ((byteval&(1<< idx ))!=0)
    """
    you get the bits, and then you use them
    but honestly I don't really get what this is doing
    sudo git a_clue
    """

    @staticmethod
    def _u32todouble(uinput):
    # def _u32todouble(self, uinput):
        # this function implements the really weird/non-standard U32 to
        # floating point conversion in the sacher VIs

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
    Apparently there's a "really weird/non-standard U32 to floating point conversion in the sacher VIs"
    It'd be gr8 if I knew what U32's were
    unsigned 32 bit something something?
    ah whatever
    I'll have to worry about this later
    """

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



    def open(self):
        eposlib.VCS_OpenDevice.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(DWORD)]
        eposlib.VCS_OpenDevice.restype = ctypes.wintypes.HANDLE
        buf = ctypes.pointer(DWORD(0))
        ret = ctypes.wintypes.HANDLE()

        #print 'types are all %s %s %s %s %s' % (type(DeviceName), type(ProtocolStackName), type(InterfaceName), type(self._port_name), type(buf))
        ret = eposlib.VCS_OpenDevice(DeviceName, ProtocolStackName, InterfaceName, self._port_name, buf)
        self._keyhandle = ret
        #print 'keyhandle is %s' % self._keyhandle
        #print 'open device ret %s' % buf
        #print 'printing'
        #print buf.contents.value
        #print 'done printer'
        if int(buf.contents.value) >= 0:
            self._is_open = True
            self._keyhandle = ret
        return
    """
    I have absolutely no idea what the hell this is doing
    Considering that close(self) is apparently closing the EPOS motor, maybe this is opening it
    """


    def close(self):
        print('closing EPOS motor.')

        eposlib.VCS_CloseDevice.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(DWORD)]
        eposlib.VCS_CloseDevice.restype = ctypes.wintypes.BOOL
        buf = ctypes.pointer(DWORD(0))
        ret = ctypes.wintypes.BOOL()

        ret = eposlib.VCS_CloseDevice(self._keyhandle, buf)

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



    def get_motor_current(self):
        nodeID = ctypes.wintypes.WORD(0)
        eposlib.VCS_GetCurrentIs.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.wintypes.DWORD)]
        eposlib.VCS_GetCurrentIs.restype = ctypes.wintypes.BOOL

        motorCurrent = ctypes.c_uint8(0)
        buf = ctypes.wintypes.DWORD(0)
        ret = eposlib.VCS_GetCurrentIs(self._keyhandle, nodeID, ctypes.byref(motorCurrent), ctypes.byref(buf))
        return motorCurrent.value

    """
    Not sure what this is doing yet
    """



    def find_home(self):
        nodeID = ctypes.wintypes.WORD(0)
        eposlib.VCS_FindHome.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.POINTER(ctypes.wintypes.DWORD)]
        eposlib.VCS_FindHome.restype = ctypes.wintypes.BOOL

        buf = ctypes.wintypes.DWORD(0)
        ret = eposlib.VCS_FindHome(self._keyhandle, nodeID, ctypes.c_uint8(35), ctypes.byref(buf))
        print('Homing: {}'.format(ret))
        return ret

    """
    Not sure what this is doing yet
    """



    def restore(self):
        nodeID = ctypes.wintypes.WORD(0)
        eposlib.VCS_FindHome.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.POINTER(ctypes.wintypes.DWORD)]
        eposlib.VCS_FindHome.restype = ctypes.wintypes.BOOL

        buf = ctypes.wintypes.DWORD(0)
        ret = eposlib.VCS_Restore(self._keyhandle, nodeID, ctypes.byref(buf))
        print('Restore: {}'.format(ret))
        return ret

    """
    Not sure what this is doing yet
    """



    def get_offset(self):
        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        eposlib.VCS_GetObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        eposlib.VCS_GetObject.restype = ctypes.wintypes.BOOL
        # These are hardcoded values I got from the LabVIEW program -- I don't think
        # any documentation exists on particular object indices
        StoredPositionObject = ctypes.wintypes.WORD(8321)
        StoredPositionObjectSubindex = ctypes.c_uint8(0)
        StoredPositionNbBytesToRead = ctypes.wintypes.DWORD(4)
        ObjectData = ctypes.c_void_p()
        ObjectDataArray = (ctypes.c_uint32*1)()
        ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_int32))
        StoredPositionNbBytesRead = ctypes.pointer(ctypes.wintypes.DWORD(0))
        ret = eposlib.VCS_GetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToRead, StoredPositionNbBytesRead, ctypes.byref(buf))

        # Cast the object data to uint32
        CastedObjectData = ctypes.cast(ObjectData, ctypes.POINTER(ctypes.c_int32))
        if ret == 0:
            logging.error(__name__ + ' Could not read stored position from Sacher EPOS motor')
        return CastedObjectData[0]

    """
    Not sure what this is doing yet
    """



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



    def set_new_offset(self, new_offset):
        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        eposlib.VCS_SetObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        eposlib.VCS_SetObject.restype = ctypes.wintypes.BOOL
        #print 'setting new offset'

        StoredPositionObject = ctypes.wintypes.WORD(8321)
        StoredPositionObjectSubindex = ctypes.c_uint8(0)
        StoredPositionNbBytesToWrite = ctypes.wintypes.DWORD(4)

        ObjectDataArray = (ctypes.c_uint32*1)(new_offset)
        ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_uint32))
        StoredPositionNbBytesWritten = ctypes.pointer(ctypes.wintypes.DWORD(0))
        ret = eposlib.VCS_SetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToWrite, StoredPositionNbBytesWritten, ctypes.byref(buf))

        if ret == 0:
            logging.error(__name__ + ' Could not write stored position from Sacher EPOS motor')
        return

    """
    Not sure what this is doing yet
    """



    def set_coeffs(self, a, b, c, min_wl, max_wl):
        print('')
        print("setting coefficients...")
        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        eposlib.VCS_SetObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        eposlib.VCS_SetObject.restype = ctypes.wintypes.BOOL
        #print 'setting new offset'
        d = (min_wl << 16) + max_wl

        StoredPositionObject = ctypes.wintypes.WORD(8204)
        for subidx, coeff in enumerate([a, b, c]):
            print(subidx, coeff)
            StoredPositionObjectSubindex = ctypes.c_uint8(subidx + 1)
            StoredPositionNbBytesToWrite = ctypes.wintypes.DWORD(4)


            ObjectDataArray = (ctypes.c_uint32*1)(self._doubletou32(coeff))
            ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_uint32))
            StoredPositionNbBytesWritten = ctypes.pointer(ctypes.wintypes.DWORD(0))
            ret = eposlib.VCS_SetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToWrite, StoredPositionNbBytesWritten, ctypes.byref(buf))

        StoredPositionObjectSubindex = ctypes.c_uint8(4)
        StoredPositionNbBytesToWrite = ctypes.wintypes.DWORD(4)
        ObjectDataArray = (ctypes.c_uint32*1)(d)
        ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_uint32))
        StoredPositionNbBytesWritten = ctypes.pointer(ctypes.wintypes.DWORD(0))
        ret = eposlib.VCS_SetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToWrite, StoredPositionNbBytesWritten, ctypes.byref(buf))

        print('Coefficients are %s %s %s' % (self._doubleA, self._doubleB, self._doubleC))

        if ret == 0:
            logging.error(__name__ + ' Could not write stored position from Sacher EPOS motor')
        return

    """
    Not sure what this is doing yet
    """



    def get_motor_position(self):
        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        pPosition = ctypes.pointer(ctypes.c_long())
        eposlib.VCS_GetPositionIs.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.wintypes.DWORD)]
        eposlib.VCS_GetPositionIs.restype = ctypes.wintypes.BOOL
        ret = eposlib.VCS_GetPositionIs(self._keyhandle, nodeID, pPosition, ctypes.byref(buf))
        #print 'get motor position ret %s' % ret
        #print 'get motor position buf %s' % buf.value
        #print 'get motor position value %s' % pPosition.contents.value

        return pPosition.contents.value

        #print('getting motor position...')
        #print(ret)
        #return print(pPosition.contents.value)

    """
    Not sure what this is doing yet
    """



    def set_target_position(self, target, absolute, immediately):
        #print('check #1')

        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        # First, set enabled state

        # print('#5 Motor current: {}'.format(self.get_motor_current()))
        # print('#5 Motor current: {}'.format(self.get_motor_current()))
        # print('#5 Motor current: {}'.format(self.get_motor_current()))
        # print('#5 Motor current: {}'.format(self.get_motor_current()))
        # print('#5 Motor current: {}'.format(self.get_motor_current()))

        ret = eposlib.VCS_SetEnableState(self._keyhandle,nodeID,ctypes.byref(buf))
        #print('Enable state ret %s buf %s' % (ret, buf.value))

        # print('#6 Motor current: {}'.format(self.get_motor_current()))
        # print('#6 Motor current: {}'.format(self.get_motor_current()))
        # print('#6 Motor current: {}'.format(self.get_motor_current()))
        # print('#6 Motor current: {}'.format(self.get_motor_current()))
        # print('#6 Motor current: {}'.format(self.get_motor_current()))

        pTarget = ctypes.c_long(target)
        pAbsolute = ctypes.wintypes.BOOL(absolute)
        pImmediately = ctypes.wintypes.BOOL(immediately)

        eposlib.VCS_MoveToPosition.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.c_long, ctypes.wintypes.BOOL, ctypes.wintypes.BOOL, ctypes.POINTER(ctypes.wintypes.DWORD)]
        eposlib.VCS_MoveToPosition.restype = ctypes.wintypes.BOOL

        #print('check #2')

        #print('About to set motor position')
        #print('Current motor position is %d' % (self.get_motor_position()))


        ret = eposlib.VCS_MoveToPosition(self._keyhandle, nodeID, pTarget, pAbsolute, pImmediately, ctypes.byref(buf))
        # print('#7 Motor current: {}'.format(self.get_motor_current()))
        # print('#7 Motor current: {}'.format(self.get_motor_current()))
        # print('#7 Motor current: {}'.format(self.get_motor_current()))
        # print('#7 Motor current: {}'.format(self.get_motor_current()))
        # print('#7 Motor current: {}'.format(self.get_motor_current()))

        #print('set motor position ret %s' % ret)
        #print('set motor position buf %s' % buf.value)

        steps_per_second = 14494.0 # hardcoded, estimated roughly, unused now

        nchecks = 0
        #print('check #3')
        while nchecks < 1000:
            # get the movement state. a movement state of 1 indicates the motor
            # is done moving
            # print('')
            # print('check #4')

            #print('Motor current: {}'.format(self.get_motor_current()))
            print('Motor position: {}'.format(self.get_motor_position()))
            #print('Motor offset: {}'.format(self.get_offset()))

            self._offset = self.get_offset()
            #print('Motor offset is %s' % self._offset)

            pMovementState = ctypes.pointer(ctypes.wintypes.BOOL())
            # print(pMovementState.contents.value)

            eposlib.VCS_GetMovementState.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.POINTER(ctypes.wintypes.BOOL), ctypes.POINTER(ctypes.wintypes.DWORD)]
            eposlib.VCS_GetMovementState.restype = ctypes.wintypes.BOOL
            # print('Getting movement state')
            ret = eposlib.VCS_GetMovementState(self._keyhandle, nodeID, pMovementState, ctypes.byref(buf))

            # print('set motor position ret %s' % ret)
            # print('set motor position buf %s' % buf.value)
            # print('Movement state is %s' % pMovementState.contents.value)
            if pMovementState.contents.value == 1:
                break
            nchecks = nchecks + 1
            # print('Current motor position is %d' % self.get_motor_position())
            # print('check #5')
            # print(nchecks)
            # print('')
            time.sleep(0.01)
        # Now set disabled state
        ret = eposlib.VCS_SetDisableState(self._keyhandle,nodeID,ctypes.byref(buf))
        #print('check #6')
        #print('Disable state ret %s buf %s' % (ret, buf.value))
        #print('Final motor position is %d' % (self.get_motor_position()))
        #print('check #7')
        return ret

    """
    Not sure what this is doing yet
    """



    def fuck_my_life(self, wavelength):
        print('goddamn this piece of shit')
        print('')

        print('Coefficients are %s %s %s' % (self._doubleA, self._doubleB, self._doubleC))
        #print('#3 Motor current: {}'.format(self.get_motor_current()))
        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)

        # Step 1: Get the actual motor position

        #print('Getting motor position')

        current_motor_pos = self.get_motor_position()

        # Step 2: Get the motor offset

        self._offset = self.get_offset()
        #print('Motor offset is %s' % self._offset)

        # Step 3: Convert the desired wavelength into a position
        # Check sign of position-to-wavelength
        pos0 = self._doubleA*(0.0)**2.0 + self._doubleB*0.0 + self._doubleC
        pos5000 = self._doubleA*(5000.0)**2.0 + self._doubleB*5000.0 + self._doubleC
        #    logging.error(__name__ + ' Sacher wavelength calibration polynomials indicated a wrong wavelength direction')
        # If that's OK, use the quadratic formula to calculate the roots
        b2a = -1.0*self._doubleB/(2.0*self._doubleA)
        sqrtarg = self._doubleB**2.0/(4.0*self._doubleA**2.0) - (self._doubleC - wavelength)/self._doubleA
        # print('wut da fuuuu')
        # print(b2a)
        # print(sqrtarg)
        # print(pos0)
        # print(pos5000)
        if sqrtarg < 0.0:
            logging.error(__name__ + ' Negative value under square root sign -- something is wrong')
        if pos0 > pos5000:
            # Take the + square root solution
            x = b2a - np.sqrt(sqrtarg)
        elif pos0 < pos5000:
            x = b2a + np.sqrt(sqrtarg)

        print(b2a)
        print(np.sqrt(sqrtarg))
        #print('Position is %s' % x)

        wavelength_to_pos = int(round(x))
        # Step 4: Calculate difference between the output position and the stored offset

        #print('Step 4...')

        diff_wavelength_offset = wavelength_to_pos - int(self._offset)
        print('wavelength_to_pos: {}'.format(wavelength_to_pos))
        print('diff_wavelength_offset: {}'.format(diff_wavelength_offset))
        print('self._offset: {}'.format(int(self._offset)))

    """
    Not sure what this is doing yet
    """



    def do_get_wavelength(self):
        self._offset = self.get_offset()
        #self._currentwl = self._doubleA*(self._offset)**2.0 + self._doubleB*self._offset + self._doubleC
        self._currentwl = self._doubleA*(self.get_motor_position())**2.0 + self._doubleB * self.get_motor_position() + self._doubleC
        print('Current wavelength: %.3f nm' % self._currentwl)
        return self._currentwl

    """
    Not sure what this is doing yet
    """



    def do_set_wavelength(self, wavelength):
        print('setting wavelength...')
        print('')

        #print('Coefficients are %s %s %s' % (self._doubleA, self._doubleB, self._doubleC))
        #print('#3 Motor current: {}'.format(self.get_motor_current()))
        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)

        # Step 1: Get the actual motor position

        #print('Getting motor position')

        current_motor_pos = self.get_motor_position()

        # Step 2: Get the motor offset

        self._offset = self.get_offset()
        #print('Motor offset is %s' % self._offset)

        # Step 3: Convert the desired wavelength into a position
        # Check sign of position-to-wavelength
        pos0 = self._doubleA*(0.0)**2.0 + self._doubleB*0.0 + self._doubleC
        pos5000 = self._doubleA*(5000.0)**2.0 + self._doubleB*5000.0 + self._doubleC
        #    logging.error(__name__ + ' Sacher wavelength calibration polynomials indicated a wrong wavelength direction')
        # If that's OK, use the quadratic formula to calculate the roots
        b2a = -1.0*self._doubleB/(2.0*self._doubleA)
        sqrtarg = self._doubleB**2.0/(4.0*self._doubleA**2.0) - (self._doubleC - wavelength)/self._doubleA
        # print('wut da fuuuu')
        # print(b2a)
        # print(sqrtarg)
        # print(pos0)
        # print(pos5000)
        if sqrtarg < 0.0:
            logging.error(__name__ + ' Negative value under square root sign -- something is wrong')
        if pos0 > pos5000:
            # Take the + square root solution
            x = b2a - np.sqrt(sqrtarg)
        elif pos0 < pos5000:
            x = b2a + np.sqrt(sqrtarg)
            #x is what the motor position should be

        #print('Position is %s' % x)

        wavelength_to_pos = int(round(x))
        # Step 4: Calculate difference between the output position and the stored offset

        #print('Step 4...')

        diff_wavelength_offset = wavelength_to_pos - int(self._offset)

        #print('Diff wavelength offset %s' % diff_wavelength_offset)

        # Step 5: If HPM is activated and the wavelength position is lower, overshoot
        # the movement by 10,000 steps

        #print('Step 5...')
        #print('#4 Motor current: {}'.format(self.get_motor_current()))

        if 1==2:
            print('uh-oh')
        # if self._HPM and diff_wavelength_offset < 0:
        #
        #     print('Overshooting by 10000')
        #
        #     self.set_target_position(diff_wavelength_offset - 10000, False, True)
        #     # Step 6: Set the real target position
        #
        #     """
        #     HEY LOOK EVERYONE RIGHT ABOVE HERE THIS IS THE STUPID THING THAT'S NOT WORKING!
        #     """
        #
        #     #print('Step 6a... diff wavelength')
        #
        #     self.set_target_position(10000, False, True)
        else:

            #print('Step 6b... diff wavelength')

            #self.set_target_position(diff_wavelength_offset, False, True)
            """WRONG"""

            self.set_target_position(wavelength_to_pos, True, True)
            """this is the real shit right here

            I need to set the absolute position to true
            """

            #self.set_target_position(10000, False, True)


        # Step 7: Get the actual motor position
        new_motor_pos = self.get_motor_position()

        #print('New motor position is %s' % new_motor_pos)
        #print('new offset is %s' % (new_motor_pos-current_motor_pos+self._offset))

        self.set_new_offset(new_motor_pos-current_motor_pos+self._offset)

        # Step 8, get and print current wavelength

        #print('Current wavelength is %.3f' % self.do_get_wavelength())

        #print('setting wavelength done')
        return

    """
    Not sure what this is doing yet
    """



    def is_open(self):
        return self._is_open

    """
    Not sure what this is doing yet
    """



    def clear_fault(self):
        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        ret = eposlib.VCS_ClearFault(self._keyhandle,nodeID,ctypes.byref(buf))
        print('clear fault buf %s, ret %s' % (buf, ret))
        if ret == 0:
            errbuf = ctypes.create_string_buffer(64)
            eposlib.VCS_GetErrorInfo(buf, errbuf, WORD(64))
            raise ValueError(errbuf.value)

    """
    Not sure what this is doing yet
    """



    def initialize(self):
        nodeID = ctypes.wintypes.WORD(0)
        buf = ctypes.wintypes.DWORD(0)
        BaudRate = DWORD(38400)
        Timeout = DWORD(100)
        ret = eposlib.VCS_SetProtocolStackSettings(self._keyhandle,BaudRate,Timeout,ctypes.byref(buf))
        #print 'set protocol buf %s ret %s' % (buf, ret)
        if ret == 0:
            errbuf = ctypes.create_string_buffer(64)
            #eposlib.VCS_GetErrorInfo(buf, errbuf, WORD(64))
            raise ValueError(errbuf.value)

        buf = ctypes.wintypes.DWORD(0)
        ret = eposlib.VCS_ClearFault(self._keyhandle,nodeID,ctypes.byref(buf))
        #print 'clear fault buf %s, ret %s' % (buf, ret)
        if ret == 0:
            errbuf = ctypes.create_string_buffer(64)
            eposlib.VCS_GetErrorInfo(buf, errbuf, WORD(64))
            raise ValueError(errbuf.value)
        buf = ctypes.wintypes.DWORD(0)
        plsenabled = ctypes.wintypes.DWORD(0)
        ret = eposlib.VCS_GetEnableState(self._keyhandle,nodeID,ctypes.byref(plsenabled),ctypes.byref(buf))
        #print 'get enable state buf %s ret %s and en %s' % (buf, ret, plsenabled)
        if ret == 0:
            errbuf = ctypes.create_string_buffer(64)
            eposlib.VCS_GetErrorInfo(buf, errbuf, WORD(64))
            raise ValueError(errbuf.value)

        if int(plsenabled.value) != 0:
            logging.warning(__name__ + ' EPOS motor enabled, disabling before proceeding.')
            ret = eposlib.VCS_SetDisableState(self._keyhandle,nodeID,ctypes.byref(buf))
            if int(ret) != 0:
                logging.warning(__name__ + ' EPOS motor successfully disabled, proceeding')
            else:
                logging.error(__name__ + ' EPOS motor was not successfully disabled!')
        buf = ctypes.wintypes.DWORD(0)
        Counts = WORD(512) # incremental encoder counts in pulses per turn
        PositionSensorType = WORD(4)
        ret = eposlib.VCS_SetEncoderParameter(self._keyhandle,nodeID,Counts,PositionSensorType,ctypes.byref(buf))

##        if ret == int(0):
##            print 'errr'
##            errbuf = ctypes.create_string_buffer(64)
##            print 'sending'
##            eposlib.VCS_GetErrorInfo.restype = ctypes.wintypes.BOOL
##            print 'boolerrorinfo'
##            eposlib.VCS_GetErrorInfo.argtypes = [ctypes.wintypes.DWORD, ctypes.c_char_p, ctypes.wintypes.WORD]
##            print 'arg'
##
##            ret = eposlib.VCS_GetErrorInfo(buf, ctypes.byref(errbuf), WORD(64))
##            print 'err'
##            raise ValueError(errbuf.value)
        # For some reason, it appears normal in the LabVIEW code that this
        # function actually returns an error, i.e. the return value is zero
        # and the buffer has a non-zero error code in it; the LabVIEW code
        # doesn't check it.
        # Also, it appears that in the 2005 version of this DLL, the function
        # VCS_GetErrorInfo doesn't exist!

        # Get operation mode, check if it's 1 -- this is "profile position mode"
        buf = ctypes.wintypes.DWORD(0)
        pMode = ctypes.pointer(ctypes.c_int8())
        eposlib.VCS_GetOperationMode.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.POINTER(ctypes.c_int8), ctypes.POINTER(ctypes.wintypes.DWORD)]
        eposlib.VCS_GetOperationMode.restype = ctypes.wintypes.BOOL
        ret = eposlib.VCS_GetOperationMode(self._keyhandle, nodeID, pMode, ctypes.byref(buf))
        # if mode is not 1, make it 1
        if pMode.contents.value != 1:
            eposlib.VCS_SetOperationMode.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.c_int8, ctypes.POINTER(ctypes.wintypes.DWORD)]
            eposlib.VCS_SetOperationMode.restype = ctypes.wintypes.BOOL
            pMode_setting = ctypes.c_int8(1)
            ret = eposlib.VCS_SetOperationMode(self._keyhandle, nodeID, pMode_setting, ctypes.byref(buf))
        eposlib.VCS_GetPositionProfile.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        eposlib.VCS_GetPositionProfile.restype = ctypes.wintypes.BOOL
        pProfileVelocity = ctypes.pointer(ctypes.wintypes.DWORD())
        pProfileAcceleration = ctypes.pointer(ctypes.wintypes.DWORD())
        pProfileDeceleration = ctypes.pointer(ctypes.wintypes.DWORD())

        ret = eposlib.VCS_GetPositionProfile(self._keyhandle, nodeID, pProfileVelocity, pProfileAcceleration, pProfileDeceleration,ctypes.byref(buf))

        print(pProfileVelocity.contents.value, pProfileAcceleration.contents.value, pProfileDeceleration.contents.value)

        if (int(pProfileVelocity.contents.value) > int(11400) or int(pProfileAcceleration.contents.value) > int(60000) or int(pProfileDeceleration.contents.value) > int(60000)):
            eposlib.VCS_GetPositionProfile.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD)]
            eposlib.VCS_GetPositionProfile.restype = ctypes.wintypes.BOOL
            pProfileVelocity = ctypes.wintypes.DWORD(429)
            pProfileAcceleration = ctypes.wintypes.DWORD(429)
            pProfileDeceleration = ctypes.wintypes.DWORD(429)
            logging.warning(__name__ + ' GetPositionProfile out of bounds, resetting...')
            ret = eposlib.VCS_SetPositionProfile(self._keyhandle, nodeID, pProfileVelocity, pProfileAcceleration, pProfileDeceleration,ctypes.byref(buf))

        # Now get the motor position (stored position offset)
        # from the device's "homposition" object

        self._offset = self.get_offset()

        # Now read the stored 'calculation parameters'
        eposlib.VCS_GetObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        eposlib.VCS_GetObject.restype = ctypes.wintypes.BOOL

        # More hardcoded values
        StoredPositionObject = ctypes.wintypes.WORD(8204)
        StoredPositionObjectSubindex = ctypes.c_uint8(1)
        StoredPositionNbBytesToRead = ctypes.wintypes.DWORD(4)
        ObjectData = ctypes.c_void_p()
        ObjectDataArray = (ctypes.c_uint32*1)()
        ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_uint32))
        StoredPositionNbBytesRead = ctypes.pointer(ctypes.wintypes.DWORD(0))
        ret = eposlib.VCS_GetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToRead, StoredPositionNbBytesRead, ctypes.byref(buf))
        # Cast the object data to uint32
        CastedObjectData = ctypes.cast(ObjectData, ctypes.POINTER(ctypes.c_uint32))

        self._coefA = CastedObjectData[0]
        eposlib.VCS_GetObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        eposlib.VCS_GetObject.restype = ctypes.wintypes.BOOL

        # Get coefficient B
        StoredPositionObject = ctypes.wintypes.WORD(8204)
        StoredPositionObjectSubindex = ctypes.c_uint8(2)
        StoredPositionNbBytesToRead = ctypes.wintypes.DWORD(4)
        ObjectData = ctypes.c_void_p()
        ObjectDataArray = (ctypes.c_uint32*1)()
        ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_uint32))
        StoredPositionNbBytesRead = ctypes.pointer(ctypes.wintypes.DWORD(0))
        ret = eposlib.VCS_GetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToRead, StoredPositionNbBytesRead, ctypes.byref(buf))
        # Cast the object data to uint32
        CastedObjectData = ctypes.cast(ObjectData, ctypes.POINTER(ctypes.c_uint32))

        self._coefB = CastedObjectData[0]
        eposlib.VCS_GetObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        eposlib.VCS_GetObject.restype = ctypes.wintypes.BOOL

        # These are hardcoded values I got from the LabVIEW program -- I don't think
        # any documentation exists on particular object indices
        StoredPositionObject = ctypes.wintypes.WORD(8204)
        StoredPositionObjectSubindex = ctypes.c_uint8(3)
        StoredPositionNbBytesToRead = ctypes.wintypes.DWORD(4)
        ObjectData = ctypes.c_void_p()
        ObjectDataArray = (ctypes.c_uint32*1)()
        ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_uint32))
        StoredPositionNbBytesRead = ctypes.pointer(ctypes.wintypes.DWORD(0))
        ret = eposlib.VCS_GetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToRead, StoredPositionNbBytesRead, ctypes.byref(buf))
        # Cast the object data to uint32
        CastedObjectData = ctypes.cast(ObjectData, ctypes.POINTER(ctypes.c_uint32))

        self._coefC = CastedObjectData[0]

        # Get coefficient D
        eposlib.VCS_GetObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.WORD, ctypes.wintypes.WORD, ctypes.c_uint8, ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
        eposlib.VCS_GetObject.restype = ctypes.wintypes.BOOL

        # These are hardcoded values I got from the LabVIEW program -- I don't think
        # any documentation exists on particular object indices
        StoredPositionObject = ctypes.wintypes.WORD(8204)
        StoredPositionObjectSubindex = ctypes.c_uint8(4)
        StoredPositionNbBytesToRead = ctypes.wintypes.DWORD(4)
        ObjectData = ctypes.c_void_p()
        ObjectDataArray = (ctypes.c_uint32*1)()
        ObjectData = ctypes.cast(ObjectDataArray, ctypes.POINTER(ctypes.c_uint32))
        StoredPositionNbBytesRead = ctypes.pointer(ctypes.wintypes.DWORD(0))
        ret = eposlib.VCS_GetObject(self._keyhandle, nodeID, StoredPositionObject, StoredPositionObjectSubindex, ObjectData, StoredPositionNbBytesToRead, StoredPositionNbBytesRead, ctypes.byref(buf))
        # Cast the object data to uint32
        CastedObjectData = ctypes.cast(ObjectData, ctypes.POINTER(ctypes.c_uint32))

        self._coefD = CastedObjectData[0]
        #print 'coefficients are %s %s %s %s' % (self._coefA, self._coefB, self._coefC, self._coefD)
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
        print('Current wavelength: %.3f nm' % self._currentwl)
        print('initializing done')
        return True

    """
    Not sure what this is doing yet
    """

"""
Also we're done with the Sacher_EPOS() class at this point
"""




if __name__ == '__main__':
    epos = Sacher_EPOS(None, b'COM3')
    #epos.set_coeffs(8.34529e-12,8.49218e-5,1081.92,10840,11860)

    #epos.do_get_wavelength()

    #print('#1 Motor current: {}'.format(epos.get_motor_current()))
    # epos.do_get_wavelength()
    # print('motor position is...')
    # current_pos = epos.get_motor_position()
    # print('current position is {}'.format(current_pos))
    # new_pos = current_pos + 10000
    # epos.set_target_position(new_pos, True, True)
    # print(epos.get_motor_position())
    #print('#2 Motor current: {}'.format(epos.get_motor_current()))

    #epos.find_home()
    #epos.restore()
    #time.sleep(7)

    epos.do_set_wavelength(1151.5)

    #epos.do_get_wavelength()
    print('Motor current: {}'.format(epos.get_motor_current()))
    print('Motor position: {}'.format(epos.get_motor_position()))

"""
OTHER MISC. NOTES:

increasing wavelength:
causes the square to rotate left
causes base to move to the left when square is stuck in
causes screw to loosen
causes large gold base to tighten

decreasing wavelength:
there's an overshoot when lowering wavelength
causes the square to rotate right
causes base to move to the right when square is stuck in
causes screw to tighten
causes large gold base to loosen, and also unplug the motor

Also you don't need to explicitly run epos.initialize() because there's an __init__ function which contains epos.initialize()
"""

#womp the end
