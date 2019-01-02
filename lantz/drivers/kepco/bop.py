# -*- coding: utf-8 -*-
"""
    lantz.drivers.kepco.bop
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of Kepco BOP power supply
    Author: Kevin Miao
    Date: 1/18/2016
"""

from lantz import Action, Feat
from lantz.messagebased import MessageBasedDriver

class BOP(MessageBasedDriver):

    @Feat()
    def idn(self):
        return self.query('*IDN?')

    @Action(values={'curr', 'volt'})
    def mode(self, value):
        """
        sets operation mode
        curr - constant current mode
        volt - constant voltage mode
        """
        return self.write('FUNC:MODE {}'.format(value))

    @Feat(units='A')
    def current(self):
        return self.query('MEAS:CURR?')

    @current.setter
    def current(self, value):
        self.write('CURR {:1.1f}'.format(value))

    @Feat(units='V')
    def voltage(self):
        return self.query('MEAS:VOLT?')

    @voltage.setter
    def voltage(self, value):
        self.write('VOLT {:1.1f}'.format(value))
