from lantz.drivers.ni.daqmx.utils import DigitalSwitch

class Fabry_Perot(DigitalSwitch):
    @Action()
    def passive_mode(self):
        self.output(False)

    @Action()
    def active_mode(self):
        self.output(True)