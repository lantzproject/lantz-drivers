# -*- coding: utf-8 -*-
from lantz.messagebased import MessageBasedDriver
from lantz import Feat
import time
#from lantz.drivers.coherent.fieldmastergs import FieldMasterGS

class PilotBox(MessageBasedDriver):

    DEFAULTS = {
        'COMMON': {
            'read_termination': '\r\n',
            'write_termination': '\r',
        },
    }

    # def initialize(self):
    #     print("turning off this goddamn echo shit...")
    #     self.write('system:echo off')


    @Feat(read_once=True)
    def idn(self):
        return self.query('*idn?')

    @Feat(read_once=True)
    def echo(self):
        return self.query('system:echo off')

    @Feat(read_once=True)
    def min(self):
        print(self.query(':Laser:ILIMit? MIN'))
        return float(self.query(':Laser:ILIMit? MIN'))


    @Feat(read_once=True)
    def max(self):
        return float(self.query(':Laser:ILIMit? MAX'))


    @Feat(read_once=True, values={'Current': 'I', 'Power': 'P'})
    def laser_mode(self):
        mode = self.query(':Laser:MODe?')
        return mode[0]
    @laser_mode.setter
    def laser_mode(self, mode):
        self.write(':Laser:MODe {}'.format(mode))


    @Feat(read_once=True)
    def current_meas(self):
        return self.query(':Laser:CURRent?')


    @Feat(read_once=True)
    def current_set(self):
        return self.query(':Laser:CURRent:Set?')
    @current_set.setter
    def current_set(self, current):
        self.write(':Laser:CURRent {}A'.format(current))


    @Feat(read_once=True)
    def laser_status(self):
        return self.query(':Laser:STATus?')
    @laser_status.setter
    def laser_status(self, status):
        self.write(':Laser:STATus {}'.format(status))

    @Feat(read_once=True)
    def piezo_mod(self):
        return self.query(':Piezo:FREQuency:GENerator ?')

    @Feat(read_once=True)
    def piezo_amp(self):
        return self.query(':Piezo:FREQuency:ampl ?')

    @Feat(read_once=True, values={False:'OFF', True:'ON'})
    def piezo_status(self):
        return self.query(':Piezo:ENAble ?')

    @Feat(read_once=True)
    def piezo_offset(self):
        return self.query(':Piezo:OFFset ?')

    @Feat(read_once=True)
    def piezo_freq(self):
        return self.query(':Piezo:FREQuency ?')

    @piezo_freq.setter
    def piezo_freq(self,freq):
        self.write(':Piezo:FREQuency {}'.format(freq))

    @piezo_offset.setter
    def piezo_offset(self,offset):
        self.write(':Piezo:OFFset {}V'.format(offset))

    @piezo_status.setter
    def piezo_status(self,status,values={False:'OFF', True:'ON'}):
        self.write(':Piezo:ENAble: {}')


    @piezo_amp.setter
    def piezo_amp(self,ampl):
        self.write(':Piezo:FREQuency:ampl {}V'.format(ampl))

    @piezo_mod.setter
    def piezo_mod(self,mod):
        self.write(':Piezo:FREQuency:GENerator {}'.format(mod))
        #off, sin, tri

    @Feat(read_once=True)
    def current_lim(self):
        return self.query(':Laser:ILIMit? MAX')

    @current_lim.setter
    def current_lim(self,currentlim):
        self.write(':Laser:ILIMit {}A'.format(currentlim))




import time
if __name__ == '__main__':
    s = PilotBox('COM9')
    with s as pbox:
        #pbox.initialize()
        print(pbox.idn)
        print(pbox.echo)
        print(pbox.min)
        print(pbox.max)
        #print(pbox.laser_mode)
        #pbox.laser_mode = 'Current'
        #print(pbox.laser_mode)
        #print(pbox.current_meas)
        #print(pbox.current_set)
        #print(pbox.current_meas)
        #print(pbox.laser_status)
        #pbox.laser_status = 'ON'
        #time.sleep(5)
        #print(pbox.laser_status)
        #print(pbox.current_meas)
        #pbox.laser_status = 'OFF'
        #time.sleep(1)
        print(pbox.laser_status)
        print(pbox.current_set)
        print(pbox.current_meas)



"""
For some reason the actual measured laser current is always zero
Maybe the detector is broken or something
"""



#
