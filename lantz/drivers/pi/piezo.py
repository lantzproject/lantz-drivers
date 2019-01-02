"""
    lantz.drivers.pi.piezo
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Implements the drivers to control pi E-709 piezo motion controller
    via USB or via serial. It uses the PI General Command Set.

    For USB, one first have to install the driver from PI.
    :copyright: 2018, see AUTHORS for more details.
    :license: GPL, see LICENSE for more details.

    Source: Instruction Manual (PI)
"""

from lantz.feat import Feat
from lantz.action import Action
from lantz.messagebased import MessageBasedDriver
# from pyvisa import constants
from lantz import Q_, ureg
# from lantz.processors import convert_to
import time
import numpy as np
# import copy
from collections import OrderedDict

if __name__=='__main__':
    from error_codes import error_codes
else:
    from .error_codes import error_codes


def parse_line(line):
    line = line.strip()  # remove whitespace at end
    return line.split('=')


def parse_multi(message):
    '''Return an ordered dictionary containing the returned parameters'''
    assert isinstance(message, list)
    return OrderedDict([parse_line(line) for line in message])


class Piezo(MessageBasedDriver):
    """ PI piezo motion controller. It assumes all axes to have units um

    Important:
    before operating, ensure that the notch filters are set to the right 
    frequencies. These frequencies depend on the load on the piezo, and can 
    be determined in NanoCapture.
    
    Example:
    import numpy as np
    import lantz
    import visa
    import lantz.drivers.pi.piezo as pi
    rm = visa.ResourceManager('@py')
    lantz.messagebased._resource_manager = rm
    ureg = lantz.ureg
    try:
        lantzlog
    except NameError:
        #lantzlog = lantz.log.log_to_screen(level=lantz.log.INFO)
        lantzlog = lantz.log.log_to_screen(level=lantz.log.ERROR)

    import warnings
    warnings.filterwarnings(action='ignore')

    print('Available devices:', lantz.messagebased._resource_manager.list_resources())
    print('Connecting to: ASRL/dev/ttyUSB0::INSTR')
    stage = pi.Piezo('ASRL/dev/ttyUSB0::INSTR', axis='X',
        sleeptime_after_move=10*ureg.ms)
    stage.initialize()
    idn = stage.idn

    stage.servo = True
    stage.velocity = 10*ureg.um/ureg.ms

    stage.position = 0*ureg.um
    print('stage position measured: ', stage.position)

    steps = 10
    stepsize = 100.0*ureg.nm
    for n in range(steps):
        stage.position = n*stepsize
        print('stage position measured: ', stage.position)

    print('Measuring step response')

    # For jupyter notebooks
    %matplotlib inline

    stage.servo = True
    stage.position = 0
    import time
    time.sleep(1)

    stepsize = 10*lantz.ureg.um
    timepoints = 100

    timepos = stage.measure_step_response(stepsize, timepoints)

    lines = stage.plot_step_response(timepos)

    stage.finalize()  # nicely close stage and turn of servo
    
    
    """

    DEFAULTS = {'COMMON': {'write_termination': '\n',
                           'read_termination': '\n',
                           'baud_rate': 57600,
                           'timeout': 20}, }

    def __init__(self, *args, **kwargs):
        self.sleeptime_after_move = kwargs.pop('sleeptime_after_move', 0*ureg.ms)
        self.axis = kwargs.pop('axis', 'X')
        super().__init__(*args, **kwargs)

    def initialize(self):
        super().initialize()

    def finalize(self):
        """ Disconnects stage """
        self.stop()
        super().finalize()

    def query_multiple(self, query):
        """Read a multi line response"""
        self.write(query)
        loop = True
        ans = []
        while loop:
            ret = self.read()
            if ret != '':
                ans.append(ret)
            else:
                return ans

    def parse_multiaxis(self, message, axis=None):
        "Parse a multi-axis message, return only value for self.axis"
        if axis is None:
            axis = self.axis
        message_parts = message.split(' ')
        try:
            message_axis = [part for part in message_parts if part[0] == axis][0]
        except IndexError:
            self.log_error('Axis {} not found in returned message: {}'.format(axis, message))
        values = message_axis.split('=')
        return values[-1]

    @Feat()
    def errors(self):
        error = int(self.query('ERR?'))
        if error != 0:
            self.log_error('Stage error code {}: {}'.format(error, error_codes[error]))
        return error

    @Feat()
    def idn(self):
        idn = self.query("*IDN?")
        self.errors
        return idn

    @Action()
    def stop(self):
        '''Stop all motions'''
        self.servo = False
        self.write('STP')
        self.errors

    @Feat(values={True: '1', False: '0'}, read_once=True)
    def servo(self):
        ''' Set the stage control in open- or closed-loop (state = False or True)'''
        return self.parse_multiaxis(self.query('SVO?'))

    @servo.setter
    def servo(self, state):
        self.write('SVO {} {}'.format(self.axis, state) )
        return self.errors

    @Feat(units='um/s')
    def velocity(self):
        ''' Set the stage velocity (closed-loop only)'''
        return self.parse_multiaxis(self.query('VEL?'))

    @velocity.setter
    def velocity(self, velocity):
        self.write('VEL {} {}'.format(self.axis, velocity))
        return self.errors

    @Feat(units='um')
    def position(self):
        ''' Move to an absolute position the stage (closed-loop only)'''
        return self.parse_multiaxis(self.query('POS?'))

    @position.setter
    def position(self, position):
        return self.move_to(position, self.sleeptime_after_move)

    @Action(units=('um','ms'))
    def move_to(self, position, timeout=None):
        ''' Move to an absolute position the stage (closed-loop only)'''
        self.write('MOV {} {}'.format(self.axis, position))
        time.sleep(timeout * 1e-3) # Give the stage time to move! (in seconds!)
        return self.errors

    @Feat(units='um')
    def read_stage_position(self, nr_avg = 1):
        ''' Read the current position from the stage'''
        positions = [self.position.magnitude for n in range(nr_avg)]
        return np.mean(positions)

    @Action(units=('um',None))
    def measure_step_response(self, stepsize, points):
        '''Python implementation to measure a step response of size  stepsize.
        Measure number of points as fast as possible.

        Servo should be on

        Note: a higher temporal resolution can be aquired by the data-recorder
        in the driver

        Example:
        stage.servo = True
        stage.position = 0
        time.sleep(1)

        stepsize = 10*lantz.ureg.um
        timepoints = 100

        timepos = stage.measure_step_response(stepsize, timepoints)

        lines = stage.plot_step_response(timepos)
        '''
        if not self.servo:
            self.log.error('Servo should be on')
            return
        import time
        self.move_to(self.position + stepsize*ureg.um, 0)
        timepos = np.array([[time.time(), self.position.magnitude] for i in range(points)])
        timepos[:,0] -= timepos[0,0] #correct time offset
        timepos[:,0] *= 1000 # make it milliseconds

        return timepos

    def plot_step_response(self, timepos):
        '''Helper function to visualize a step respons'''
        import matplotlib.pyplot as plt
        lines = plt.plot(*timepos.T)
        plt.xlabel('Time [ms]')
        plt.ylabel('Position [um]')
        return lines

if __name__=='__main__':
    # before operating, ensure that the notch filters are set to the right 
    # frequencies. These frequencies depend on the load on the piezo, and can 
    # be determined in NanoCapture.
    from lantz.ui.app import start_test_app

    import lantz
    import visa
    import lantz.drivers.pi.piezo as pi
    rm = visa.ResourceManager('@py')
    lantz.messagebased._resource_manager = rm
    try:
        lantzlog
    except NameError:
        lantzlog = lantz.log.log_to_screen(level=lantz.log.INFO)
    with Piezo('ASRL/dev/ttyUSB0::INSTR') as inst:
        start_test_app(inst)

