from lantz.driver import Driver
from lantz import Feat

import urllib.request

class VariableAttenuator(Driver):
    """
    This class is a driver for the Minicircuits RCDAT series of programmable
    attenuators. Note that at the time of this writing (9/9/2017), this was
    only written to control a single output, although perhaps multi-channel
    attenuators may be supported in the future.

    The attenuation range can be changed to accomodate different filter models,
    or to accomodate different max powers into your amplifier.
    """

    att_range = (0.0, 60.0)

    def __init__(self, address, port=80, timeout=2.0):
        super().__init__(address, port)

        self.address = address
        self.port = port
        self.timeout = timeout

    @Feat()
    def model_number(self):
        """
        Returns the attenuator model number.
        """
        return self.query('MN?')[3:]

    @Feat()
    def serial_number(self):
        """
        Returns the attenuator serial number.
        """
        return int(self.query('SN?')[3:])

    @Feat(limits=att_range)
    def attenuation(self):
        """
        Returns the current attentuation setting (in dB).
        """
        return float(self.query('ATT?'))


    @attenuation.setter
    def attenuation(self, dB):
        """
        Sets the current attenuation to be dB.
        """
        print('Attenuation: {}dB'.format(dB))
        return self.query('SetAtt:{0:.2f}'.format(dB))


    def query(self, message):
        """
        Params:
            message = command to be sent to variable attenuator.
        """
        return str(urllib.request.urlopen('http://{}/:{}'.format(self.address, message)).read(), 'utf-8')

def test_driver():

    ip_addr = '192.168.1.104'
    port = 80

    att = VariableAttentuator(ip_addr, port)

    print('Model Number: {}'.format(att.model_number))
    print('Serial Number: {}'.format(att.serial_number))

    print('Attenuation: {}dB'.format(att.attenuation))
    att.attenuation = 30.0
    print('Attenuation: {}dB'.format(att.attenuation))
    att.attenuation = 10.0
    print('Attenuation: {}dB'.format(att.attenuation))

if __name__ == "__main__":
    test_driver()
