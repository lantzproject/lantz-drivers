"""
    lantz.drivers.keysight.e8364b
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Drivers for the E8364B Network Analyzer using RAW SOCKETS

    Authors: Alexandre Bourassa
    Date: 24/03/2016
"""
import numpy as _np

from lantz import Feat, DictFeat, Action
from lantz.feat import MISSING
from lantz.errors import InstrumentError
from lantz.messagebased import MessageBasedDriver

class E8364B(MessageBasedDriver):
    """E8364B Network Analyzer
    """


    DEFAULTS = {'COMMON': {'write_termination': '\n',
                           'read_termination': '\n',
                           'timeout':10000,}}

    @Feat(read_once=True)
    def idn(self):
        return self.query('*IDN?')

# ----------------------------------------------------
#       Sweep Settings functions
# ----------------------------------------------------

    @Feat(units='Hz')
    def center_frequency(self):
        """Center Frequency
        """
        return float(self.query('SENS:FREQ:CENT?'))

    @center_frequency.setter
    def center_frequency(self, value):
        self.write('SENS:FREQ:CENT {}'.format(int(value)))


    @Feat(units='Hz')
    def span(self):
        """Span of the sweep
        """
        return float(self.query('SENS:FREQ:SPAN?'))

    @span.setter
    def span(self, value):
        self.write('SENS:FREQ:SPAN {}'.format(int(value)))

    @Feat(units='Hz')
    def if_bandwidth(self):
        """Bandwidth of the digital IF filter
        """
        return float(self.query('SENS:BAND?'))

    @if_bandwidth.setter
    def if_bandwidth(self, value):
        self.write('SENS:BAND {}'.format(int(value)))

    @Feat(limits=(1, 16001, 1))
    def nb_points(self):
        """The number of data points for the measurement
        """
        return int(self.query('SENS:SWE:POIN?'))

    @nb_points.setter
    def nb_points(self, points):
        self.write('SENS:SWE:POIN {}'.format(int(points)))

    ALLOWED_MEAS_TYPE = {"S11", "S12", "S21", "S22"}
    @Feat(values=ALLOWED_MEAS_TYPE)
    def meas_type(self):
        return self.get_measurement_catalog()['CH1_S11_1']

    @meas_type.setter
    def meas_type(self, meas_type):
        self.write("CALC:PAR:MOD {}".format(meas_type))


# ----------------------------------------------------
#       Power functions
# ----------------------------------------------------

    @Feat(values={True: 1, False: 0})
    def power_on(self):
        """RF Power State (True==ON or False==OFF)
        """
        return int(self.query('OUTP?'))

    @power_on.setter
    def power_on(self, state=True):
        self.write('OUTP {}'.format(state))

    @Feat()
    def power_level(self):
        """RF Power level in dBm
        """
        return float(self.query("SOUR:POW?"))

    @power_level.setter
    def power_level(self, level):
        self.write("SOUR:POW {}".format(level))

    ## Possibly not available on this model...
    # @Feat(values={True: 1, False: 0})
    # def manual_noise_on(self):
    #     """RF Power State (True==ON or False==OFF)
    #     """
    #     return int(self.query('OUTP:MAN:NOIS?'))
    #
    # @manual_noise_on.setter
    # def manual_noise_on(self, state=True):
    #     if state:   state_str = 'ON'
    #     else:       state_str = 'OFF'
    #     self.write('OUTP:MAN:NOIS ' + state_str)

#----------------------------------------------------
#       Averaging functions
#----------------------------------------------------

    @Feat(values={True: 1, False: 0})
    def average_on(self):
        """Averaging state (True==ON or False==OFF)
        """
        return int(self.query('SENS:AVER:STAT?'))

    @average_on.setter
    def average_on(self, state=True):
        self.write('SENS:AVER:STAT {}'.format(state))

    @Feat(limits=(1,65536, 1))
    def average_count(self):
        """Averaging count
        """
        return int(self.query('SENS:AVER:COUN?'))

    @average_count.setter
    def average_count(self, counts):
        self.write('SENS:AVER:COUN {}'.format(int(counts)))

    @Action()
    def clear_average(self):
        """Reset the averaging
        """
        self.write('SENS:AVER:CLE')



#----------------------------------------------------
#       Data Query functions
#----------------------------------------------------
    @Feat(values={"REAL32":"REAL,+32", "REAL64":"REAL,+64", "ASCII":"ASC,+0"})
    def data_format(self):
        return self.query("FORM:DATA?")

    @data_format.setter
    def data_format(self, value):
        self.write('FORM:DATA {}'.format(value))

    def query_data(self, command, use_cached=True):
        # For quick data acquisition, let's assume data format as not changed since last query
        form = self.recall('data_format') if use_cached else self.data_format
        if form is MISSING: return _np.array([])
        if form == "REAL64":
            return _np.array(self.resource.query_binary_values(command, datatype='d', is_big_endian=True))
        elif form == "REAL32":
            return _np.array(self.resource.query_binary_values(command, datatype='f', is_big_endian=True))
        elif form == "ASCII":
            return _np.array(list(map(float, self.query(command).split(','))))
        else:
            raise Exception(str(form) + "Invalid data format")

    @Action()
    def x_data(self):
        return self.query_data('SENS:X?')

    @Action()
    def y_data(self):
        data = self.query_data("CALC:DATA? SDATA")
        data = data[::2]+data[1::2]*1j
        return data


# ----------------------------------------------------
#       Traces and Channel functions (Complicates the remote use of the device
#       so don't use unless you know what you are doing...)
#       For simplicity, we will always use CH1 and parameter name 'CH1_S11_1'
# ----------------------------------------------------
    def clear_all_traces(self):
        self.write('SYST:FPR')
        self.write('DISP:WIND:STAT ON')

    def create_new_measurement(self, name='CH1_S11_1', meas_type="S11"):
        if not meas_type in self.ALLOWED_MEAS_TYPE: raise Exception("Invalid meas_type: "+str(meas_type))
        self.write("CALC:PAR:DEF '"+name+"',"+meas_type)
        self.write("DISP:WIND:TRAC:FEED '"+name+"'")


    def get_measurement_catalog(self):
        response = self.query("CALC:PAR:CAT?").translate({ord('"'):None}).split(',')
        ans = dict()
        for i in range(int(len(response)/2)):
            ans[response[2*i]]=response[2*i+1]
        return ans

    def select_measurement(self, name):
        self.write("CALC:PAR:SEL '{}'".format(name))

# ----------------------------------------------------
#       Misc. functions
# ----------------------------------------------------

    @Action()
    def initialize(self):
        super(E8364B, self).initialize()
        meas = self.get_measurement_catalog()
        if not 'CH1_S11_1' in meas:
            self.clear_all_traces()
            self.create_new_measurement(name='CH1_S11_1', meas_type="S11")

        self.select_measurement('CH1_S11_1')
        self.data_format = 'REAL64'















