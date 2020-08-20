import sys
from time import *

# we use the tinyrpc package to connect to the JSON-RPC server
if sys.version_info.major > 2:
    try:
        from tinyrpc import RPCClient
    except Exception as e:
        print(str(e))
        print (
"""
Failed to import JSON-RPC library. Ensure that you have it installed by typing
> pip install tinyrpc
in your terminal.
""")
        sys.exit(1)
else:
    try:
        from tinyrpc import RPCClient
        from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
        from tinyrpc.transports.http import HttpPostClientTransport        
    except Exception as e:
        print(str(e))
        print (
"""
Failed to import JSON-RPC library. Ensure that you have it installed by typing
> pip install tinyrpc
> pip install gevent-websocket
in your terminal.
""")
        sys.exit(1)    

# binary and base64 conversion
import struct
import base64
import six
import numpy as np
from enum import Enum

class Serial(Enum):
    ID = 0
    MAC = 1

class Clock_source(Enum):
    INTERNAL = 0
    EXT_125MHZ = 1
    EXT_10MHZ = 2

class Start(Enum):
    IMMEDIATE = 0
    SOFTWARE = 1
    HARDWARE_RISING = 2
    HARDWARE_FALLING = 3
    HARDWARE_RISING_AND_FALLING = 4

class Mode(Enum):
    NORMAL = 0
    SINGLE = 1

class PulseStreamer():
    """
    Simple python wrapper for a PulseStreamer 8/2
    that describes pulses in the form (time, ['ch0', 'ch3'], 0.8, -0.4),
    where time is an integer in ns (clock ticks),
    ['ch0','ch3'] is a list naming the channels that should be high
    the last two numbers specify the analog outputs in volt.
    """
    
    def __init__(self, ip_hostname='pulsestreamer'):
        print("Connect to Pulse Streamer via JSON-RPC.")
        print("IP / Hostname:", ip_hostname)
        url = 'http://'+ip_hostname+':8050/json-rpc'
        try:
            self.INFINITE = -1
            self.CONSTANT_ZERO = (0,0,0,0)

            if sys.version_info.major > 2:
                client = RPCClient(url)
            else:
                client = RPCClient(JSONRPCProtocol(), HttpPostClientTransport(url))

            self.proxy = client.get_proxy()
            try:
                self.proxy.getSerial()
            except:
                try:
                    self.proxy.isRunning()
                    print ("Pulse Streamer class not compatible with current firmware. Please update your firmware.")
                    sys.exit(1)
                except:
                    print("No Pulse Streamer found at IP/Host-address: "+ip_hostname)
                    sys.exit(1)
        except:
            print("No Pulse Streamer found at IP/Host-address: "+ip_hostname)
            sys.exit(1)

    def reset(self):
        return self.proxy.reset()
        
    def constant(self, pulse):
        if (pulse == 'CONSTANT_ZERO' or pulse == 'constant_zero'):
            pulse = self.CONSTANT_ZERO
        else:
            if isinstance(pulse[1], list):
                pulse = self.convert_pulse(pulse)
            else:
                pulse=pulse
        self.proxy.constant(pulse)

    def forceFinal(self):
        return self.proxy.forceFinal()
        
    def stream(self, seq, n_runs='INFINITE', final='CONSTANT_ZERO'):
        if (n_runs == 'INFINITE' or n_runs == 'infinite'):
            n_runs = self.INFINITE
        if (final == 'CONSTANT_ZERO' or final == 'constant_zero'):
            final = self.CONSTANT_ZERO
        else:
            if isinstance(final[1], list):
                final = self.convert_pulse(final)
            else:
                final=final

        if six.PY2:
            s = self.enc(seq)
        else:
            s = self.enc(seq).decode("utf-8")
        
        self.proxy.stream(s, n_runs, final)

    def isStreaming(self):
        return self.proxy.isStreaming()

    def hasFinished(self):
        return self.proxy.hasFinished()

    def hasSequence(self):
        return self.proxy.hasSequence()

    def startNow(self):
        return self.proxy.startNow()

    def getUnderflow(self):
        return self.proxy.getUnderflow()

    def getDebugRegister(self):
        return self.proxy.getDebugRegister()

    def selectClock(self, clock_source):
        if not isinstance(clock_source, Clock_source):
            raise TypeError("clock_source must be an instance of Clock_source Enum")
        else:
            return self.proxy.selectClock(clock_source.name)

    def getFirmwareVersion(self):
        return self.proxy.getFirmwareVersion()

    def getSerial(self, serial=Serial.MAC):
        if not isinstance(serial, Serial):
            raise TypeError("serial must be an instance of Serial Enum")
        else:
            return self.proxy.getSerial(serial.name)
    
    def setTrigger(self, start, mode=Mode.NORMAL):
        if not isinstance(start, Start):
            raise TypeError("start must be an instance of Start Enum")
        else:
            if not isinstance(mode, Mode):
                raise TypeError("mode must be an instance of Mode Enum")
            else:
                return self.proxy.setTrigger(start.name, mode.name)

    def setNetworkConf(self, ip, netmask, gateway):
        return self.proxy.setNetworkConf(ip, netmask, gateway)

    def getNetworkConf(self):
        return self.proxy.getNetworkConf()

    def testNetworkConf(self):
        return self.proxy.testNetworkConf()
        
    def enableStaticIP(self, permanent=False):
        assert permanent in [True, False]
        return self.proxy.enableStaticIP(permanent)

    def rearm(self):
        return self.proxy.rearm()
        
    def enc(self, seq):
        """
        Convert a human readable python sequence to a base64 encoded string
        """
        s = b''
        convert_list = []
        if type(seq[0][1])== list:
            for pulse in seq:
                convert_list.extend(self.convert_pulse(pulse))    
        else:
            for pulse in seq:
                convert_list.extend(pulse)

        fmt = '>' + len(convert_list)//4*'IBhh'
        s=struct.pack(fmt, *convert_list)  
        return base64.b64encode(s)
    
    def convert_pulse(self, pulse):
        t, chans, a0, a1 = pulse
        return (t, self.chans_to_mask(chans), int(round(0x7fff*a0)), int(round(0x7fff*a1)))

    def chans_to_mask(self, chans):
        mask = 0
        for chan in chans:
            mask |= 1<<chan
        return mask
        
"""---------Test-Code-------------------------------"""

if __name__ == '__main__':
    pulser = PulseStreamer(ip_hostname='pulsestreamer')

    print("Serial number:", pulser.getSerial())
    print("Firmware Version:", pulser.getFirmwareVersion())
