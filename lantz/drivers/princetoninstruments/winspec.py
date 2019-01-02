# -*- coding: utf-8 -*-
"""
    lantz.drivers.princetoninstruments.winspec
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Implementation of Winspec PI Camera over a Socket
    Author: Berk Diler
    Date: 29/08/2017
"""

from collections import OrderedDict
from lantz import Action, Feat, DictFeat, Q_
from lantz.messagebased import MessageBasedDriver
import json
import numpy as np



class Winspec(MessageBasedDriver):

    DEFAULTS = {
        'COMMON': {
            'write_termination': '',
            'read_termination': '\r\n',
        }
    }

    GRATINGS = OrderedDict([
        (1,1),
        (2,2)
    ])

    CALIBRATION_PARAMS = OrderedDict([
        (1, {
            "d": 1./600.,
            "gamma": 0.479941,
            "fl": 304.223,
            "delta": -0.00882795,
            "dpixel": 2.33503,
            "dl1": -0.0446331,
            "dl2": -0.0000352349
        }),
        (2, {
            "d": 1. / 150.,
            "gamma": -0.0101195,
            "fl": 320.391,
            "delta": 0.00946824,
            "dpixel": 2.6969,
            "dl1": -0.0308197,
            "dl2": 0.0000550113
        }),
        ("constants", {
            "pwidth" : 25.e-3,
            "center_pixel": 512.5,
            "m": 1
        })
    ])

    @Feat(units="s")
    def exposure_time(self):
        return float(self.query("get exposure time"))

    @exposure_time.setter
    def exposure_time(self, exp_time):
        if self.query("set exposure time {:1.3e}".format(exp_time)) != "OK":
            raise Exception

    @Feat(units="nm")
    def wavelength(self):
        return float(self.query("get wavelength"))

    @wavelength.setter
    def wavelength(self, wl):
        if self.query("set wavelength {:1.3e}".format(wl)) != "OK":
            raise Exception
        
    @Feat(values=GRATINGS)
    def grating(self):
        return int(self.query("get grating"))

    @grating.setter
    def grating(self, wl):
        if self.query("set grating {:1.3e}".format(wl)) != "OK":
            raise Exception
    
    @Feat(units="kelvin", limits=(174,248))
    def target_temperature(self):
        temp_c = float(self.query("get target temperature"))
        result = Q_(temp_c, "degC").to("kelvin").magnitude
        return result

    @target_temperature.setter
    def target_temperature(self, t):
        t = Q_(t, "kelvin").to("degC").magnitude
        if self.query("set target temperature {:1.3e}".format(t)) != "OK":
            raise Exception

    @Feat(units="kelvin")
    def temperature(self):
        temp_c = float(self.query("get temperature"))
        result = Q_(temp_c, "degC").to("kelvin").magnitude
        return result

    @DictFeat(read_once=True, keys=GRATINGS)
    def grating_grooves(self, grating):
        return self.query("get grating grooves {}".format(grating))

    @Action()
    def get_exposure(self):
        return np.array(json.loads(self.query("get spectrum")))

    @Action()
    def get_int_wavelength(self):
        return np.array(json.loads(self.query("get wavelengths")))

    @Action()
    def get_cal_wavelength(self):
        grating = self.grating
        center_wl = self.wavelength.magnitude
        d = self.CALIBRATION_PARAMS[grating]["d"]
        gamma = self.CALIBRATION_PARAMS[grating]["gamma"]
        fl = self.CALIBRATION_PARAMS[grating]["fl"]
        delta = self.CALIBRATION_PARAMS[grating]["delta"]
        dpixel = self.CALIBRATION_PARAMS[grating]["dpixel"]
        dl1 = self.CALIBRATION_PARAMS[grating]["dl1"]
        dl2 = self.CALIBRATION_PARAMS[grating]["dl2"]
        pwidth = self.CALIBRATION_PARAMS["constants"]["pwidth"]
        center_pixel = self.CALIBRATION_PARAMS["constants"]["center_pixel"]
        m = self.CALIBRATION_PARAMS["constants"]["m"]

        x_array = np.array(range(1024)) + 1
        x_array = x_array - center_pixel + dpixel + dl1 * (center_wl - 1000.0) + dl2 * (center_wl - 1000.0) * (
        center_wl - 1000.0)
        xi = np.arctan(x_array * pwidth * np.cos(delta) / (fl + x_array * pwidth * np.sin(delta)))
        psi = np.arcsin(m * center_wl * 1.0e-6 / (2.0 * d * np.cos(gamma / 2.0)))
        wl = (d / m) * (np.sin(psi - gamma / 2.0) + np.sin(psi + gamma / 2.0 + xi)) * 1.0e6
        return wl
