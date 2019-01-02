from lantz.messagebased import MessageBasedDriver
from lantz import Feat, DictFeat, Action
from collections import OrderedDict


#from lantz import Q_
import numpy as np


import socket
import warnings

class Ag81130A(MessageBasedDriver):
    """
    Lantz driver for interfacing with Agilent 81130A pulse pattern generator.

    Includes testing code, which should work out of the box assuming you give
    it the correct GPIB address.

    Author: P. Mintun
    Date: 12/6/2016
    Version: 0.1
    """

    DEFAULTS = {
        'COMMON': {
            'write_termination': '\n',
            'read_termination': '\n',
        }
    }

    ON_OFF_VALS = OrderedDict([
                    ('on', 1),
                    ('off', 0),
    ])

    ARM_SOURCE_VALS = OrderedDict([
                      ('immediate', 'IMM'),
                      ('external', 'EXT'),
                      ('manual', 'MAN')
    ])

    TRIG_SOURCE_VALS = OrderedDict([
                      ('immediate', 'IMM'),
                      ('external', 'EXT'),
                      ('internal', '1')
    ])

    TRIG_MODE_VALS = OrderedDict([
                      ('continuous', 'CONT'),
                      ('start', 'STAR')
    ])

    channels = range(1,3)
    #channels = OrderedDict([
    #               ('1', 0),
    #               ('2', 1)
    #               ])

    segments = range(1,5)

    # some weird list comprehension variable scope thing here
    chan_segs = [(x,y) for x in range(1,3) for y in range(1,5)]


    @Feat()
    def idn(self):
        """
        Identifiies the instrument.
        """
        return self.query('*IDN?')

    @Action()
    def reset(self):
        """
        Resets the instrument to default settings. This is recommended by the
        manual before starting to programming it.
        """
        return self.write('*RST')

    @DictFeat(keys=channels, limits=(-4.0,4.0))
    def volt_high(self, chan):
        """
        Returns the voltage corresponding to HIGH for channel chan.

        """
        return self.query('VOLT{}:HIGH?'.format(chan))

    @volt_high.setter
    def volt_high(self, chan, volts):
        """
        Sets the voltage corresponding to HIGH for channel chan to volts.
        """
        return self.write('VOLT{}:HIGH {}V'.format(chan, volts))

    @DictFeat(keys=channels, limits=(-4.0,4.0))
    def volt_low(self, chan):
        """
        Returns the voltage corresponding to LOW for channel chan.

        """
        return self.query('VOLT{}:LOW?'.format(chan))

    @volt_low.setter
    def volt_low(self, chan, volts):
        """
        Sets the voltage corresponding to LOW for channel chan to volts.
        """
        return self.write('VOLT{}:LOW {}V'.format(chan, volts))

    @Feat(values=ON_OFF_VALS)
    def display(self):
        """
        Returns if display is on or off, (off enables faster programming).
        """
        return int(self.query('DISP?'))

    @display.setter
    def display(self, on_off):
        """
        Sets display to be on or off, (off enables faster programming).
        """
        return self.write('DISP {}'.format(on_off))


    @Feat(values=ON_OFF_VALS)
    def pattern_mode(self):
        """
        Returns whether or not pattern mode is enabled.
        """
        return int(self.query('DIG:PATT?'))

    @pattern_mode.setter
    def pattern_mode(self, on_off):
        """
        Sets pattern mode to be enabled or disabled.
        """
        return self.write('DIG:PATT {}'.format(on_off))

    @Feat(values=ARM_SOURCE_VALS)
    def arm_source(self):
        """
        Returns the source used for the arming signal for triggering the instrument.

        Options are immediate (continuous mode), external trigger, and manually
        triggered from the keypad.
        """
        return self.query('ARM:SOUR?')

    @arm_source.setter
    def arm_source(self, source_channel):
        """
        Sets the trigger signal to the source channel.

        Options are immediate (continuous mode), external trigger, and manually
        triggered from the keypad.
        """
        return self.write('ARM:SOUR {}'.format(source_channel))

    @Feat(values=TRIG_SOURCE_VALS)
    def trigger_source(self):
        """
        Returns the source of the pulse period trigger signal.

        Options are immediate, internal, or external (CLK IN signal)
        """
        return self.query('TRIG:SOUR?')

    @trigger_source.setter
    def trigger_source(self, trigger_source):
        """
        Sets the source of the pulse period trigger signal.

        Options are immediate, internal, or external (CLK IN signal)
        """
        return self.write('TRIG:SOUR {}'.format(trigger_source))

    @DictFeat(keys=segments)
    def dig_patt_length(self, seg_num, limits=(0,65504,1)):
        """
        Returns the segment type
        """

        return int(self.query('DIG:PATT:SEGM{}:LENG?'.format(seg_num)))

    @dig_patt_length.setter
    def dig_patt_length(self, seg_num, length):

        return self.write('DIG:PATT:SEGM{}:LENG {}'.format(seg_num, int(length)))

    @DictFeat(keys=chan_segs, values={'data':'DATA', 'PRBS':'PRBS', 'high':'HIGH', 'low':'LOW'})
    def dig_patt_type(self, chan_seg):
        """
        Returns the segment type
        """
        channel = chan_seg[0]
        seg_num = chan_seg[1]

        return self.query('DIG:PATT:SEGM{}:TYPE{}?'.format(seg_num, channel))

    @dig_patt_type.setter
    def dig_patt_type(self, chan_seg, patt_type):

        channel = chan_seg[0]
        seg_num = chan_seg[1]

        return self.write('DIG:PATT:SEGM{}:TYPE{} {}'.format(seg_num, channel, patt_type))

    @Feat(limits=(1e3,660e6))
    def frequency(self):
        """
        Gets the operating frequency of the device - this is what sets the timescale
        of the pattern duration.
        """
        return float(self.query('FREQ?'))

    @frequency.setter
    def frequency(self, Hz):
        """
        Sets the internal PLL frequency to Hz.
        """
        return self.write('FREQ {}'.format(Hz))

    @DictFeat(keys=channels, values={'nrz':'NRZ', 'rz':'RZ', 'r1':'R1'})
    def data_format(self, channel):
        """
        Returns current data format for the given channel.

        Options are:
        - nrz (non-return to zero)
        - rz (return to zero)
        - r1 (?)
        """
        return self.query('DIG:SIGN{}:FORM?'.format(channel))

    @data_format.setter
    def data_format(self, channel, data_format):
        """
        Sets data format of the given channel to data_format.

        Options are:
        - nrz (non-return to zero)
        - rz (return to zero)
        - r1 (?)
        """
        return self.write('DIG:SIGN{}:FORM {}'.format(channel, data_format))

    @DictFeat(keys=channels, values=ON_OFF_VALS)
    def output_on(self, channel):
        """
        Queries the output of the specified channel.
        """
        return int(self.query('OUTP{}?'.format(channel)))

    @output_on.setter
    def output_on(self, channel, state):
        """
        Sets the output of the specified channel to state.
        """
        return self.write('OUTP{} {}'.format(channel, state))

    @DictFeat(keys=channels, values=ON_OFF_VALS)
    def comp_output_on(self, channel):
        """
        Queries the output of the specified channel.
        """
        return int(self.query('OUTP{}:COMP ?'.format(channel)))

    @comp_output_on.setter
    def comp_output_on(self, channel, state):
        """
        Sets the output of the specified channel to state.
        """
        return self.write('OUTP{}:COMP {}'.format(channel, state))

    @DictFeat(keys=chan_segs)
    def segment_data(self, chan_seg):
        """
        Returns the data from segment seg_num, channel chan
        """
        channel = chan_seg[0]
        seg_num = chan_seg[1]
        result = self.query('DIG:PATT:SEGM{}:DATA{}?'.format(seg_num, channel))

        # now process data
        return result

    @segment_data.setter
    def segment_data(self, chan_seg, data_stream):
        """
        Sets the data from segment seg_num, channel chan to data_stream (numpy array)
        """
        print('called data setter')


        channel = chan_seg[0]
        seg_num = chan_seg[1]

        data = self.encode_data(data_stream[0])

        self.write('DIG:PATT:SEGM{}:DATA{} {}'.format(seg_num, channel, data))

        return data



    @Feat(limits=(1,5,1))
    def start_seg(self):
        """
        Queries the starting segment for the device pattern.
        """
        return int(self.query('DIG:PATT:LOOP:STAR?'))

    @start_seg.setter
    def start_seg(self, segment):
        """
        Sets the starting segment for the device pattern to segment.
        """
        return self.write('DIG:PATT:LOOP:STAR {}'.format(segment))

    @Feat(limits=(1,5,1))
    def loop_length(self):
        """
        Queries the number of segments to be repeated in the loop.
        """
        return int(self.query('DIG:PATT:LOOP:LENG?'))

    @loop_length.setter
    def loop_length(self, length):
        """
        Sets the number of segments to be included in the loop.
        """
        return self.write('DIG:PATT:LOOP:LENG {}'.format(length))

    @DictFeat(keys=channels, limits=(0, 2*np.pi))
    def phase_delay(self, chan):
        """
        Returns the phase delay of the output signal of channel chan, in radians.
        """
        return float(self.query('PHAS{}?'.format(chan)))

    @phase_delay.setter
    def phase_delay(self, chan, delay):
        """
        Sets the phase delay of the output signal of channel chan to delay, in radians.
        """
        return self.write('PHAS{} {}'.format(chan, delay))

    @DictFeat(keys=channels, limits=(0, 3000e-9))
    def timed_delay(self, chan):
        """
        Returns the timed delay of the output signal of channel chan in seconds.
        """
        return float(self.query('PULS:DEL{}?'.format(chan)))


    @timed_delay.setter
    def timed_delay(self, chan, sec):
        """
        Sets the timed delay of output of channel chan to sec.
        """
        return self.write('PULS:DEL{} {}S'.format(chan, sec))


    @Feat()
    def trig_output(self):
        """
        Returns the voltage level used for trigger output.
        """
        return self.query('PULS:TRIG:VOLT?')

    @Feat()
    def trig_pos(self):
        """
        Returns the trigger out position in pattern mode, returning the segment number.
        """
        return self.query('PULS:TRIG:POS?')

    @Feat(values=TRIG_MODE_VALS)
    def trig_mode(self):
        """
        Returns the trigger out generation mode in pattern mode.
        """
        return self.query('PULS:TRIG:MODE?')

    @trig_mode.setter
    def trig_mode(self, trigger_mode):
        """
        Sets the trigger out generation mode (pattern mode only). Options are
        continuous or start.
        """
        return self.write('PULS:TRIG:MODE {}'.format(trigger_mode))


    def encode_data(self, data_series):
        """
        Helper function to implement IEEE 488.2 7.7.6.2 program data protocol.

        Encodes data_series (numpy byte array) into format that can be read by PPG.
        """
        # starts with # character
        data_string = '#'

        # hack to avoid issues w/ ellipses in large np arrays
        np.set_printoptions(threshold=65536)

        raw_data = np.array_str(data_series, max_line_width=65536)

        np.set_printoptions(threshold=1000)
        # figure out length of data_series
        data_length = data_series.size
        # figure out length of length of data_series
        len_data_length = len(str(data_length))

        # add all this stuff
        data_string += str(len_data_length)
        data_string += str(data_length)

        # TODO: fix import
        #max_line_width avoids adding newline or whitespace
        #raw_data = np.array_str(data_series, max_line_width=1000000)

        data_string += raw_data[1:-1:2] #strips out left bracket, right bracket, and spaces

        return data_string

    def decode_data(self, encoded_series):
        """
        Helper function to implement IEEE 488.2 7.7.6.2 program data protocol.

        Decodes encoded_series from PPG into raw data that can be read.
        """

        if encoded_series[0] != '#':

            print('invalid encoded series!')

        len_len = int(encoded_series[1])

        char_list = list(encoded_series[2+len_len:])

        return [int(x) for x in char_list]


    def preview_wfm(self):

        import matplotlib.pyplot as plt

        # code to figure out timeseries + number of points
        loop_start = self.start_seg
        loop_len = self.loop_length

        segments = [loop_start]
        current_seg = loop_start

        # probably not the best way possible to do this, but it works...
        while loop_len > 1:
            current_seg += 1
            loop_len -= 1

            if current_seg > 4:
                segments.append(current_seg % 4)

            else:
                segments.append(current_seg)

        patt_length = 0

        for seg in segments:
            patt_length += self.dig_patt_length[seg]
            print('seg{}:{}'.format(seg, self.dig_patt_length[seg]))

        print('Total length:{}'.format(patt_length))

        freq  = self.frequency
        t = np.arange(0, patt_length, 1)/freq

        chan1 = np.zeros(patt_length)
        chan2 = np.zeros(patt_length)

        current_index = 0

        for seg in segments:

            seg_type_1 = self.dig_patt_type[(1, seg)]
            seg_type_2 = self.dig_patt_type[(2, seg)]
            length = self.dig_patt_length[seg]

            if seg_type_1 == 'low':
                chan1[current_index:current_index+length] = 0

            elif seg_type_1 == 'high':
                chan1[current_index:current_index+length] = 1

            elif seg_type_1 == 'data':
                chan1[current_index:current_index+length] = self.segment_data[(1,seg)]


            if seg_type_2 == 'low':
                chan2[current_index:current_index+length] = 0

            elif seg_type_2 == 'high':
                chan2[current_index:current_index+length] = 1

            elif seg_type_2 == 'data':
                chan2[current_index:current_index+length] = self.segment_data[(2, seg)]

            current_index += length
            #chan1 = np.zeros()
            #chan2 = np

        def square(t_val, tmax):
            """
            Square wave helper function for plotting trigger output
            """

            if t_val < tmax/2.0:
                return 1
            else:
                return 0
        vectorized_square = np.vectorize(square) #vectorize because :gottagofast:

        plt.figure(1)
        plt.subplot(311)
        plt.ylabel('$T_0$')
        axes = plt.gca()
        axes.step(t, vectorized_square(t, t.max()), 'k-', where='mid')
        axes.set_ylim([-0.5,1.5])

        # now plot series from channel 1
        plt.subplot(312)
        plt.ylabel('Channel 1')
        axes = plt.gca()
        axes.step(t, chan1, 'r--', where='mid')
        axes.set_ylim([-0.5,1.5])

        # plot series from channel 2
        plt.subplot(313)
        plt.ylabel('Channel 2')
        axes = plt.gca()
        axes.step(t, chan2, 'r--', where='mid')
        axes.set_ylim([-0.5,1.5])
        #plt.show()

    @Action()
    def odmr_waveform(self, preview_wfm=False, ref_freq=503.0):

        ref_freq = 503.0
        print('Setting up ODMR waveforms')

        print('Identification: {}'.format(self.idn))
        self.reset() #initializes default parameters for clean setup
        self.display = 'off'
        print('Display off?: {}'.format(self.display))

        self.pattern_mode = 'on'
        print('Digital pattern mode on?:{}'.format(self.pattern_mode))

        self.arm_source = 'immediate' # sets continuous operation
        print('Arm source immediate?: {}'.format(self.arm_source))

        # output TTL pulses for RF switch on channel 1
        # TTL pulses should be between 0 (low) and 2.5 (high) volts
        # so set up channel 1 output like this
        self.volt_low[1] = 0.0
        self.volt_high[1] = 2.5

        print('High voltage, should be 2.5 V:{}'.format(self.volt_high[1]))
        print('Low voltage, should be 0 V:{}'.format(self.volt_low[1]))


        self.volt_low[2] = 0.0
        self.volt_high[2] = 1.0

        print('High voltage, should be 1.0 V:{}'.format(self.volt_high[2]))
        print('Low voltage, should be 0 V:{}'.format(self.volt_low[2]))

        self.data_format[1] = 'nrz'
        self.data_format[2] = 'nrz'


        #ref_freq = 503.0 #Hz
        # since we have two pieces to the square wave, the frequency generator should
        # be set to use at least twice the references.

        self.frequency = 2*ref_freq
        self.dig_patt_length[1] = 4

        self.dig_patt_type[(2,1)] = 'high'
        self.dig_patt_type[(1,1)] = 'data'

        self.write('DIG:PATT:SEGM1:PRES1 2, 2')

        #self.segment_data[2,1] = [np.ones(4)]

        print('Internal PLL frequency:{}'.format(self.frequency))

        #print(self.segment_data[1,1])

        #print(self.segment_data[2,1])

        #self.output_on[1] = 'on'
        #self.output_on[2] = 'on'

        print(self.output_on[1])
        print(self.output_on[2])

        self.output_on[1] = 'on'
        self.output_on[2] = 'on'

        print(self.output_on[1])
        print(self.output_on[2])

        print(self.output_on[2])
        print(self.output_on[2])


        #self.dig_patt_length[2] = scale_factor
        # ignore last two segments
        #self.dig_patt_length[3] = 0
        #self.dig_patt_length[4] = 0

        #for i in range(1,5):
        #    print('Segment {} length: {}'.format(i, self.dig_patt_length[i]))
        #if preview_wfm:
        #    self.preview_wfm()
        # configure two segements, one where channel 1 is high + one where channel 1 is low
        #self.dig_patt_type[(1, 1)] = 'high'
        #print('Channel {}, segment {} type:{}'.format(1, 1, self.dig_patt_type[(1, 1)]))
        #self.dig_patt_type[(1, 2)] = 'low'
        #print('Channel {}, segment {} type:{}'.format(1, 2, self.dig_patt_type[(1, 2)]))


        # external sync goes to TTL ref in on back of lockin
        print('TODO: check that the output on the scope of this is actually reasonable')


    def outputs_high(self, preview_wfm=False, ref_freq=503.0):

        ref_freq = 10e6
        print('PPG all outputs high!')

        print('Identification: {}'.format(self.idn))
        self.reset() #initializes default parameters for clean setup
        self.display = 'off'
        print('Display off?: {}'.format(self.display))

        self.pattern_mode = 'on'
        print('Digital pattern mode on?:{}'.format(self.pattern_mode))

        self.arm_source = 'immediate' # sets continuous operation
        print('Arm source immediate?: {}'.format(self.arm_source))

        # output TTL pulses for RF switch on channel 1
        # TTL pulses should be between 0 (low) and 2.5 (high) volts
        # so set up channel 1 output like this
        self.volt_low[1] = 0.0
        self.volt_high[1] = 2.5

        print('High voltage, should be 2.5 V:{}'.format(self.volt_high[1]))
        print('Low voltage, should be 0 V:{}'.format(self.volt_low[1]))


        self.volt_low[2] = 0.0
        self.volt_high[2] = 1.0

        print('High voltage, should be 1.0 V:{}'.format(self.volt_high[2]))
        print('Low voltage, should be 0 V:{}'.format(self.volt_low[2]))

        self.data_format[1] = 'nrz'
        self.data_format[2] = 'nrz'


        #ref_freq = 503.0 #Hz
        # since we have two pieces to the square wave, the frequency generator should
        # be set to use at least twice the references.

        self.frequency = 2*ref_freq
        self.dig_patt_length[1] = 4

        self.dig_patt_type[(2,1)] = 'high'
        self.dig_patt_type[(1,1)] = 'high'


        #self.segment_data[2,1] = [np.ones(4)]

        print('Internal PLL frequency:{}'.format(self.frequency))

        #print(self.segment_data[1,1])

        #print(self.segment_data[2,1])

        #self.output_on[1] = 'on'
        #self.output_on[2] = 'on'

        print(self.output_on[1])
        print(self.output_on[2])

        self.output_on[1] = 'on'
        self.output_on[2] = 'on'

        print(self.output_on[1])
        print(self.output_on[2])

        print(self.output_on[2])
        print(self.output_on[2])




    def rabi_waveform_step(inst, step_number):
        # helper function to program the second segment of PPG waveforms to perform Rabi
        #print('not implemented yet!')

        #inst.output_on[1] = 'off'
        #inst.output_on[2] = 'off'

        #inst.comp_output_on[1] = 'off'

        print(step_number)
        T_init = 13200
        T_rabi_max = 224
        T_readout = 13200

        off_len = T_rabi_max/2 - step_number
        on_len = 2*step_number

        data = [np.hstack((np.zeros(off_len, dtype='int'), np.ones(on_len, dtype='int'), np.zeros(off_len, dtype='int')))]
        print(data)

        #readout = [np.hstack((np.ones(T_readout + T_init, dtype='int'), np.zeros(T_rabi_max, dtype='int'), np.ones(T_readout, dtype='int')))]

        #inst.segment_data[(1,2)] = data


        encoded = inst.encode_data(data[0])

        seg_num = 2
        channel = 1

        inst.write('DIG:PATT:SEGM{}:DATA{} {}'.format(seg_num, channel, encoded))

        print('Channel {}, segment {} data:'.format(1, 2, inst.segment_data[(1,2)]))

        #inst.output_on[2] = 'on'


        return -1

    def rabi_waveform_setup(inst, rabi_params):

        # unpack measurement paramters
        #T_init = rabi_params['T_init']
        #T_readout = rabi_params['T_readout']

        print('Running Rabi waveform')

        print('Identification: {}'.format(inst.idn))
        inst.reset() #initializes default parameters for clean setup
        inst.display = 'off'
        print('Display off?: {}'.format(inst.display))

        inst.pattern_mode = 'on'
        print('Digital pattern mode on?:{}'.format(inst.pattern_mode))

        #inst.arm_source = 'immediate' # sets continuous operation
        #print('Arm source immediate?: {}'.format(inst.arm_source))



        inst.frequency = 660e6/20.0
        # output TTL pulses for RF switch on channel 1
        # TTL pulses should be between 0 (low) and 2.5 (high) volts
        # so set up channel 1 output like this
        inst.volt_low[1] = 0.0
        inst.volt_high[1] = 2.5
        print('MW TTL high voltage, should be 2.5 V:{}'.format(inst.volt_high[1]))
        print('MW TTL low voltage, should be 0 V:{}'.format(inst.volt_low[1]))

        inst.data_format[1] = 'nrz'
        inst.output_on[1] = 'on'
        inst.comp_output_on[1] = 'on' #for scope viewing


        # set up laser channel
        inst.volt_low[2] = 0.0
        inst.volt_high[2] = 1.0
        print('AOM high voltage, should be 1.0 V:{}'.format(inst.volt_high[2]))
        print('AOM Low voltage, should be 0 V:{}'.format(inst.volt_low[2]))

        inst.data_format[2] = 'nrz'
        inst.output_on[2] = 'on'

        print('Trigger type:{}'.format(inst.trig_output))


        #inst.timed_delay[1] = 100e-9 #ns
        #inst.timed_delay[2] = 250e-9 #ns

        print('Channel 1 timed_delay:{}'.format(inst.timed_delay[1]))
        print('Channel 2 timed_delay:{}'.format(inst.timed_delay[2]))
        # set up 3 different segments
        # start at segment 1 and loop through all 3 segments

        T_init = 13200
        T_rabi_max = 224
        T_readout = 13200

        # Segment 1 - laser initializes spin for T_init
        inst.dig_patt_length[1] = T_init
        #print('Segment {} length:{}'.format(1, inst.dig_patt_length[1]))

        # Segment 1 - RF off
        inst.dig_patt_type[(1, 1)] = 'low'
        #print('Channel {}, segment {} type:{}'.format(1, 1, inst.dig_patt_type[(1, 1)]))

        # Segment 1 - laser on, initializing spin
        inst.dig_patt_type[(2, 1)] = 'high'
        #print('Channel {}, segment {} type:{}'.format(2, 1, inst.dig_patt_type[(2, 1)]))


        # Segment 2 - apply variable length RF pulse

        # 2 rf is on for variable time tau_rf
        inst.dig_patt_length[2] = T_rabi_max
        #print('Segment {} length:{}'.format(2, inst.dig_patt_length[2]))

        inst.dig_patt_type[(1,2)] = 'data'
        #print('Channel {}, segment {} type:{}'.format(1, 2, inst.dig_patt_type[(1, 2)]))

        # Set up segment 2 RF - initial point is with no RF on
        inst.segment_data[(1,2)] = [np.zeros(T_rabi_max, dtype='int')]

        #print('Channel {}, segment {} data:'.format(1, 2, inst.segment_data[(1,2)]))

        # Segment 2 - laser is off
        inst.dig_patt_type[(2, 2)] = 'low'
        #print('Channel {}, segment {} type:{}'.format(2, 2, inst.dig_patt_type[(2, 2)]))

        # Segment 3 - laser reads out, initializes, waits, reads out
        inst.dig_patt_length[3] = T_rabi_max + T_init + 2 * T_readout
        #print('Segment {} length:{}'.format(3, inst.dig_patt_length[3]))

        # Segment 3 - RF is always off
        inst.dig_patt_type[(1, 3)] = 'low'
        #print('Channel {}, segment {} type:{}'.format(1, 3, inst.dig_patt_type[(1, 3)]))

        # Segment 3 - laser initializes, waits, reads out
        inst.dig_patt_type[(2, 3)] = 'data'
        #print('Channel {}, segment {} type:{}'.format(2, 3, inst.dig_patt_type[(2, 3)]))

        readout1 = [np.hstack((np.ones(T_readout + T_init, dtype='int'), np.zeros(T_rabi_max, dtype='int')))]

        print(inst.dig_patt_length)
        #print(readout[0].shape)

        inst.segment_data[(2,3)] = readout1 #[np.hstack((np.ones(T_readout + T_init, dtype='int'), np.zeros(T_rabi_max, dtype='int'), np.ones(T_readout, dtype='int')))]

        # Segment 3 - RF is always off
        inst.dig_patt_type[(1, 3)] = 'low'
        #print('Channel {}, segment {} type:{}'.format(1, 3, inst.dig_patt_type[(1, 3)]))

        # Segment 3 - laser initializes, waits, reads out
        inst.dig_patt_type[(2, 3)] = 'data'
        #print('Channel {}, segment {} type:{}'.format(2, 3, inst.dig_patt_type[(2, 3)]))

        inst.dig_patt_type[(1, 4)] = 'low'

        inst.dig_patt_type[(2, 4)] = 'data'

        readout2 = [np.hstack((np.ones(T_readout, dtype='int')))]

        print(inst.dig_patt_length)
        #print(readout[0].shape)

        inst.segment_data[(2,4)] = readout2 #[np.hstack((np.ones(T_readout + T_init, dtype='int'), np.zeros(T_rabi_max, dtype='int'), np.ones(T_readout, dtype='int')))]





        # sets PPG to loop through segments 1-3 repeatedly
        inst.loop_start = 1
        inst.loop_length = 3

        print('Trigger source?: {}'.format(inst.trigger_source))

        inst.trigger_source = 'internal'
        print('Trigger source?: {}'.format(inst.trigger_source))


        print('trigger mode:{}'.format(inst.trig_mode))


        print(inst.trig_output)
        print('trigger position:{}'.format(inst.trig_pos))

        #from time import sleep

        #sleep(10)

        #inst.write('ARM:SOUR MAN')
        #inst.write('ARM:MODE STAR')

        #inst.write('DIG:PATT:LOOP:INF ON')
        #inst.write('DIG:PATT:INST:STAR SEGM1')
        #inst.write('DIG:PATT:LOOP:LENG 3')

        #inst.preview_wfm()
        #
        # data = np.random.randint(2, size=100, dtype=np.uint8)
        # encoded = inst.encode_data(data)
        #
        # print('Data:{}'.format(data))
        # print('Encoded:{}'.format(encoded))
        #
        # decoded = inst.decode_data('{}'.format(encoded))
        # print('Decoded:{}'.format(decoded))
        # for segment in segments:
        #
        #     segment_length = inst.dig_patt_length[segment]
        #
        #     for channel in [1,2]:
        #
        #         v_high = inst.volt_high[channel]
        #         v_low = inst.volt_low[channel]
        #
        #         segment_type = inst.dig_patt_type[(channel, segment)]
        #
        #         if segment_data == 'data':
        #             pass
        #             #data = inst.segment_data[(channel, segment)]
        #
        #
        #         #print(segment)
        #         #print(inst.segment_data[(channel, segment)])
        #
        #     #print(data)
        #     plt.plot(data)
        #     plt.xlabel('Time')
        #     plt.ylabel('Voltage')
        #     plt.show()


        # figure out these numbers!
        T_init = 1000 #us
        T_gap = 50 #us
        T_readout = 1000 #us

        tau_rf = 100*1e-3 #100 ns


        # program pattern of RF on for tau after T_init + T_gap / 2 - tau_rf




        # figure out how to vary tau_rf + have it still placed appropriately

    def pulse_odmr_setup(inst):
        """
        Sets up PPG output channels for pulsed ODMR measurements.
        """
        print('Identification: {}'.format(inst.idn))
        inst.reset() #initializes default parameters for clean setup
        inst.display = 'off'
        print('Display off?: {}'.format(inst.display))

        inst.pattern_mode = 'on'
        print('Digital pattern mode on?:{}'.format(inst.pattern_mode))

        #inst.arm_source = 'immediate' # sets continuous operation
        #print('Arm source immediate?: {}'.format(inst.arm_source))

        inst.frequency = 660e6
        # output TTL pulses for RF switch on channel 1
        # TTL pulses should be between 0 (low) and 2.5 (high) volts
        # so set up channel 1 output like this
        inst.volt_low[1] = 0.0
        inst.volt_high[1] = 2.5
        print('MW TTL high voltage, should be 2.5 V:{}'.format(inst.volt_high[1]))
        print('MW TTL low voltage, should be 0 V:{}'.format(inst.volt_low[1]))

        inst.data_format[1] = 'nrz'
        inst.output_on[1] = 'on'
        inst.comp_output_on[1] = 'on' #for scope viewing

        # set up laser channel
        inst.volt_low[2] = 0.0
        inst.volt_high[2] = 1.0
        print('AOM high voltage, should be 1.0 V:{}'.format(inst.volt_high[2]))
        print('AOM Low voltage, should be 0 V:{}'.format(inst.volt_low[2]))

        inst.data_format[2] = 'nrz'
        inst.output_on[2] = 'on'
        inst.comp_output_on[2] = 'on' #for scope viewing


        print('Trigger type:{}'.format(inst.trig_output))

        #inst.timed_delay[1] = 100e-9 #ns
        #inst.timed_delay[2] = 250e-9 #ns

        print('Channel 1 timed_delay:{}'.format(inst.timed_delay[1]))
        print('Channel 2 timed_delay:{}'.format(inst.timed_delay[2]))

    def rabi_step(inst, step_number):
        """
        Sets up next waveform point for Rabi
        """
        T_rabi_max = 4096

        data = [np.hstack((np.ones(step_number, dtype='int'), np.zeros(T_rabi_max - step_number, dtype='int')))]

        encoded = inst.encode_data(data[0])

        seg_num = 3
        channel = 1

        inst.write('DIG:PATT:SEGM{}:DATA{} {}'.format(seg_num, channel, encoded))


    def ramsey_setup(inst, ramsey_params, pi_pulse_len):

        T_ramsey_max = 6144
        T_init = 336*5 #~2.5us
        T_gap = 16*15 # segment 2, everything off
        T_readout = 336*5 #~2.5us

        pi_pulse = np.ones(pi_pulse_len, dtype='int')
        pad = np.zeros(T_ramsey_max - pi_pulse_len, dtype='int')


        # Segment 1 - RF off, laser on to initialize
        inst.dig_patt_length[1] = T_init
        inst.dig_patt_type[(1, 1)] = 'low'
        inst.dig_patt_type[(2, 1)] = 'high'

        # Segment 2 - gap, everything is off
        inst.dig_patt_length[2] = T_gap
        inst.dig_patt_type[(1,2)] = 'low'
        inst.dig_patt_type[(2,2)] = 'low'

        # Segment 3 - laser is off, variable length RF pulse
        inst.dig_patt_length[3] = T_ramsey_max
        inst.dig_patt_type[(2, 3)] = 'low'
        inst.dig_patt_type[(1,3)] = 'data'

        # Set up segment 2 RF - initial point is pi pulse w/o separation


        inst.segment_data[(1,3)] = [np.hstack((pi_pulse, pad))]

        # Segment 4 - laser reads out
        inst.dig_patt_length[4] = T_readout
        # Segment 4 - RF is always off, laser on
        inst.dig_patt_type[(1, 4)] = 'low'
        inst.dig_patt_type[(2, 4)] = 'high'


    def ramsey_step(inst, ramsey_params, pi_pulse_len, tau):

        T_ramsey_max = 6144


        pi_pulse = np.ones(pi_pulse_len, dtype='int')

        pi2_pulse = np.ones(int(pi_pulse_len/2), dtype='int')

        delay = np.zeros(tau, dtype='int')

        pad = np.zeros((T_ramsey_max - (tau + pi_pulse_len)), dtype='int')

        data = np.hstack((pi2_pulse, delay, pi2_pulse, pad))

        seg_num = 3
        channel = 1

        encoded = inst.encode_data(data)

        inst.write('DIG:PATT:SEGM{}:DATA{} {}'.format(seg_num, channel, encoded))



    def hahn_setup(inst, hahn_params):

        freq = hahn_params['ppg_freq']
        inst.frequency = freq

        conversion = freq / 660e6

        T_hahn_max = hahn_params['T_hahn_max']
        T_init = int(hahn_params['T_init'] * conversion)
        T_gap = int(hahn_params['T_gap'] * conversion)
        T_readout = int(hahn_params['T_readout'] * conversion)
        tau_min = int(hahn_params['tau_min'] * conversion)


        pi_pulse_len = 2

        pad = np.zeros(int((T_hahn_max - 2*pi_pulse_len - tau_min)/2.0), dtype='int')


        pi_pulse = np.ones(pi_pulse_len, dtype='int')
        pi2_pulse = np.ones(int(pi_pulse_len/2), dtype='int')
        tau2 = np.zeros(int(tau_min/2), dtype='int')

        # Segment 1 - RF off, laser on to initialize
        inst.dig_patt_length[1] = T_init
        inst.dig_patt_type[(1, 1)] = 'low'
        inst.dig_patt_type[(2, 1)] = 'high'

        # Segment 2 - gap, everything is off
        inst.dig_patt_length[2] = T_gap
        inst.dig_patt_type[(1,2)] = 'low'
        inst.dig_patt_type[(2,2)] = 'low'

        # Segment 3 - laser is off, pi/2, tau, pi, -pi/2 pulses
        inst.dig_patt_length[3] = T_hahn_max
        inst.dig_patt_type[(2, 3)] = 'low'

        inst.dig_patt_type[(1,3)] = 'data'


        hahn_data = np.hstack((pad, pi2_pulse, tau2, pi_pulse, tau2,
                               pi2_pulse, pad))

        print(T_hahn_max)
        print(hahn_data.shape)


        inst.segment_data[(1,3)] = [hahn_data]


        # Segment 4 - laser reads out
        inst.dig_patt_length[4] = T_readout
        # Segment 4 - RF is always off, laser on
        inst.dig_patt_type[(1, 4)] = 'low'
        inst.dig_patt_type[(2, 4)] = 'high'




    def hahn_step(inst, hahn_params, tau):

        T_hahn_max = hahn_params['T_hahn_max']
        pi_pulse_len = hahn_params['pi_pulse_len']

        pi_pulse = np.ones(pi_pulse_len, dtype='int')
        pi2_pulse = np.ones(int(pi_pulse_len/2), dtype='int')
        tau2 = np.zeros(int(tau/2), dtype='int')

        pad = np.zeros(int((T_hahn_max - 2*pi_pulse_len - tau)/2.0), dtype='int')

        hahn_data = np.hstack((pad, pi2_pulse, tau2, pi_pulse, tau2, pi2_pulse, pad))

        print(hahn_data.shape)

        seg_num = 3
        channel = 1

        encoded = inst.encode_data(hahn_data)

        inst.write('DIG:PATT:SEGM{}:DATA{} {}'.format(seg_num, channel, encoded))

        inst.segment_data[(channel, seg_num)]

        return

    def rabi_setup(inst):
        """
        Sets up pulse sequence for doing Rabi
        """
        T_init = 336*6 #500 ns
        T_gap = 16*15 # segment 2, everything off
        T_rabi_max = 4096

        T_readout = 336*6 # 500 ns


        # Segment 1 - RF off, laser on to initialize
        inst.dig_patt_length[1] = T_init
        inst.dig_patt_type[(1, 1)] = 'low'
        inst.dig_patt_type[(2, 1)] = 'high'

        # Segment 2 - gap, everything is off
        inst.dig_patt_length[2] = T_gap
        inst.dig_patt_type[(1,2)] = 'low'
        inst.dig_patt_type[(2,2)] = 'low'

        # Segment 3 - laser is off, variable length RF pulse
        inst.dig_patt_length[3] = T_rabi_max
        inst.dig_patt_type[(2, 3)] = 'low'
        inst.dig_patt_type[(1,3)] = 'data'

        # Set up segment 2 RF - initial point is with no RF on
        inst.segment_data[(1,3)] = [np.zeros(T_rabi_max, dtype='int')]

        # Segment 4 - laser reads out
        inst.dig_patt_length[4] = T_readout
        # Segment 4 - RF is always off, laser on
        inst.dig_patt_type[(1, 4)] = 'low'
        inst.dig_patt_type[(2, 4)] = 'high'

        print('Trigger source?: {}'.format(inst.trigger_source))

        inst.trigger_source = 'internal'
        print('Trigger source?: {}'.format(inst.trigger_source))


        print('trigger mode:{}'.format(inst.trig_mode))


        print(inst.trig_output)
        print('trigger position:{}'.format(inst.trig_pos))


    def calibrate_pi_setup(inst, downconversion_rate):

        inst.frequency = 660e6 / downconversion_rate
        print(inst.frequency)


        T_init = int(336*6 / downconversion_rate) #500 ns
        T_gap = int(16*15 / downconversion_rate) # segment 2, everything off
        T_rabi_max = int(4096 / downconversion_rate)

        T_readout = int(336*6 / downconversion_rate) # 500 ns


        # Segment 1 - RF off, laser on to initialize
        inst.dig_patt_length[1] = T_init
        inst.dig_patt_type[(1, 1)] = 'low'
        inst.dig_patt_type[(2, 1)] = 'high'

        # Segment 2 - gap, everything is off
        inst.dig_patt_length[2] = T_gap
        inst.dig_patt_type[(1,2)] = 'low'
        inst.dig_patt_type[(2,2)] = 'low'

        # Segment 3 - laser is off, variable length RF pulse
        inst.dig_patt_length[3] = T_rabi_max
        inst.dig_patt_type[(2, 3)] = 'low'
        inst.dig_patt_type[(1,3)] = 'data'

        # Set up segment 2 RF - initial point is with no RF on
        num_pulses = 5

        data = np.hstack((np.ones(2*num_pulses, dtype='int'), np.zeros(T_rabi_max - 2*num_pulses, dtype='int')))

        inst.segment_data[(1,3)] = [data]

        # Segment 4 - laser reads out
        inst.dig_patt_length[4] = T_readout
        # Segment 4 - RF is always off, laser on
        inst.dig_patt_type[(1, 4)] = 'low'
        inst.dig_patt_type[(2, 4)] = 'high'

        inst.trigger_source = 'internal'

        return




if __name__ == '__main__':

    test_wfm = True
    test_rabi = False
    test_comm = False

    gpib_addr = 10

    with Ag81130A('GPIB0::{}::INSTR'.format(gpib_addr)) as inst:

        #inst.preview_wfm()

        if test_wfm:
            inst.odmr_waveform()

        elif test_rabi:

            rabi_waveform_test(inst)

        elif test_comm:

            print('Identification: {}'.format(inst.idn))
            inst.reset()
            print('Display: {}'.format(inst.display))
            inst.display = 'off'
            print('Display: {}'.format(inst.display))

            print('Digital pattern mode: {}'.format(inst.pattern_mode))
            inst.pattern_mode = 'on'
            print('Digital pattern mode: {}'.format(inst.pattern_mode))

            print('Arm source: {}'.format(inst.arm_source))
            inst.arm_source = 'manual'
            print('Arm source: {}'.format(inst.arm_source))
            inst.arm_source = 'immediate'
            print('Arm source: {}'.format(inst.arm_source))


            for segment in range(1,5):
                print('Segment {} length:{}'.format(segment, inst.dig_patt_length[segment]))
                inst.dig_patt_length[segment] = 100
                print('Segment {} length:{}'.format(segment, inst.dig_patt_length[segment]))



            for channel in [1,2]:
                print('Channel {} high:{}V'.format(channel, inst.volt_high[channel]))
                inst.volt_high[channel] = 3.0
                print('Channel {} high:{}V'.format(channel, inst.volt_high[channel]))
                inst.volt_high[channel] = 2.5
                print('Channel {} high:{}V'.format(channel, inst.volt_high[channel]))

                print('Channel {} low:{}V'.format(channel, inst.volt_low[channel]))
                inst.volt_low[channel] = -1.0
                print('Channel {} low:{}V'.format(channel, inst.volt_low[channel]))
                inst.volt_low[channel] = 0.0
                print('Channel {} low:{}V'.format(channel, inst.volt_low[channel]))

                for segment in range(1,5):

                    inst.dig_patt_type[(channel, segment)] = 'high'
                    print('Channel {}, segment {} type:{}'.format(channel, segment, inst.dig_patt_type[(channel, segment)]))

                print('Channel format:{}'.format(inst.data_format[channel]))
                inst.data_format[channel] = 'nrz'
                print('Channel format:{}'.format(inst.data_format[channel]))

                print('Channel output:{}'.format(inst.output_on[channel]))
                inst.output_on[channel] = 'on'
                print('Channel output:{}'.format(inst.output_on[channel]))
