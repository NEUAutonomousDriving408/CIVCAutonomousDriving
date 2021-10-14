"""
Simulation Platform Library
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

platform is an HTTP library, written in Python.
usage:

    >>> import ADCPlatform
    >>> ADCPlatform.start('20190812', '123456')
    >>> print ADCPlatform.get_control_data()
    >>> ADCPlatform.stop()


:copyright: (c) 2019 by Junyu Mei.
:license: CATARC Tianjin.
"""


from . import __version__
from .api import start, stop, get_image, get_control_data, get_data, get_sensors, start_task,\
    control,brake
from .type_node import DataType, ImageType, SignBoard
#from .tools import convert_image_to_numpy_ndarray, ThreadWithExc


"""A client to operation ADCPlatform function
 Some operation like controller vehicle, get Image and Data from vehicle sensor.
 """


def __init__(self, proxy=None, __cookie=None):
    self.proxy = proxy
    self.__cookie = __cookie





