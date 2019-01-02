# -*- coding: utf-8 -*-
"""
	lantz.drivers.arduino.goniometer
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~

	Lantz interface to the arduino controlling the goniometer

	Authors: Alexandre Bourassa
	Date: 3/28/2017

"""

from lantz import Action, Feat, DictFeat, Q_
from lantz.errors import InstrumentError, LantzTimeoutError
from lantz.messagebased import MessageBasedDriver

from pyvisa.constants import Parity, StopBits

import time

class Goniometer(MessageBasedDriver):

	comm_delay = 1

	DEFAULTS = {
		'ASRL': {
			'write_termination': '\n',
			'read_termination': '\r\n',
			'baud_rate': 9600,
			'timeout': 1600,
		}
	}

	errors = {
		 -1:  'theta or phi were out of bounds',
		 -2:  'alpha or beta were out of bounds',
		 -3:  'attempted rotateTo while run_state != 0',
		 -4:  'period is out of bound',
		 -9:  'R is out of bounds',
		-10:  'Unknown cmd',
		-11:  'other error',
		-50:  'no error',
	}


	def initialize(self):
		super().initialize()
		time.sleep(1.6)
		self.query('stop')

	def check_error(self, err):
		if err != -50:
			raise InstrumentError(self.errors[err])
		else:
			return

	def query(self, cmd):
		self.write(cmd)
		ans = self.read()
		err = int(self.read())
		self.check_error(err)
		# time.sleep(self.comm_delay)
		return ans

	@Feat(limits=(70, 110, 0.01))
	def theta(self):
		return float(self.query('theta?'))

	@theta.setter
	def theta(self, val):
		return self.query('theta {}'.format(val))

	@Feat(limits=(25, 135, 0.01))
	def phi(self):
		return float(self.query('phi?'))

	@phi.setter
	def phi(self, val):
		return self.query('phi {}'.format(val))

	@Feat(units='mm', limits=(0., 250.))
	def R(self):
		return float(self.query('raxis?'))

	@R.setter
	def R(self, val):
		return self.query('rabs {}'.format(val))

	@Feat(values={'ready':'0', 'moving':'1'})
	def state(self):
		return self.query('state?')

	@Action()
	def stop(self):
		return self.query('stop')

	@Feat(units='us', limits=(0,1000,1))
	def period_alpha(self):
		return float(self.query('period? 0'))

	@period_alpha.setter
	def period_alpha(self, val):
		return self.query('pperiod 0 {}'.format(int(val)))

	@Feat(units='us', limits=(0,1000,1))
	def period_beta(self):
		return float(self.query('period? 1'))

	@period_beta.setter
	def period_beta(self, val):
		return self.query('pperiod 1 {}'.format(int(val)))

	@Feat(units='us', limits=(0,1000,1))
	def period_R(self):
		return float(self.query('period? 2'))

	@period_R.setter
	def period_R(self, val):
		return self.query('pperiod 2 {}'.format(int(val)))

	@Action()
	def wait_for_ready(self, max_iter=30):
		for i in range(max_iter):
			if self.state == 'ready':
				return
			time.sleep(self.comm_delay)
		raise LantzTimeoutError('Could not get a ready state response...')

	@Action()
	def unsafe_R_relative_move(self, distance):
		if type(distance) == Q_:
			distance = distance.to('mm').m
		if abs(distance)>= 25:
			raise ValueError("Cannot do relative move of more then 25 mm")
		return self.query('rrel {}'.format(distance))

	# @Action()
	# def return_to_origin(self):
	# 	self.phi = 90
	# 	self.theta = 90

	@Action()
	def zero(self, axis):
		if not axis in [0,1,2]:
			raise ValueError('Axis must be 0, 1 or 2')
		else:
			return self.query('zero {}'.format(axis))

	@Feat(values={'on':'0', 'off':'1'})
	def emergency_switch(self):
		return self.query('switch?')

	@Action()
	def lock(self, state):
		if state:
			return self.query('lock')
		else:
			return self.query('unlock')
