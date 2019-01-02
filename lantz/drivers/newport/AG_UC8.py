# -*- coding: utf-8 -*-
"""
    AG-UC8.py

    :brief Implements the drivers for the agilis controller

    :author AlexBourassa
"""

from lantz import Feat, DictFeat, Action
from lantz.errors import InstrumentError
from lantz.messagebased import MessageBasedDriver
import re

import pyvisa.resources.serial as _s

speed_dict = {'stop':0, 'lowest':1, 'low':2, 'high':3, 'highest':4}
inv_speed_dict = {v: k for k, v in speed_dict.items()}

jog_modes = {'no move': '0','1700 step/s' : '3', '666 step/s' : '4',  '100 step/s' : '2',  '5 step/s': '1',
                            '-1700 step/s': '-3','-666 step/s': '-4', '-100 step/s': '-2', '-5 step/s': '-1'}

class AG_UC8(MessageBasedDriver):
    """
    Implements the drivers for the agilis controller
    """
    
    DEFAULTS = {'ASRL': {'write_termination': '\r\n',
                         'read_termination': '\r\n',
                         'baud_rate': 921600,
                         'data_bits' : 8,
                         'stop_bits' : _s.constants.StopBits.one,
                         'timeout' : 20,
                         'parity' : _s.constants.Parity.none}}

    speed_list = [[0,0]]*4 # Instance variable that defines the speeds which will be used for all the move calls

    def __init__(self, resource_name, name='AG-UC8',**kwargs):
        MessageBasedDriver.__init__(self, resource_name=resource_name, name=name, **kwargs)

    def query(self, cmd, send_args=(None, None), recv_args=(None, None), filter=r'.*'):
        """Sends a query using the base class method, then parses the response according to the regex filter and
           returns group 1 (or group zero if no group in the filter)
        """
        ans = MessageBasedDriver.query(self, command=cmd,send_args=send_args, recv_args=recv_args)
        match = re.search(filter, ans)
        if match is None            : raise Exception("Filter '" +filter+"' didn't match ans '" + ans +"'")
        elif len(match.groups())==0 : return match.group(0)
        else                        : return match.group(1)



    @DictFeat(keys = [1,2,3,4], values=speed_dict)
    def speed1(self, channel):
        """Speed of axis 1 for a given channel
        """
        return self.speed_list[channel-1][0]

    @speed1.setter
    def speed1(self, channel, speed):
        self.speed_list[channel][0] = speed

    @DictFeat(keys = [1,2,3,4], values=speed_dict)
    def speed2(self, channel):
        """Speed of axis 2 for a given channel
        """
        return self.speed_list[channel-1][1]

    @speed2.setter
    def speed2(self, channel, speed):
        self.speed_list[channel][1] = speed

    @Feat()
    def limit_status(self):
        """Tell limit status
        """
        return self.query('PH?')

    @Action()
    def jog(self, axis=1, reverse=False):
        """Move the current channel specified axis at the specified speed
        """
        speed = self.speed_list[int(self.channel)-1][axis-1]
        if reverse and speed!=0: cmd = '{}JA-{}'
        else      : cmd = '{}JA{}'
        print(self.query(cmd.format(axis,speed)))

    @Feat(values = {str(i):str(i) for i in [1,2,3,4]})
    def channel(self):
        return self.query('CC?', filter='CC([1,4])')



    @channel.setter
    def channel(self, channel):
        self.write('CC'+str(channel))



    def get_error_status(self,read_only=False):
        """Get error of previous command
             0  No error
            -1  Unknown command
            -2  Axis out of range (must be 1 or 2, or must not be specified)
            -3  Wrong format for parameter nn (or must not be specified)
            -4  Parameter nn out of range
            -5  Not allowed in local mode
            -6  Not allowed in current state
        """
        if read_only: return self.read()
        else        : return self.query('TE?')



    @Action()
    def stop_all(self):
        """Throw all the stop command in the book!
            Hopefully one of them works...
        """
        for i in [1,2]: self.move_to_limit[i] = 'no move'
        for i in [1,2]: self.jog = 'stop'
        # for stop_cmd in ['1MV0','2MV0','1JA0','2JA0']:
        #     self.write(stop_cmd)


    def check_connect(self):
        pass