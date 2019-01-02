from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver

from pyvisa import constants

from numpy import abs, ceil

from time import sleep


class SP2150i(MessageBasedDriver):
    """
    Implements controls for the Princeton Instruments Acton Series SP2150i
    Monochromater over the internal USB virtual serial port.

    Communication with the device is a little finnicky, so if you run into
    problems, I would suggest adding more buffer clears to avoid garbage
    accumulating in the buffer and messing up your commands.

    Author: Peter Mintun (pmintun@uchicago.edu)
    Date: 1/21/2016
    """
    DEFAULTS = {'ASRL': {'write_termination': '\r',
                         'read_termination': 'ok\r\n',
                         'baud_rate': 9600,
                         'data_bits': 8,
                         'parity': constants.Parity.none,
                         'stop_bits': constants.StopBits.one,
                         'encoding': 'latin-1',
                         'timeout': 2000}}

    max_speed = 100
    wavelength_min = 380
    wavelength_max = 520

    num_gratings = 8

    def initialize(self):
        """
        """
        super().initialize()
        self.clear_buffer()

    def clear_buffer(self):
        """
        This function sends an empty query just to clear any junk from the read
        buffer...This could probably be done more elegantly...but it works, for
        now at least.
        """
        return self.query('')

    @Feat(limits=(wavelength_min, wavelength_max))
    def nm(self):
        """
        Returns current wavelength of monochromater.
        """
        self.clear_buffer()
        read = self.query('?NM')
        wavelength = read.replace('nm', '')
        return float(wavelength)

    @nm.setter
    def nm(self, wavelength):
        """
        Sets output to specified wavelength, traveling at the current scan
        rate.
        """
        curr_wavelength = self.nm
        scan_rate = self.scan_speed
        delta_lambda = abs(curr_wavelength - wavelength)
        if delta_lambda > 0.1:
            scan_time = ceil(delta_lambda / scan_rate * 60) + 2  # need seconds
            self.clear_buffer()
            print('Scanning from {}nm to {}nm, will take {}sec'.format(
                curr_wavelength, wavelength, scan_time))
            return self.write_message_wait('{0:.1f} NM'.format(wavelength),
                                           scan_time)
        else:
            return


    @Feat(limits=(0, max_speed))
    def scan_speed(self):
        """
        Get scan rate in nm/min.
        """
        self.clear_buffer()
        read = self.query('?NM/MIN')
        speed = read.replace('nm/min', '')
        return float(speed)

    @scan_speed.setter
    def scan_speed(self, speed):
        """
        Sets current scan speed in nm/min.
        """
        return self.write_message_wait('{0:.1f} NM/MIN'.format(speed), 0.1)

    @Feat(limits=(1, 2, 1))
    def grating(self):
        """
        Returns the current grating position
        """
        response = self.query('?GRATING')
        return int(response)

    @grating.setter
    def grating(self, grating_num):
        """
        Changes the current grating to be the one in slot grating_num.
        """
        print('Warning: Untested code! No other gratings were installed.')
        print('Changing grating, please wait 20 seconds...')
        return self.write_message_wait('{} GRATING'.format(grating_num), 20)

    @Feat(limits=(1, 3, 1))
    def turret(self):
        """
        Returns the selected turret number.
        """
        response = self.query('?TURRET')
        return int(response.replace('  ok', ''))

    @turret.setter
    def turret(self, turr_set):
        """
        Selects the parameters for the grating on turret turr_set
        """
        print('Warning: untested. No other turrets were installed.')
        return self.write_message_wait('{} TURRET'.format(turr_set), 1)

    @Feat()
    def turret_spacing(self):
        """
        Returns the groove spacing of the grating for each turret.
        """
        print('Warning: This command does\'t do anything?')
        return self.write_message_wait('?TURRETS', 0.5)

    @Feat()
    def grating_settings(self):
        """
        Returns the groove spacing and blaze wavelength of grating positions
        for all possible gratings.
        """
        gratings = []
        self.write('?GRATINGS')
        self.read()
        for i in range(0, self.num_gratings):
            gratings.append(self.read())
        self.read()
        return gratings

    def write_message_wait(self, message, wait_time):
        self.write(message)
        sleep(wait_time)
        return self.read()

if __name__ == '__main__':
    with SP2150i('ASRL4::INSTR') as inst:
        print('== Monochromater Wavelength ==')
        print('Wavelength:{}nm'.format(inst.nm))
        print('Scan rate:{}nm/min'.format(inst.scan_speed))

        print('== Monochromater Information ==')
        print('Selected turret:{}'.format(inst.turret))
        print('Selected grating:{}'.format(inst.grating))
        # inst.turret = 3
        # inst.grating = 2
        print('Selected turret:{}'.format(inst.turret))
        print('Selected grating:{}'.format(inst.grating))
        print('Turret Spacing:{}'.format(inst.turret_spacing))
        print('Gratings:{}'.format(inst.grating_settings))

        for i in range(1, 20):
            inst.scan_speed = 100.0
            print('Scan rate:{}nm/min'.format(inst.scan_speed))
            print('Wavelength:{}nm'.format(inst.nm))
            inst.nm = 400.0
            print('Wavelength:{}nm'.format(inst.nm))
            inst.scan_speed = 50.0
            print('Scan rate:{}nm/min'.format(inst.scan_speed))
            inst.nm = 500.0
            print('Wavelength:{}nm'.format(inst.nm))
            print('Cycle {} complete.'.format(i))
