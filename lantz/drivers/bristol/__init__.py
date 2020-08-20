from lantz.drivers import Wavemeter

class Bristol6XX(Wavemeter):
    pass

from .bristol621 import Bristol621
from .bristol671 import Bristol671

__all__ = ['Bristol621', 'Bristol671', 'Bristol6XX']
