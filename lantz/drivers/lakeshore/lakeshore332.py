# Lakeshore 332 Temperature Controller Driver
# Peter Mintun <pmintun@uchicago.edu>

# This file is a driver for the Lakeshore 332 series temperature controller.

# Some sort of license information goes here.

from lantz import Feat, Action, DictFeat
from lantz.messagebased import MessageBasedDriver
from time import sleep


class Lakeshore332(MessageBasedDriver):
    """
    Lakeshore 332 Temperature controlller.

    This class, based off of the Lantz MessageBasedDriver class, implements a
    set of basic controls for the Lakeshore 332 series temperature controller.
    It essentially a port of a nice driver written for QtLab by Reinier Heeres.

    Full documentation of the device is available at:
    http://www.lakeshore.com/ObsoleteAndResearchDocs/332_Manual.pdf
    """

    # These defaults assume that you have set the IEEE Term setting to: Lf Cr
    DEFAULTS = {'COMMON': {'write_termination': '\n',
                           'read_termination': ''}}

    GPIB_name = None
    GPIB_address = -1

    channels = ['a', 'b']
    loops = ['1', '2']
    heater_range_vals = {'off': 0, 'low': 1, 'medium': 2, 'high': 3}
    heater_status_vals = {'no error': 0, 'open load': 1, 'short': 2}
    controller_modes = {'local': 0, 'remote': 1, 'remote, local lockout': 2}
    cmodes = {'manual PID': 1, 'zone': 2, 'open loop': 3, 'AutoTune PID': 4,
              'AutoTune PI': 5, 'AutoTune P': 6}

    T_min = 0
    T_max = 350

    T_min_set = 1.8
    T_max_set = 350

    _verbose = True

    @Feat()
    def idn(self):
        """
        Returns the instrument identification.
        """
        print('getting IDN')
        return self.query('*IDN?')

    @Action()
    def reset(self):
        """
        Resets the Lakeshore 332 temperature controller.
        """
        self.write('*RST')

    @DictFeat(limits=(T_min, T_max), keys=channels)
    def kelvin_meas(self, channel):
        """
        Returns measured temperature reading from specified channel in Kelvin.
        """
        return float(self.query('KRDG?{}'.format(channel)))

    @DictFeat(keys=channels)
    def sensor(self, channel):
        """
        Returns sensor reading from specified channel.
        """
        return float(self.query('SRDG?{}'.format(channel)))

    @Feat(values=heater_status_vals)
    def heater_status(self):
        """
        Returns the heater status.
        """
        return int(self.query('HTRST?'))

    @Feat(values=heater_range_vals)
    def heater_range(self):
        """
        Queries the instrument, prints a message describing the current heater
        range setting, then returns the heater range value.
        """
        return int(self.query('RANGE?'))

    @heater_range.setter
    def heater_range(self, heater_setting):
        """
        Sets heater range to  heater_setting.

        heater_setting must be an integer between 0 and 3 inclusive.
        """
        return self.write('RANGE {}'.format(heater_setting))

    @Feat()
    def heater_output_1(self):
        """
        Returns Loop 1 heater output in percent (%).
        """
        return float(self.query('HTR?'))

    @Feat()
    def heater_output_2(self):
        """
        Returns Loop 2 heater output in percent (%).
        """
        return float(self.query('AOUT?'))

    @Feat(values=controller_modes)
    def mode(self):
        """
        Reads the mode setting of the controller.
        """
        return int(self.query('MODE?'))

    @mode.setter
    def mode(self, mode):
        """
        Sets controller mode, valid mode inputs are:
        local (0)
        remote (1)
        remote, local lockout (2)
        """
        return self.query('MODE{}'.format(mode))

    @DictFeat(keys=loops)
    def pid(self, loop):
        """
        Get parameters for PID loop.
        """
        return self.query('PID?{}'.format(loop))

    @pid.setter
    def pid(self, loop, pid):
        """
        Get parameters for PID loop
        """
        p = pid[0]
        i = pid[1]
        d = pid[2]
        return self.query('PID{},{},{},{}'.format(loop, p, i, d))

    @DictFeat(limits=(T_min_set, T_max_set), keys=loops)
    def setpoint(self, channel):
        """
        Return the temperature controller setpoint.
        """
        return float(self.query('SETP?{}'.format(channel)))

    @setpoint.setter
    def setpoint(self, loop, T_set):
        """
        Sets the setpoint of channel channel to value value
        """
        self.query('SETP{},{}'.format(loop, T_set))
        sleep(0.05)
        return

    @DictFeat(limits=(0, 100), keys=loops)
    def mout(self, loop):
        """
        Returns loop manual heater power output.
        """
        return self.query('MOUT?{}'.format(loop))

    @mout.setter
    def mout(self, loop, percent):
        """
        Sets loop manual heater power output in percent.
        """
        return self.query('MOUT{},{}'.format(loop, percent))

    @DictFeat(values=cmodes, keys=loops)
    def cmode(self, loop):
        """
        Returns the control mode according to the following table.
        'manual PID' (1)
        'zone'(2)
        'open loop' (3)
        'AutoTune PID' (4)
        'AutoTune PI' (5)
        'AutoTune P' (6)
        """
        return int(self.query('CMODE?{}'.format(loop)))

    @cmode.setter
    def cmode(self, loop, value):
        """
        Sets the control mode according to the following table.
        'manual PID' (1)
        'zone'(2)
        'open loop' (3)
        'AutoTune PID' (4)
        'AutoTune PI' (5)
        'AutoTune P' (6)
        """
        return self.query('CMODE{},{}'.format(loop, value))


if __name__ == '__main__':
    with Lakeshore332('GPIB0::16::INSTR') as inst:
        print('The instrument identification is ' + inst.idn)

        print('resetting...')
        inst.reset
        print('reset.')

        # Testing mode switching functionality
        print('The current mode is ' + inst.mode + '.')
        inst.mode = 'remote, local lockout'
        print('Now the mode is ' + inst.mode + '.')
        inst.mode = 'remote'
        print('Now the mode is ' + inst.mode + '.')

        # Testing Kelvin read functionality
        print('Current temperature on channel a is ' +
              str(inst.kelvin_meas['a']) + ' Kelvin')
        print('Current temperature on channel b is ' +
              str(inst.kelvin_meas['b']) + ' Kelvin')

        # Testing sensor reading functionality
        print('Sensor reading on channel a is ' + str(inst.sensor['a']))
        print('Sensor reading on channel b is ' + str(inst.sensor['b']))

        # Testing heater status
        print('Heater status is ' + str(inst.heater_status))

        # Testing heater range
        print('Heater range is ' + str(inst.heater_range))
        inst.heater_range = 'low'
        print('Heater range is ' + str(inst.heater_range))
        inst.heater_range = 'off'
        print('Heater range is ' + str(inst.heater_range))

        # Testing heater output
        print('Loop 1 heater output ' + str(inst.heater_output_1) + '%')
        print('Loop 2 heater output ' + str(inst.heater_output_2) + '%')

        # Testing manual output
        print('Loop 1 manual output ' + str(inst.mout['1']))
        print('Loop 2 manual output ' + str(inst.mout['2']))
        inst.mout['1'] = 50
        inst.mout['2'] = 50
        print('Loop 1 manual output ' + str(inst.mout['1']))
        print('Loop 2 manual output ' + str(inst.mout['2']))
        inst.mout['1'] = 0
        inst.mout['2'] = 0
        print('Loop 1 manual output ' + str(inst.mout['1']))
        print('Loop 2 manual output ' + str(inst.mout['2']))

        # Testing cmode
        print('Loop 1 Command Mode: ' + str(inst.cmode['1']))
        inst.cmode['1'] = 'open loop'
        print('Loop 1 Command Mode: ' + str(inst.cmode['1']))
        inst.cmode['1'] = 'AutoTune P'
        print('Loop 1 Command Mode: ' + str(inst.cmode['1']))
        print('Loop 2 Command Mode: ' + str(inst.cmode['2']))

        # Testing setpoint
        inst.setpoint['1'] = 25
        print('Loop 1 setpoint is ' + str(inst.setpoint['1']))
        inst.setpoint['1'] = 50
        print('Loop 1 setpoint is ' + str(inst.setpoint['1']))
        inst.setpoint['1'] = 300
        print('Loop 1 setpoint is ' + str(inst.setpoint['1']))
        inst.setpoint['2'] = 300
        print('Loop 2 setpoint is ' + str(inst.setpoint['2']))

        # Testing PID
        inst.pid['1'] = list([10.0, 10.0, 10.0])
        print('Loop 1 PID parameters:' + str(inst.pid['1']))
        inst.pid['1'] = list([50.0, 20.0, 1.0])
        print('Loop 1 PID parameters:' + str(inst.pid['1']))
        print('Loop 2 PID parameters:' + str(inst.pid['2']))
