import ctypes as ct

from lantz import Driver, Feat, Action
from lantz.errors import InstrumentError
from lantz.foreign import LibraryDriver
import time


class TLB6700(LibraryDriver):
    LIBRARY_NAME = "UsbDll"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initialize()
        self.dev_id = self.get_id()



    def initialize(self):
        answer = self.lib.newp_usb_init_system()
        if answer == 0:
            return True
        else:
            raise Exception("Couldn't initialize the device")

    # Get the device information, parse the answer to get the USB
    # number which is the identification of the device to be used
    # later.
    # Note: Needs to be modified for mutliple devices!!!
    def get_id(self):
        buf = ct.create_string_buffer(64)
        buf_address = ct.addressof(buf)
        success = self.lib.newp_usb_get_device_info(buf_address)
        if success == 0:
            buf_value = buf.value
            dev_id = [x.strip() for x in buf_value.decode("utf-8").split(",")]
            return int(dev_id[0])
        else:
            raise Exception("Couldn't obtain the device id")

    def check_error(self):
        error = self.query("ERRSTR?")
        code, message = [x.strip('"') for x in error.split(",")]
        if code == '0':
            return None
        else:
            raise Exception(message)

    def check_success(self, returned):
        if returned == "OK":
            return True
        else:
            self.check_error()

    @Feat
    def idn(self):
        buf = ct.create_string_buffer(64)
        buf_address = ct.addressof(buf)
        success = self.lib.newp_usb_get_device_info(buf_address)
        if success == 0:
            return buf.value.decode("utf-8").replace(r"\r\n;","")
        else:
            raise Exception("No device found!")

    # Terminate the connection
    def uninitialize(self):
        answer = self.lib.newp_usb_uninit_system()
        if answer == 0:
            return True
        else:
            raise Exception("Device connection did not terminate correctly!")

    # This function is built only to clear the device buffer.
    # It repeatedly asks for an answer until it doesn't get
    # anything, thus clears the device buffer for the next
    # inquiry.
    def clear_buffer(self):
        buf = ct.create_string_buffer(64)
        buf_address = ct.addressof(buf)
        length = ct.c_ulong(0)
        success = 0
        while success == 0:
            time.sleep(0.01)
            success = self.lib.newp_usb_get_ascii(ct.c_long(self.dev_id), buf_address, ct.sizeof(buf), ct.byref(length))

    # Only write a command to the device, by asking for an answer
    # from the device we empty the device memory to be used later
    # Returns True if the writing is succesfull otherwise returns
    # false.
    def write(self, command):
        p = ct.create_string_buffer(command.encode())
        success = self.lib.newp_usb_send_ascii(ct.c_long(self.dev_id), p, len(command))
        self.clear_buffer()
        if success == 0:
            return True
        else:
            return False

    # This function is essentially the same as before however it
    # returns the value stored in the computer buffer.
    def query(self, command):
        buf = ct.create_string_buffer(64)
        buf_address = ct.addressof(buf)
        length = ct.c_ulong(0)
        self.clear_buffer()
        p = ct.create_string_buffer(command.encode())
        self.lib.newp_usb_send_ascii(ct.c_long(self.dev_id), p, ct.c_ulong(len(command)))
        time.sleep(0.01)
        success = self.lib.newp_usb_get_ascii(ct.c_long(self.dev_id), buf_address, ct.sizeof(buf), ct.byref(length))
        if success == 0:
            buf_value = buf.value.decode("utf-8")
            answer = [x.strip() for x in buf_value.split("\r\n")][0]
            return answer
        else:
            return False

    def finalize(self):
        self.uninitialize()
        self.dev_id = None

    @Feat(units="nm", limits=(1035,1075))
    def target_wavelength(self):
        """Target Wavelength """
        return float(self.query("SOUR:WAVE?"))*1e-9

    @target_wavelength.setter
    def target_wavelength(self, twl):
        """Target Wavelength"""
        self.check_success(self.write("SOUR:WAVE {:.2f}".format(twl)))

    @Feat(units = "nm")
    def measured_wavelength(self):
        """Measured Wavelength"""
        return float(self.query("SENS:WAVE"))*1e-9

    @Feat(values={True: 1, False: 0})
    def laser_on(self):
        """Laser State"""
        return float(self.query("OUTP:STAT?"))

    @laser_on.setter
    def laser_on(self, state):
        """Laser State"""
        self.check_success(self.write("OUTP:STAT {:d}".format(state)))

    @Feat(values={True: 1, False: 0})
    def wavelength_track(self):
        """Lambda Track"""
        return float(self.query("OUTP:TRAC?"))

    @wavelength_track.setter
    def wavelength_track(self, state):
        """Lambda Track"""
        self.check_success(self.write("OUTP:TRAC {:d}".format(state)))

    @Feat(units = "mA")
    def measured_current(self):
        return float(self.query("SENS:CURR:DIOD"))

    @Feat(units = "mW")
    def measured_power(self):
        return float(self.query("SENS:POW:DIOD"))


    @Feat(units="mW", limits=(0, 18.1))
    def target_power(self):
        return float(self.query("SOUR:POW:DIOD?"))

    @target_power.setter
    def target_power(self, power):
        self.check_success(self.write("SOUR:POW:DIOD {:.2f}".format(power)))

    @Feat(values={"Current": 0, "Power": 1})
    def power_mode(self):
        return float(self.query("SOUR:CPOW?"))

    @power_mode.setter
    def power_mode(self, mode):
        self.check_success(self.write("SOUR:CPOW {:d}".format(mode)))

    @Feat(units="mA", limits=(0, 180))
    def target_current(self):
        return float(self.query("SOUR:CURR:DIOD?"))*1e-3

    @target_current.setter
    def target_current(self, current):
        self.check_success(self.write("SOUR:CURR:DIOD {:.2f}".format(current)))
