from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from pyvisa import constants

from time import sleep


class CoBriteDX1(MessageBasedDriver):
    """

    """

    # Set these parameters from the datasheet of your model.
    channels = ['1,1,1']  # can add additional channels here!

    freq_min = 191.3  # THz
    freq_max = 196.25  # THz

    min_power = 6  # dBm
    max_power = 15.5  # dBm
    offset_lim = 12.0  # GHz

    sbs_lims = (0, 1, 0.1)

    THz_to_nm = 299792  # 1 THz in nm
    lambda_min = THz_to_nm/freq_max
    lambda_max = THz_to_nm/freq_min

    on_off = {'off': 0, 'on': 1}
    yes_no = {'no': 0, 'yes': 1}

    DEFAULTS = {'ASRL': {'write_termination': ';',
                         'read_termination': ';',
                         'baud_rate': 115200,
                         'data_bits': 8,
                         'parity': constants.Parity.none,
                         'stop_bits': constants.StopBits.one,
                         'encoding': 'utf-8',
                         'timeout': 2000}}

    def initialize(self):
        """
        """
        super().initialize()
        sleep(1)
        self.echo = 'off'  # need to do this to drop command echoing

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
        print(':SYS:ECHO {}'.format(status))
        return self.query(':SYS:ECHO {}'.format(status))

    @Feat()
    def idn(self):
        """
        Returns the laser firmware and hardware information.
        """
        return self.query('*idn?')

    @Feat()
    def layout(self):
        """
        Returns the configuration of the attached system.

        This will be in format:
        SYSTEM <Master chassis type>, <slave chassis type>,
        <slave chassis type>,...\n <Slot address>, <card type>, \n
        <Slot address>, <card type>\n...
        """
        return self.query(':SYS:LAY?')

    @DictFeat(keys=channels, limits=(lambda_min, lambda_max))
    def wavelength(self, channel):
        """
        Returns the current laser wavelength, in nm.
        """
        result = self.query(':SOUR:WAV? {}'.format(channel))
        return float(result.replace(channel + ',', ''))

    @wavelength.setter
    def wavelength(self, channel, lambd):
        """
        Sets the current laser wavelength to lambda (nm).
        """
        delay = 1
        value = self.query(':SOUR:WAV {}, {:.4f}'.format(channel, lambd))
        while not self.operation_complete:
            sleep(delay)
        #self.read()
        return value

    @DictFeat(keys=channels, limits=(lambda_min, lambda_max))
    def wavelength_lim(self, channel):
        """
        Returns wavelength limits of the laser at channel in nm.
        """
        result = self.query(':SOUR:WAV:LIM? {}'.format(channel))
        return self.split_floats(channel, result)

    @DictFeat(keys=channels, limits=(freq_min, freq_max))
    def frequency(self, channel):
        """
        Returns the frequency of the laser at channel in THz.
        """
        return float(self.query(':SOUR:FREQ? {}'.format(channel)))

    @frequency.setter
    def frequency(self, channel, THz):
        """
        Sets the frequency of the laser at channel to THz.
        """
        delay = 1
        value = self.write(':SOUR:FREQ {},{:.4f}'.format(channel, THz))
        while not self.operation_complete:
            sleep(delay)
        self.read()
        return value

    @DictFeat(keys=channels, limits=(freq_min, freq_max))
    def frequency_lim(self, channel):
        """
        Return the frequency limits of the laser at channel in THz.
        """
        result = self.query(':SOUR:FREQ:LIM? {}'.format(channel))
        return self.split_floats(channel, result)

    @DictFeat(keys=channels, limits=(0, offset_lim))
    def offset(self, channel):
        """
        Returns the offset of the laser at channel in GHz.
        """
        return float(self.query(':SOUR:OFF? {}'.format(channel)))

    @offset.setter
    def offset(self, channel, GHz):
        """
        Sets the offset of the laser at channel to GHz.
        """
        delay = 1
        value = self.write(':SOUR:OFF {},{:.4f}'.format(channel, GHz))
        while not self.operation_complete:
            sleep(delay)
        self.read()
        return value

    @DictFeat(keys=channels, limits=(0, offset_lim))
    def offset_lim(self, channel):
        """
        Returns the fine tuning limits of the laser at channel in GHz.
        """
        return float(self.query(':SOUR:OFF:LIM? {}'.format(channel)))

    @DictFeat(keys=channels, limits=(min_power, max_power))
    def power(self, channel):
        """
        Returns the laser power.
        """
        return float(self.query(':SOUR:POW? {}'.format(channel)))

    @power.setter
    def power(self, channel, dBm):
        """
        Sets the power of the laser at channel to dBm.
        """
        delay = 1
        value = self.write(':SOUR:POW {},{:.4f}'.format(channel, dBm))
        while not self.operation_complete:
            sleep(delay)
        self.read()
        return value

    @DictFeat(keys=channels, limits=(0, max_power))
    def power_lim(self, channel):
        """
        Returns maximum power of the laser at channel in dBm.
        """
        result = self.query(':SOUR:FREQ:LIM? {}'.format(channel))
        return self.split_floats(channel, result)

    @DictFeat(keys=channels)
    def limits(self, channel):
        """
        Returns all limits of the laser at channel in form:
        [Min freq (THz), Max freq(THz), Tune range (GHz), Min pow (dBm),
        Max power (dBm)]
        """
        result = self.query(':SOUR:LIM? {}'.format(channel))
        return self.split_floats(channel, result)

    @DictFeat(keys=channels, values=on_off)
    def state(self, channel):
        """
        Returns the current state of the laser at channel.
        """
        return int(self.query(':SOUR:STAT? {}'.format(channel)))

    @state.setter
    def state(self, channel, on_status):
        """
        Sets the state of the laser at channel to on_status
        """
        delay = 1
        value = self.write(':SOUR:STAT {},{}'.format(channel, on_status))
        while not self.operation_complete:
            sleep(delay)
        self.read()
        return value

    @DictFeat(keys=channels)
    def configuration(self, channel):
        """
        Returns the current laser configuration in format:
        [Freq (THz), Fine tuning (GHz), Power (dBm), On/off (0/1), Busy (0/1),
        Dither (0/1)]
        """
        result = self.query(':SOUR:CONF? {}'.format(channel)).split(',')
        return (list(map(float, result[0:3])) + list(map(int, result[3:6])))

    @DictFeat(keys=channels, values=yes_no)
    def busy(self, channel):
        """
        Query state of a device.
        If 1, the laser is currently tuning and not settled.
        """
        return int(self.query(':SOUR:BUSY? {}'.format(channel)))

    @DictFeat(keys=channels)
    def monitor(self, channel):
        """
        Returns monitor information from laser in format:
        [LD chip temp (deg C), LD base temp (deg C), LD chip current (mA),
        TEC current (mA)]
        """
        result = self.query(':SOUR:MON? {}'.format(channel))
        return self.split_floats(channel, result)

    @DictFeat(keys=channels, values=on_off)
    def dither(self, channel):
        """
        Queries whether or not the laser at channel is on or off.
        """
        return int(self.query(':SOUR:DIT? {}'.format(channel)))

    @dither.setter
    def dither(self, channel, dither_status):
        """
        Sets the dither tone of the laser at channel to be dither_status.
        """
        return self.query(':SOUR:DIT {},{}'.format(channel, dither_status))

    @DictFeat(keys=channels, values=on_off)
    def sbs(self, channel):
        """
        Queries whether or not the stimulated Brillouin scattering (SBS)
        supression is on or off.
        """
        return int(self.query(':SOUR:SBS:STAT? {}'.format(channel)))

    @sbs.setter
    def sbs(self, channel, sbs_status):
        """
        Sets the stimulated Brillouin scattering (SBS) supression to be
        sbs_status.
        """
        return self.query(':SOUR:SBS:STAT {},{}'.format(channel, sbs_status))

    @Feat(limits=sbs_lims)
    def sbs_freq(self):
        """
        Queries the stimulated Brillouin scattering (SBS) supression amplitude
        for all lasers in GHz.
        """
        return float(self.query(':SOUR:SBS:FREQ?'))

    @sbs_freq.setter
    def sbs_freq(self, GHz):
        """
        Sets the stimulated Brillouin scattering (SBS) supression amplitude
        for all lasers to GHz.
        """
        return self.query(':SOUR:SBS:FREQ {}'.format(GHz))

    @Feat()
    def operation_complete(self):
        """
        Operation complete query, checks to see if all lasers are settled.
        """
        if self.query('*opc?') == '1':
            return True
        else:
            return False

    @Action()
    def save_curr_state(self, channel):
        """
        Permanently saves the current laser port state for channel, which will
        be loaded again after a power on/off cycle or reset. Autostart must be
        enabled for this to work.
        """
        if channel in self.channels:
            return self.query(':SYS:SCSTAT'.format(channel))
        else:
            print('Invalid channel.')
            return 0

    @Feat(values=on_off)
    def autostart(self):
        """
        Check to see if laser autostart is enabled.
        """
        return int(self.query(':SYS:AUTOSTA?'))

    @autostart.setter
    def autostart(self, autostart_status):
        """
        Sets the laser autostart to be autostart_status.
        """
        return self.query(':SYS:AUTOSTA'.format(autostart_status))

    def split_floats(self, channel, result):
        """
        Helper function for returning tuples returned during communication.
        """
        ret_vals = []
        for val in result.replace(channel + ',', '').split(','):
            ret_vals.append(float(val))
        return ret_vals

if __name__ == '__main__':
    with CoBriteDX1.via_serial(8) as inst:
        inst.echo = 'off'
        print('== System Information ==')
        print('IDN:{}'.format(inst.idn))
        print('Layout:{}'.format(inst.layout))
        print('Autostart:{}'.format(inst.autostart))

        print('== System Control Demo ==')

        for chan in inst.channels:
            print('Laser at channel: {}'.format(chan))
            print('== Laser Parameters ==')
            print('Wavelength: {} nm'.format(inst.wavelength[chan]))
            print('Frequency: {} THz'.format(inst.frequency[chan]))
            print('Power: {} dBm'.format(inst.power[chan]))
            print('Offset: {} GHz'.format(inst.offset[chan]))
            print('State: {}'.format(inst.state[chan]))
            print('Busy?: {}'.format(inst.busy[chan]))
            print('Configuration: {}'.format(inst.configuration[chan]))
            print('Dither?: {}'.format(inst.dither[chan]))
            print('SBS?: {}'.format(inst.sbs[chan]))
            print('SBS Frequency: {} GHz'.format(inst.sbs_freq))

            print('== Laser limits ==')
            print('Wavelength limits: {} nm'.format(inst.wavelength_lim[chan]))
            print('Frequency limits: {} THz'.format(inst.frequency_lim[chan]))
            print('Offset limit: {} GHz'.format(inst.offset_lim[chan]))
            print('Power limit: {} dBm'.format(inst.power_lim[chan]))
            print('All limits: {}'.format(inst.limits[chan]))

            print('== Laser Control Demo ==')
            #print('Saving current state...')
            #inst.save_curr_state(channel=chan)

            inst.frequency[chan] = 195.3
            print('Configuration: {}'.format(inst.configuration[chan]))
            inst.wavelength[chan] = 1530.1234
            print('Configuration: {}'.format(inst.configuration[chan]))
            inst.frequency[chan] = 191.3
            inst.offset[chan] = 6.5
            inst.state[chan] = 'on'
            print('Configuration: {}'.format(inst.configuration[chan]))
            print('Monitor: {}'.format(inst.monitor[chan]))
            inst.offset[chan] = 12
            inst.power[chan] = 6.1
            print('Configuration: {}'.format(inst.configuration[chan]))
            print('Busy:{}'.format(inst.busy[chan]))
            inst.power[chan] = 15.5
            print('Configuration: {}'.format(inst.configuration[chan]))
            inst.offset[chan] = 0.0
            print('Configuration: {}'.format(inst.configuration[chan]))
            inst.state[chan] = 'off'
            print('Configuration: {}'.format(inst.configuration[chan]))
