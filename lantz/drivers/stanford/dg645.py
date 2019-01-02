# -*- coding: utf-8 -*-
"""
    lantz.drivers.stanford.dg645
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Implementation of DG645 digital delay generator
    Author: Kevin Miao & Berk Diler
    Date: 1/14/2016 & 11/08/2017
"""

from collections import OrderedDict
from lantz import Action, Feat, DictFeat, Q_
from lantz.messagebased import MessageBasedDriver

class DGException(Exception):
    pass

class DG645(MessageBasedDriver):

    DEFAULTS = {
        'COMMON': {
            'write_termination': '\r\n',
            'read_termination': '\r\n',
        }
    }

    ERRORS = OrderedDict([
                   ('NO ERROR', 0),
                   ('EXECUTION ERROR: Illegal Value. \n'
                    'Parameter was out of range.', 10),
                   ('EXECUTION ERROR: Illegal Mode. \n'
                    'The action is illegal in the current mode. This might happen, for instance, if a single shot '
                    'is requested when the trigger source is not single shot.', 11),
                   ('EXECUTION ERROR: Illegal Delay. \n'
                    'The requested delay is out of range.', 12),
                   ('EXECUTION ERROR: Illegal Link. \n'
                    'The requested delay linkage is illegal.', 13),
                   ('EXECUTION ERROR: Recall Failed. \n'
                    'The recall of instrument settings from nonvolatile storage failed. '
                    'The instrument settings were invalid. ', 14),
                   ('EXECUTION ERROR: Not Allowed \n'
                    'The requested action is not allowed because the instrument is locked by another interface.', 15),
                   ('EXECUTION ERROR: Failed Self Test. \n'
                    'The DG645 self test failed.', 16),
                   ('EXECUTION ERROR: Failed Auto Calibration \n'
                    'The DG645 auto calibration failed.', 17),
                   ('QUERY ERROR: Lost Data \n'
                    'Data in the output buffer was lost. This occurs if the output buffer overflows, or if a'
                    'communications error occurs and data in output buffer is discarded. ', 30),
                   ('QUERY ERROR: No Listener \n'
                    'This is a communications error that occurs if the DG645 is addressed to talk on the GPIB '
                    'bus, but there are no listeners. The DG645 discards any pending output. ', 32),
                   ('PARSING ERROR: Illegal Command. \n'
                    'The command syntax used was illegal. A command is normally a sequence of four letters, '
                    'or a ‘*’ followed by three letters.', 110),
                   ('PARSING ERROR: Undefined Command. \n'
                    'The specified command does not exist.', 111),
                   ('PARSING ERROR: Illegal Query. \n'
                    'The specified command does not permit queries.', 112),
                   ('PARSING ERROR: Illegal Set. \n'
                    'The specified command can only be queried.', 113),
                   ('PARSING ERROR: Null Parameter. \n'
                    'The parser detected an empty parameter.', 114),
                   ('PARSING ERROR: Extra Parameters \n'
                    'The parser detected more parameters than allowed by the command.', 115),
                   ('PARSING ERROR: Missing Parameters. \n'
                    'The parser detected missing parameters required by the command.', 116),
                   ('PARSING ERROR: Parameter Overflow \n'
                    'The buffer for storing parameter values overflowed. This probably indicates a syntax error.', 117),
                   ('PARSING ERROR: Invalid Floating Point Number \n'
                    'The parser expected a floating point number, but was unable to parse it.', 118),
                   ('PARSING ERROR: Invalid Integer  \n'
                    'The parser expected an integer, but was unable to parse it.', 120),
                   ('PARSING ERROR: Integer Overflow \n'
                    'A parsed integer was too large to store correctly.', 121),
                   ('PARSING ERROR: Invalid Hexadecimal \n'
                    'The parser expected hexadecimal characters but was unable to parse them.', 122),
                   ('PARSING ERROR: Syntax Error \n'
                    'The parser detected a syntax error in the command.', 126),
                   ('COMMUNICATION ERROR: Communication Error \n'
                    'A communication error was detected. This is reported if the hardware detects a framing, '
                    'or parity error in the data stream. ', 170),
                   ('COMMUNICATION ERROR: Over run \n '
                    'The input buffer of the remote interface overflowed. All data in both the input and output '
                    'buffers will be flushed. ', 171),
                   ('VERY SERIOUS ERROR: Too Many Errors  \n'
                    'You destroyed the instrument, throw it in the garbage. \n'
                    'Just kidding. Check your errors though.\n'
                    'Probably the error buffer is full. Subsequent errors have been dropped. ', 254),
    ])

    CHANNELS = OrderedDict([
                   ('T0', 0),
                   ('T1', 1),
                   ('A', 2),
                   ('B', 3),
                   ('C', 4),
                   ('D', 5),
                   ('E', 6),
                   ('F', 7),
                   ('G', 8),
                   ('H', 9)
                   ])

    OUTPUT_CHANNELS = OrderedDict([
                   ('T0', 0),
                   ('AB', 1),
                   ('CD', 2),
                   ('EF', 3),
                   ('GH', 4)
                   ])

    TRIGGER_CHANNELS = OrderedDict([
                   ('Internal', 0),
                   ('External Rising Edge', 1),
                   ('External Falling Edge', 2),
                   ('Single Shot External Rising Edge', 3),
                   ('Single Shot External Falling Edge', 4),
                   ('Single Shot', 5),
                   ('Line', 6)
                   ])

    @Feat(read_once=True)
    def idn(self):
        self.clear_errors()
        return self.query('*IDN?')

    @Action()
    def reset(self):
        self.clear_errors()
        self.write('*RST')

    # Error Commands
    @Feat(values=ERRORS)
    def error(self):
        return int(self.query("LERR?"))

    @Action()
    def clear_errors(self):
        err = self.error
        while err != "NO ERROR":
            raise DGException(err)
            err = self.error


    # Delay Commands

    @DictFeat(keys = CHANNELS, units="s")
    def delay(self, channel):
        retval = self.query('DLAY? {}'.format(channel))
        linked, offset = retval.split(',')
        self.clear_errors()
        return float(offset)

    @delay.setter
    def delay(self, channel, value):
        retval = self.query('DLAY? {}'.format(channel))
        linked, offset = retval.split(',')
        new_str = 'DLAY {},'+str(linked)+',{:1.12e}'
        self.write(new_str.format(channel,value))
        self.clear_errors()

    @DictFeat(keys = CHANNELS)
    def reference(self, channel):
        retval = self.query('DLAY? {}'.format(channel))
        linked, offset = retval.split(',')
        self.clear_errors()
        return list(self.CHANNELS.keys())[int(linked)]

    @reference.setter
    def reference(self, channel, reference):
        new_ref = self.CHANNELS[reference]
        retval = self.query('DLAY? {}'.format(channel))
        linked, offset = retval.split(',')
        new_str = 'DLAY {},{:d},' + offset
        args = channel, new_ref
        self.write(new_str.format(*args))
        self.clear_errors()

    @DictFeat(keys = OUTPUT_CHANNELS, units="V", limits=(0.5,5.0))
    def amplitude(self, channel):
        retval = self.query('LAMP?{}'.format(channel))
        self.clear_errors()
        return float(retval)

    @amplitude.setter
    def amplitude(self, channel, value):
        self.write("LAMP {},{:1.3e}".format(channel,value))
        self.clear_errors()

    @DictFeat(keys = OUTPUT_CHANNELS, units="V", limits=(-2.,2.))
    def offset(self, channel):
        retval = self.query('LOFF?{}'.format(channel))
        self.clear_errors()
        return float(retval)

    @offset.setter
    def offset(self, channel, value):
        self.write("LOFF {},{:1.2e}".format(channel,value))
        self.clear_errors()

    @DictFeat(keys = OUTPUT_CHANNELS, values={"POS" : 1, "NEG" : 0})
    def polarity(self,channel):
        answ = float(self.query("LPOL? {}".format(channel)))
        self.clear_errors()
        return answ

    @polarity.setter
    def polarity(self,channel,pol):
        self.write("LPOL {},{}".format(channel,pol))
        self.clear_errors()

    # Trigger Commands

    @Feat(values = TRIGGER_CHANNELS)
    def trigger_source(self):
        answ = float(self.query('TSRC?'))
        self.clear_errors()
        return answ

    @trigger_source.setter
    def trigger_source(self,src):
        self.write('TSRC {:d}'.format(src))
        self.clear_errors()

    @Feat(units = "Hz")
    def trigger_rate(self):
        answ = float(self.query("TRAT?"))
        self.clear_errors()
        return answ

    @trigger_rate.setter
    def trigger_rate(self,rate):
        self.write("TRAT {:d}".format(rate))
        self.clear_errors()

    @Feat(units="V", limits=(0,3.5))
    def trigger_level(self):
        answ = float(self.query("TLVL?"))
        self.clear_errors()
        return answ

    @trigger_level.setter
    def trigger_level(self, lvl):
        self.write("TLVL {:1.2e}".format(lvl))
        self.clear_errors()

    # BURST Commands

    @Feat(limits=(1, 2 ** 32 - 1))
    def burst_count(self):
        answ = self.query('BURC?')
        self.clear_errors()
        return answ

    @burst_count.setter
    def burst_count(self, value):
        self.write('BURC {:d}'.format(value))
        self.clear_errors()

    @Feat(units='s')
    def burst_delay(self):
        answ =self.query('BURD?')
        self.clear_errors()
        return answ

    @burst_delay.setter
    def burst_delay(self, value):
        self.write('BURD {:1.12e}'.format(value))
        self.clear_errors()

    @Feat(values={True: '1', False: '0'})
    def burst_mode(self):
        answ = self.query('BURM?')
        self.clear_errors()
        return answ

    @burst_mode.setter
    def burst_mode(self, value):
        self.write('BURM {:s}'.format(value))
        self.clear_errors()

    @Feat(units='s', limits=(100e-9, (2 ** 32 - 1) * 1e-8, 10e-9))
    def burst_period(self):
        answ = self.query('BURP?')
        self.clear_errors()
        return answ

    @burst_period.setter
    def burst_period(self, value):
        self.write('BURP {:1.12e}')
        self.clear_errors()

    @Feat(values={True: '1', False: '0'})
    def burst_config(self):
        answ = self.query('BURT?')
        self.clear_errors()
        return answ

    @burst_config.setter
    def burst_config(self, value):
        self.write('BURT {:s}'.format(value))
        self.clear_errors()