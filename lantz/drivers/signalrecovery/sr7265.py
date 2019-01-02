from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver

from collections import OrderedDict

from time import sleep


class SR7265(MessageBasedDriver):
    """Signal Recovery 7265
    DSP Lock-in Amplifier

    Author: P. Mintun
    Version: 0.0.1
    Date: 11/13/2015

    "Stay safe and happy locking in..."

    This driver assumes that the COMM settings of the 7265 are set up as
    follows:

    ADDRESS = N
    TERMINATOR = [EOI]
    TECH ECHO = DISABLED

    SDC=ADF 1 ENABLED
    """

    DEFAULTS = {
        'COMMON': {
            'write_termination': '\r\n',
            'read_termination': '\r\n'
        }
    }

    INT_EXT_REF = OrderedDict([
                   ('Internal', 0),
                   ('Rear External', 1),
                   ('External', 2)
                   ])

    TIME_CONSTANTS = OrderedDict([
                     ('10 us' , 0  ),
                     ('20 us' , 1  ),
                     ('40 us' , 2  ),
                     ('80 us' , 3  ),
                     ('160 us', 4  ),
                     ('320 us', 5  ),
                     ('640 us', 6  ),
                     ('5 ms'  , 7  ),
                     ('10 ms' , 8  ),
                     ('20 ms' , 9  ),
                     ('50 ms' , 10 ),
                     ('100 ms', 11 ),
                     ('200 ms', 12 ),
                     ('500 ms', 13 ),
                     ('1 s'   , 14 ),
                     ('2 s'   , 15 ),
                     ('5 s'   , 16 ),
                     ('10 s'  , 17 ),
                     ('20 s'  , 18 ),
                     ('50 s'  , 19 ),
                     ('100 s' , 20 ),
                     ('200 s' , 21 ),
                     ('500 s' , 22 ),
                     ('1 ks'  , 23 ),
                     ('2 ks'  , 24 ),
                     ('5 ks'  , 25 ),
                     ('10 ks' , 26 ),
                     ('20 ks' , 27 ),
                     ('50 ks' , 28 ),
                     ('100 ks', 29 ),
                     ])

    AC_GAINS = OrderedDict([
               ('0 dB', 0),
               ('10 dB', 1),
               ('20 dB', 2),
               ('30 dB', 3),
               ('40 dB', 4),
               ('50 dB', 5),
               ('60 dB', 6),
               ('70 dB', 7),
               ('80 dB', 8),
               ('90 dB', 9),
               ])

    SENSITIVITIES = OrderedDict([
                    ('2 nV',   1  ),
                    ('5 nV',   2  ),
                    ('10 nV',  3  ),
                    ('20 nV',  4  ),
                    ('50 nV',  5  ),
                    ('100 nV', 6  ),
                    ('200 nV', 7  ),
                    ('500 nV', 8  ),
                    ('1 uV',   9  ),
                    ('2 uV',   10 ),
                    ('5 uV',   11 ),
                    ('10 uV',  12 ),
                    ('20 uV',  13 ),
                    ('50 uV',  14 ),
                    ('100 uV', 15 ),
                    ('200 uV', 16 ),
                    ('500 uV', 17 ),
                    ('1 mV',   18 ),
                    ('2 mV',   19 ),
                    ('5 mV',   20 ),
                    ('10 mV',  21 ),
                    ('20 mV',  22 ),
                    ('50 mV',  23 ),
                    ('100 mV', 24 ),
                    ('200 mV', 25 ),
                    ('500 mV', 26 ),
                    ('1 V',    27 ),
                    ])

    def remove_null(self, value):
        value = value.replace('\x00', '')
        return value

    @Feat()
    def idn(self):
        """
        Returns current instrument identification.
        """
        return self.query('ID')

    @Feat(units='V')
    def x(self):
        """
        Read x value from lockin.
        """
        return float(self.remove_null(self.query('X.')))

    @Feat(units='V')
    def y(self):
        """
        Read y value from lockin.
        """
        return float(self.remove_null(self.query('Y.')))

    @Feat()
    def xy(self):
        """
        Read x and y values from lockin simultaneously.
        """
        return [float(value) for value in self.remove_null(self.query('XY.')).split(',')]

    @Feat(units='V')
    def magnitude(self):
        """
        Read signal magnitude from lockin.
        """
        return float(self.remove_null(self.query('MAG.')))

    @Feat(units='degree')
    def phase(self):
        """
        Read signal phase from lockin.
        """
        return float(self.remove_null(self.query('PHA.')))

    @Feat()
    def mag_phase(self):
        """
        Read signal magnitude and phase from lockin.
        """
        return [float(value) for value in self.remove_null(self.query('MP.')).split(',')]

    @Action()
    def autophase(self):
        """
        Adds an offset to the phase of the lockin to minimize the y-channel
        signal and maximize the x-channel signal.
        """
        return self.write('AQN')

    @Feat(values=TIME_CONSTANTS)
    def time_constant(self):
        """
        Returns current time constant setting (in seconds).
        """
        return float(self.query('TC'))

    @time_constant.setter
    def time_constant(self, time_const):
        self.write('TC{}'.format(time_const))
        return

    @Feat()
    def frequency(self):
        """
        Read current signal frequency.
        """
        return float(self.remove_null(self.query('FRQ.')))

    @Feat(limits=(0, 250e3))
    def oscillator_freq(self):
        """
        Read internal oscillator frequency.
        """
        return float(self.remove_null(self.query('OF.')))

    @oscillator_freq.setter
    def oscillator_freq(self, frequency):
        """
        Set internal oscillator frequency.
        """
        self.write('OF.{}'.format(frequency))

    @Feat(values=AC_GAINS)
    def gain(self):
        """
        Read current AC gain (dB).
        """
        return int(self.query('ACGAIN'))

    @gain.setter
    def gain(self, gain_value):
        """
        Set current AC gain (dB)
        """
        self.write('ACGAIN{}'.format(gain_value))



    @Feat(values=SENSITIVITIES)
    def sensitivity(self):
        """
        Gets sensitivity according to the SENSITIVITIES table.
        """
        return int(self.query('SEN'))

    @sensitivity.setter
    def sensitivity(self, sen_it):
        """
        Sets value of sensitivity as described by SENSITIVITIES.
        """
        self.write('SEN{}'.format(sen_it))

    @Feat()
    def voltage_mode(self):
        """
        Gets the voltage mode
        """
        return int(self.query('VMODE'))

    @voltage_mode.setter
    def voltage_mode(self, n):
        """
        Sets value of voltage mode
        From page 138 of the 7265 manual, they say:
            n   Input configuration
            0   Both inputs grounded (test mode)
            1   A input only
            2   -B input only
            3   A-B differential mode
        """
        self.write('VMODE{}'.format(n))

    @Action()
    def autosensitivity(self):
        """
        Runs an autosensitivity operation.

        The instrument adjusts its full-scale sensitivity so that the magnitude
        output lies between 30-90 percent of full-scale
        """
        a = self.write('AS')
        sleep(7.5)  # wait for operation to complete
        return a

    @Action()
    def autogain(self):
        """
        Set current AC gain to automatic.
        """
        return self.write('AUTOMATIC1')

    @Feat(values=INT_EXT_REF)
    def int_ext_ref(self):
        """
        Check if lockin is internally or externally referenced
        """
        return int(self.query('IE'))

    @int_ext_ref.setter
    def int_ext_ref(self, value):
        """
        Set lockin to be internal or external reference
        """
        return self.write('IE {}'.format(value))

    def status_byte(self):
        return int(self.query('ST'))

    def get_bit(self, byte, bit):
        return True if int('{0:b}'.format(byte).zfill(8)[-(bit + 1)]) else False

    @Feat(values={True: True, False: False})
    def reference_unlock(self):
        return self.get_bit(self.status_byte(), 3)

    @Feat(values={True: True, False: False})
    def overload(self):
        return self.get_bit(self.status_byte(), 4)

    @Action()
    def autophase(self):
        """
        Automatically detect offset
        """
        return self.write('AXO')

    @Feat(values={True: 1, False: 0})
    def x_offset_enabled(self):
        return int(self.query('XOF?').split(',')[0])

    @x_offset_enabled.setter
    def x_offset_enabled(self, val):
        return self.write('XOF {}'.format(val))

    @Feat(values={True: 1, False: 0})
    def y_offset_enabled(self):
        return int(self.query('YOF?').split(',')[0])

    @x_offset_enabled.setter
    def y_offset_enabled(self, val):
        return self.write('YOF {}'.format(val))

    @Feat()
    def x_offset(self):
        return int(self.query('XOF?').split(',')[1])

    @x_offset.setter
    def x_offset(self, val):
        return self.write('XOF 1 {}'.format(val))

    @Feat()
    def y_offset(self):
        return int(self.query('YOF?').split(',')[1])

    @y_offset.setter
    def y_offset(self, val):
        return self.write('YOF 1 {}'.format(val))

if __name__ == '__main__':
    with SR7265.via_gpib(7) as inst:
        print('The instrument identification is ' + inst.idn)

        print('Testing signal readings')
        print('Signal X: {}V'.format(inst.x))
        print('Signal Y: {}V'.format(inst.y))
        print('Signal magnitude: {}V'.format(inst.magnitude))
        print('Signal phase: {}degrees'.format(inst.phase))

        print('Testing full quadrature readings')
        print('X,Y: {}V'.format(list(inst.xy)))
        print('Magnitude, Phase: {}'.format(list(inst.mag_phase)))
        inst.autophase
        sleep(2)
        print('Magnitude, Phase: {}'.format(list(inst.mag_phase)))

        print('Testing frequency code')
        print('Ref f: {}Hz'.format(inst.frequency))
        inst.oscillator_freq = 137.0
        print('Ref f: {}Hz'.format(inst.frequency))
        inst.oscillator_freq = 17
        print('Ref f: {}Hz'.format(inst.frequency))
        #
        print('Internal External Reference check')
        print('Internal/ext reference: {}'.format(inst.int_ext_ref))
        inst.int_ext_ref = 'ext'
        print('Internal/ext reference: {}'.format(inst.int_ext_ref))
        inst.int_ext_ref = 'int'
        print('Internal/ext reference: {}'.format(inst.int_ext_ref))

        print('Time constant check')
        print('Int TC: {}'.format(inst.time_constant_integer))
        print('TC (sec): {}s'.format(inst.time_constant))
        inst.time_constant_integer = 15
        print('Int TC: {}'.format(inst.time_constant_integer))
        print('TC (sec): {}s'.format(inst.time_constant))
        inst.time_constant_integer = 10
        print('Int TC: {}'.format(inst.time_constant_integer))
        print('TC (sec): {}s'.format(inst.time_constant))

        print('AC Gain Check')
        print('AC Gain: {}'.format(inst.gain))
        inst.gain = '30dB'
        print('AC Gain: {}'.format(inst.gain))
        inst.autogain
        print('AC Gain: {}'.format(inst.gain))

        print('Sensitivity Check')
        print('Sen: {}'.format(inst.sensitivity))
        inst.sensitivity = '2e-8V'
        print('Sen: {}'.format(inst.sensitivity))
        inst.autosensitivity()
        print('Sen: {}'.format(inst.sensitivity))
