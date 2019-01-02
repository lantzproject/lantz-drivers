from lantz.driver import Driver
from lantz import Feat, Action
import cv2
import numpy as np

class USBCam(Driver):

    def __init__(self, device_id):
        self.device_id = device_id
        self._flipud = False
        self._fliplr = False
        self._rotation = 0
        return

    def initialize(self):
        self.capture = cv2.VideoCapture(self.device_id)
        return

    def finalize(self):
        self.capture.release()
        return

    @Feat(values={0, 90, 180, 270})
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        self._rotation = value
        return

    @Feat(values={True, False})
    def flipud(self):
        return self._flipud

    @flipud.setter
    def flipud(self, value):
        self._flipud = value
        return

    @Feat(values={True, False})
    def fliplr(self):
        return self._fliplr

    @fliplr.setter
    def fliplr(self, value):
        self._fliplr = value
        return

    @Action()
    def get_frame(self):
        img = self.capture.read()[1]
        array = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if self._flipud:
            array = np.flipud(array)
        if self._fliplr:
            array = np.fliplr(array)
        array = np.rot90(array, k=int(self._rotation / 90))
        return array
