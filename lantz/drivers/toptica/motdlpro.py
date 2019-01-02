from lantz.driver import Driver
from lantz import Feat, Action
import serial
import numpy as np
import struct
import time
import enum

class MotDLpro(Driver):

    tmcl_struct = struct.Struct('>BBBBiB')

    _STATUSCODES = {
        100 : "Succesfully executed, no error",
        101 : "Command loaded into TMCL program EEPROM",
          1 : "Wrong Checksum",
          2 : "Invalid command",
          3 : "Wrong type",
          4 : "Invalid value",
          5 : "Configuration EEPROM locked",
          6 : "Command not available",
    }

    TMCL_OK_STATUS = {
        100, 101
    }

    _STAT_OK = 100

    class CMDS(enum.Enum):
        ROR = 1
        ROL = 2
        MST = 3
        MVP = 4
        SAP = 5
        GAP = 6
        STAP = 7
        RSAP = 8
        SGP = 9
        GGP = 10
        STGP = 11
        RSGP = 12
        RFS = 13
        SIO = 14
        GIO = 15
        CALC = 19
        COMP = 20
        JC = 21
        JA = 22
        CSUB = 23
        RSUB = 24
        EI = 25
        DI = 26
        WAIT = 27
        STOP = 28
        SCO = 30
        GCO = 31
        CCO = 32
        CALCX = 33
        AAP = 34
        AGP = 35
        VECT = 37
        RETI = 38
        ACO = 39

    _COMMAND_NUMBERS = {
        1 : "ROR",    2 : "ROL",    3 : "MST",
        4 : "MVP",    5 : "SAP",    6 : "GAP",
        7 : "STAP",   8 : "RSAP",   9 : "SGP",
        10 : "GGP",   11 : "STGP",  12 : "RSGP",
        13 : "RFS",   14 : "SIO",   15 : "GIO",
        19 : "CALC",  20 : "COMP",  21 : "JC",
        22 : "JA",    23 : "CSUB",  24 : "RSUB",
        25 : "EI",    26 : "DI",    27 : "WAIT",
        28 : "STOP",  30 : "SCO",   31 : "GCO",
        32 : "CCO",   33 : "CALCX", 34 : "AAP",
        35 : "AGP",   37 : "VECT",  38 : "RETI",
        39 : "ACO",
    }

    _NUMBER_COMMANDS = dict((v, k) for k, v in _COMMAND_NUMBERS.items())

    _INTERRUPT_VECTORS = {
        0 : "Timer 0",
        1 : "Timer 1",
        2 : "Timer 2",
        3 : "Target position reached",
       15 : "stallGuard",
       21 : "Deviation",
       27 : "Left stop switch",
       28 : "Right stop switch",
       39 : "Input change 0",
       40 : "Input change 1",
      255 : "Global interrupts",
    }

    _CMD_MVP_TYPES = {
        'ABS' : 0,
        'REL' : 1,
        'COORDS' : 2,
    }

    _CMD_RFS_TYPES = {
        'START' : 0,
        'STOP' : 1,
        'STATUS' : 2,
    }

    TR_24s = [(-2**23+1, 2**23)]
    TR_32u = [(0, 2**32)]
    TR_32s = [(-2**31, 2**31)]
    TR_16u = [(0, 2**16)]
    TR_12s = [(-2**11+1, 2**11)]
    TR_12u = [(0, 2**12)]
    TR_11u = [(0, 2**11)]
    TR_10u = [(0, 2**10)]
    TR_8u = [(0, 2**8)]
    TR_7s = [(-2**6, 2**6)]
    TR_5u = [(0, 2**5)]
    TR_1u = [(0, 2**1)]
    TR_m3 = [(0, 3)]
    TR_m4 = [(0, 4)]
    TR_m9 = [(0, 9)]
    TR_m12 = [(0, 14)]
    TR_m14 = [(0, 14)]
    TR_m16 = [(0, 16)]

    TR_xCHP0 = [(-3, 13)]
    TR_xCHP1 = [(0, 1), (2, 16)]
    TR_xSE0 = [(1, 4)]
    TR_xRFS0 = [(1, 9)]
    TR_xRFS1 = [(0, 8388307)]
    TR_xPWR0 = [(1, 2**16)]
    TR_xRND0 = [(0, 2**31)]

    T_R = 4
    T_W = 2
    T_E = 1
    T_RW = T_R + T_W
    T_RWE = T_RW + T_E

    _AXIS_PARAMETER = {
         0 : ("target position", TR_24s, T_RW),
         1 : ("actual position", TR_24s, T_RW),
         2 : ("target speed", TR_12s, T_RW),
         3 : ("actual speed", TR_12s, T_RW),
         4 : ("max positioning speed", TR_11u, T_RWE),
         5 : ("max acceleration", TR_11u, T_RWE),
         6 : ("abs max current", TR_8u, T_RWE),
         7 : ("standby current", TR_8u, T_RWE),
         8 : ("target pos reached", TR_1u, T_R),
         9 : ("ref switch status", TR_1u, T_R),
        10 : ("right limit switch status", TR_1u, T_R),
        11 : ("left limit switch status", TR_1u, T_R),
        12 : ("right limit switch disable", TR_1u, T_RWE),
        13 : ("left limit switch disable", TR_1u, T_RWE),
       130 : ("minimum speed", TR_11u, T_RWE),
       135 : ("actual acceleration", TR_11u, T_R),
       138 : ("ramp mode", TR_m3, T_RWE),
       140 : ("microstep resolution", TR_m9, T_RWE),
       141 : ("ref switch tolerance", TR_12u, T_RW),
       149 : ("soft stop flag", TR_1u, T_RWE),
       153 : ("ramp divisor", TR_m14, T_RWE),
       154 : ("pulse divisor", TR_m14, T_RWE),
       160 : ("step interpolation enable", TR_1u, T_RW),
       161 : ("double step enable", TR_1u, T_RW),
       162 : ("chopper blank time", TR_m4, T_RW),
       163 : ("chopper mode", TR_1u, T_RW),
       164 : ("chopper hysteresis dec", TR_m4, T_RW),
       165 : ("chopper hysteresis end", TR_xCHP0, T_RW),
       166 : ("chopper hysteresis start", TR_m9, T_RW),
       167 : ("chopper off time", TR_xCHP1, T_RW),
       168 : ("smartEnergy min current", TR_1u, T_RW),
       169 : ("smartEnergy current downstep", TR_m4, T_RW),
       170 : ("smartEnergy hysteresis", TR_m16, T_RW),
       171 : ("smartEnergy current upstep", TR_xSE0, T_RW),
       172 : ("smartEnergy hysteresis start", TR_m16, T_RW),
       173 : ("stallGuard2 filter enable", TR_1u, T_RW),
       174 : ("stallGuard2 threshold", TR_7s, T_RW),
       175 : ("slope control high side", TR_m4, T_RW),
       176 : ("slope control low side", TR_m4, T_RW),
       177 : ("short protection disable", TR_1u, T_RW),
       178 : ("short detection timer", TR_m4, T_RW),
       179 : ("Vsense", TR_1u, T_RW),
       180 : ("smartEnergy actual current", TR_5u, T_RW),
       181 : ("stop on stall", TR_11u, T_RW),
       182 : ("smartEnergy threshold speed", TR_11u, T_RW),
       183 : ("smartEnergy slow run current", TR_8u, T_RW),
       193 : ("ref. search mode", TR_xRFS0, T_RWE),
       194 : ("ref. search speed", TR_11u, T_RWE),
       195 : ("ref. switch speed", TR_11u, T_RWE),
       196 : ("distance end switches", TR_xRFS1, T_R),
       204 : ("freewheeling", TR_16u, T_RWE),
       206 : ("actual load value", TR_10u, T_R),
       208 : ("TMC262 errorflags", TR_8u, T_R),
       209 : ("encoder pos", TR_24s, T_RW),
       210 : ("encoder prescaler", TR_16u, T_RWE), # that one isnt really correct
       212 : ("encoder max deviation", TR_16u, T_RWE),
       214 : ("power down delay", TR_xPWR0, T_RWE),
    }

    _SINGLE_AXIS_PARAMETERS = [140] + list(range(160, 184))

    _GLOBAL_PARAMETER = {
        (0, 64) : ("EEPROM magic", TR_8u, T_RWE),
        (0, 65) : ("RS485 baud rate", TR_m12, T_RWE),
        (0, 66) : ("serial address", TR_8u, T_RWE),
        (0, 73) : ("EEPROM lock flag", TR_1u, T_RWE),
        (0, 75) : ("telegram pause time", TR_8u, T_RWE),
        (0, 76) : ("serial host adress", TR_8u, T_RWE),
        (0, 77) : ("auto start mode", TR_1u, T_RWE),
        (0, 81) : ("TMCL code protect", TR_m4, T_RWE),
        # (0, 84) : ("coordinate storage", TR_1u, T_RWE), # wrong type?
        (0, 128) : ("TMCL application status", TR_m3, T_R),
        (0, 129) : ("download mode", TR_1u, T_R),
        (0, 130) : ("TMCL program counter", TR_32u, T_R),
        (0, 132) : ("tick timer", TR_32u, T_RW),
        # (0, 133) : ("random number", TR_xRND0, T_R), # wrong type?
        (3, 0) : ("Timer0 period", TR_32u, T_RWE),
        (3, 1) : ("Timer1 period", TR_32u, T_RWE),
        (3, 2) : ("Timer2 period", TR_32u, T_RWE),
        (3, 39) : ("Input0 edge type", TR_m4, T_RWE),
        (3, 40) : ("Input0 edge type", TR_m4, T_RWE),
    }

    def __init__(self, address, target):
        self.address = address
        self.target = target
        return

    def initialize(self):
        self._serial = serial.Serial(
            port=self.address,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,
        )

        self.init_motor_parameters()
        self.get_calibration_data()
        return

    def set_sap_for_all_motors(self, sap_type, sap_value):
        for mot in range(3):
            self.send_instruction(5, sap_type, mot, sap_value)
        return

    def init_motor_parameters(self):
        self.set_sap_for_all_motors(4, 1000)    # set speed to 1000
        self.set_sap_for_all_motors(5, 100)     # set max accel to 100
        self.set_sap_for_all_motors(6, 42)      # set maxcurrentl to 250 - this is in units of 255 = 100%; I think the max current is 1.5 A so this is ~250 mA.
        self.set_sap_for_all_motors(7, 0)       # set standby current to 0
        self.set_sap_for_all_motors(12, 1)      # disable right limit switch
        self.set_sap_for_all_motors(13, 0)      # enable left limit switch
        self.set_sap_for_all_motors(140, 4)     # set microstep resolution to 16 microsteps (parameter value = 4)

        # vvv this was commented
        # self.set_sap_for_all_motors(143, 1)     # set rest current to approximately 12%

        self.set_sap_for_all_motors(153, 7)     # set ramp to 7
        self.set_sap_for_all_motors(154, 3)     # set pulse to 3
        self.set_sap_for_all_motors(194, 1000)  # set reference speed to 1000
        self.set_sap_for_all_motors(203, 100)   # set the mixed decay threshold to 100

        # vvv this had a value of 30
        self.set_sap_for_all_motors(204, 10)    # set FreeWheelTime to 10

        for idx in range(6):
            self.send_instruction(14, typ=idx, mot=0, val=0)
        return

    # def get_calibration_data(self):
    #     # hardcode for now - need to change when getting new laser
    #     self.wavelength_limits = (1064.86, 1144.51)
    #     self.p_coeffs = (-1.15278e6, 64.5135, 0.962788)
    #     self.backlash_coeff = 5035
    #     return

    def toptica_integer_to_double(self, ints):
        # this is how DC got the hardcoded values in the commented get_calibration_data
        return struct.unpack('d', struct.pack('ii', *reversed(ints)))[0]

    def get_calibration_data(self):
        params = self.get_global_parameters()
        min_wl = self.toptica_integer_to_double(params[22:24])
        max_wl = self.toptica_integer_to_double(params[24:26])
        p2 = self.toptica_integer_to_double(params[26:28])
        p1 = self.toptica_integer_to_double(params[28:30])
        p0 = self.toptica_integer_to_double(params[30:32])
        backlash = params[32]
        self.wavelength_limits = (min_wl, max_wl)
        self.p_coeffs = p2, p1, p0
        self.backlash_coeff = backlash
        self.step_margin = 1000
        self.step_limits = self.wavelength_to_step(min_wl), self.wavelength_to_step(max_wl)
        return

    def checksum(self, buffer):
        chk = np.sum(buffer, dtype=np.uint8)
        return chk

    def send_instruction(self, n, typ=0, mot=0, val=0):
        """
        Sends one instruction, and return the reply.
        n (0<=int<=255): instruction ID
        typ (0<=int<=255): instruction type
        mot (0<=int<=255): motor/bank number
        val (0<=int<2**32): value to send
        return (0<=int<2**32): value of the reply (if status is good)
        raises:
            IOError: if problem with sending/receiving data over the serial port
            TMCLError: if status if bad

        IMPORTANT: TO BE COMPATIBLE WITH TOPTICA'S CODE, IF YOU LOOK IN THE
        GENERATE/SEND COMMAND VI, FOR SOME REASON THE AUTHOR TAKES THE INTEGER
        2 AND SUBTRACTS THE MOTOR NUMBER FROM IT. SO MOTOR 0 IN THE TOPTICA
        VI IS ACTUALLY MOTOR 2 IN THE TMCL CODE.
        """

        mot = 2 - mot
        data = [
            self.target,
            n,
            typ,
            mot,
            val,
            0,
        ]
        msg = np.frombuffer(self.tmcl_struct.pack(*data), dtype=np.uint8).tolist()
        msg[-1] = self.checksum(msg)
        self._serial.write(msg)
        self._serial.flush()
        while True:
            ret = self._serial.read(9)
            if len(ret) < 9:
                # could not read 9 bytes
                pass
            *retdata, chk = self.tmcl_struct.unpack(ret)
            if self.checksum(np.frombuffer(ret, dtype=np.uint8)[:-1]) == chk:
                ra, rt, status, rn, rval = retdata
                if self.target and self.target != rt: # target = 0 means any device
                    pass
                if rn != n:
                    continue
                if status not in self.TMCL_OK_STATUS:
                    raise TMCLError(status, rval)
            else:
                raise TMCLError
            return rval

    def wavelength_to_step(self, wl):
        if not self.wavelength_limits[0] <= wl <= self.wavelength_limits[1]:
            raise ValueError('wavelength {} out of operation range ({}, {})'.format(wl, *self.wavelength_limits))
        p0, p1, p2 = self.p_coeffs
        step = p0 + p1 * wl + p2 * wl * wl
        return int(step)

    def step_to_wavelength(self, step):
        p0, p1, p2 = self.p_coeffs
        wl = (-p1 + np.sqrt(p1 * p1 - 4 * p2 * (p0 - step))) / (2 * p2)
        if not self.wavelength_limits[0] <= wl <= self.wavelength_limits[1]:
            raise ValueError('wavelength {} out of operation range ({}, {})'.format(wl, *self.wavelength_limits))
        return wl

    @Feat(limits=(0, 300000))
    def position(self):
        return int(self.send_instruction(6, typ=1, mot=0, val=0))

    @position.setter
    def position(self, step):
        step = int(step)
        ret = self.send_instruction(4, typ=0, mot=0, val=step)
        time.sleep(0.25)
        now = time.time()
        while time.time() < (now + 10.0):
            if step == self.position:
                break
            else:
                time.sleep(0.1)
        else:
            raise MotDLproError('timeout, needed to get to {}, stopped at {}'.format(step, self.position))
        return

    @Feat()
    def wavelength(self):
        return self.step_to_wavelength(self.position)

    @wavelength.setter
    def wavelength(self, wl):
        target_position = self.wavelength_to_step(wl)
        current_position = self.position
        if current_position > target_position:
            # if we make a movement to the left, set the desired step
            # to beyond by the "backlash" calibration parameter
            target_position -= self.backlash_coeff
        self.position = target_position

    @Action()
    def precision_move(self, target_position, offset=10000, from_high=False):
        current_position = self.position
        offset = -offset if from_high else offset
        lower, upper = self.step_limits
        args = [
            current_position + offset,
            lower - self.step_margin,
            upper + self.step_margin,
        ]
        offset_position = np.clip(*args)
        status = True
        try:
            self.position = offset_position
            time.sleep(0.25)
            self.position = target_position
        except MotDLproError:
            status = False
        return status

    # @Action()
    # def precision_move(self, step, direction=1):
    #     if direction == 1:
    #         if step > 10000:
    #             self.position = step - 10000
    #         else:
    #             self.position = 0
    #     else:
    #         if step < 172000:
    #             self.position = step + 10000
    #         else:
    #             self.position = 172000 + 10000
    #     self.position = step
    #     return

    @Action()
    def reference_search(self):
        self.send_instruction(13, typ=0, mot=0, val=0)

        now = time.time()
        while time.time() < (now + 45.0):
            ret = self.send_instruction(13, typ=2, mot=0, val=0)
            if not ret:
                break
        else:
            print('timeout')
            self.send_instruction(13, typ=2, mot=0, val=0)
        return

    @Action()
    def calibrate(self, steps=1000):
        lower, upper = self.wavelength_limits
        _positions = np.linspace(lower, upper, steps)
        frequencies = list()
        wavelengths = list()

        for from_high in [False, True]:
            if from_high:
                positions = _positions[::-1]
            for position in positions:
                self.precision_move(position, from_high=from_high)
                frequencies.append(wavemeter.frequency)
                wavelengths.append(wavemeter.wavelength)

        frequencies = np.array(frequencies)
        wavelengths = np.array(wavelengths)

        n = len(positions)
        # we will create the calibration fit from the lower-to-upper motor direction
        p = np.polyfit(wavelength[:n], _positions, deg=2)

        def motor_pos(wl):
            return p[0] * np.square(wl) + p[1] * wl + p[2]

        fit_positions = motor_pos(wavelengths[n:])
        backlash = np.mean(fit_positions - _positions[::-1])

        wl_max = np.max(wavelengths[:n])
        wl_min = np.min(wavelengths[n:])

        return wl_min, wl_max, p[2], p[1], p[0], backlash

    def restore_global_parameters(self):
        parameters = list()
        for idx in range(34):
            offset = 20 + idx
            self.send_instruction(12, typ=offset, mot=0, val=0)
            ret = self.send_instruction(10, typ=offset, mot=0, val=0)
            parameters.append(ret)
        return parameters

    def get_global_parameters(self):
        parameters = list()
        for idx in range(34):
            offset = 20 + idx
            ret = self.send_instruction(10, typ=offset, mot=0, val=0)
            parameters.append(ret)
        return parameters


class TMCLError(Exception):
    pass

class MotDLproError(Exception):
    pass

def test():
    mot = MotDLpro('COM7', 1)
    mot.initialize()
    mot.restore_global_parameters()
    print(mot.wavelength)
    mot.wavelength += 2
    print(mot.wavelength)
    mot.wavelength -= 2
    print(mot.wavelength)

if __name__ == '__main__':
    test()
