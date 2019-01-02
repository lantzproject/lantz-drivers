from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from pyvisa import constants

from numpy import ceil

from time import sleep


class HindsPEM90(MessageBasedDriver):
    """

    """

    # Set paramters here
    on_off = {'off': 0, 'on': 1}
    waves_limits = (0.0, 19999.9)
    retardation_limits = (0.0, 1.0)

    DEFAULTS = {'ASRL': {'write_termination': '\n',
                         'read_termination': '\n',
                         'baud_rate': 9600,
                         'data_bits': 8,
                         'parity': constants.Parity.none,
                         'stop_bits': constants.StopBits.one,
                         'encoding': 'utf-8',
                         'timeout': 2000}}

    def initialize(self):
        """
        """
        super().initialize()

    @Feat(values=on_off)
    def echo(self):
        """
        Checks to see if ECHO mode is enabled. Note that the code in this
        driver assumes that the command echo is disabled.
        """
        return int(self.query(':SYS:ECHO?'))

    @echo.setter
    def echo(self, status):
        """
        Sets echo mode to be controlled by on_off.
        """
        print('E:{}'.format(status))
        return self.query('E:{}'.format(status))


    @Feat(limits=waves_limits)
    def wavelength(self):
        """
        Reads out current wavelength in nm
        """
        return float(self.query('W'))

    @wavelength.setter
    def wavelength(self, nm):
        """
        Sets wavelength in nm.
        """
        print('W:{}'.format(nm))
        return self.query('W:{0:0>7.1f}'.format(nm))

    @Feat(limits=retardation_limits)
    def retardation(self):
        """
        Reads out current retardation in wave units
        """
        return float(self.query('R')/1000.0)

    @retardation.setter
    def retardation(self, wave_units):
        """
        Sets retardation in wave units.
        """
        print('R:{}'.format(wave_units))
        return self.query('R:{0:04}'.format(ceil(wave_units*1000)))

    @Feat()
    def frequency(self):
        """
        Reads out the reference frequency in hertz
        """
        return float(self.query('F'))

    @Feat()
    def frequency2(self):
        """
        Reads out the reference frequency2 in hertz
        """
        return float(self.query('2F'))

    @Feat(values=on_off)
    def inhibit(self):
        """
        Returns 0 for the retardation inhibitor
        """
        return 0

    @inhibitor.setter
    def inhibitor(self, status):
        """
        Sets the mode to be controlled by on_off.
        """
        print('I:{}'.format(status))
        return self.query('I:{}'.format(status))

    @Action()
    def reset(self):
        """
        Resets PEM-90 to default factory settings.
        """
        return self.query('Z')

if __name__ == '__main__':
    with HindsPEM90.via_serial(10) as inst:

        echo = 'off'
