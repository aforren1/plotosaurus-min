import sys
import struct
import numpy as np
import hid
from toon.input.base_input import BaseInput
from ctypes import c_double


class Hand(BaseInput):
    """Hand Articulation Neuro-Training Device (HAND)."""

    @staticmethod
    def samp_freq(**kwargs):
        return kwargs.get('sampling_frequency', 1000)

    @staticmethod
    def data_shapes(**kwargs):
        return [[15]]

    @staticmethod
    def data_types(**kwargs):
        return [c_double]

    def __init__(self, nonblocking=False, **kwargs):
        super(Hand, self).__init__(**kwargs)
        self._rot = np.pi / 4.0
        self._sinrot = np.sin(self._rot)
        self._cosrot = np.cos(self._rot)
        self.nonblocking = nonblocking
        self._device = None
        self._data_buffer = np.full(15, np.nan)

    def __enter__(self):
        self._device = hid.device()
        dev_path = ''
        for d in hid.enumerate():
            if d['product_id'] == 1158 and d['usage'] == 512:
                dev_path = d['path']
        if sys.version_info >= (3, 0):
            dev_path = bytes(dev_path, 'utf-8')
        self._device.open_path(dev_path)
        self._device.set_nonblocking(self.nonblocking)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._device.close()

    def read(self):
        data = self._device.read(46)
        time = self.clock()
        if data:
            data = struct.unpack('>LhHHHHHHHHHHHHHHHHHHHH', bytearray(data))
            data = np.array(data, dtype='d')
            data[0] /= 1000.0
            data[2:] /= 65535.0
            self._data_buffer[0::3] = data[2::4] * self._cosrot - data[3::4] * self._sinrot  # x
            self._data_buffer[1::3] = data[2::4] * self._sinrot + data[3::4] * self._cosrot  # y
            self._data_buffer[2::3] = data[4::4] + data[5::4]  # z
            return time, self._data_buffer