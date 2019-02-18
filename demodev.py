from toon.input.device import BaseDevice, make_obs
from timeit import default_timer
import ctypes
import numpy as np


class SingleResp(BaseDevice):
    t0 = default_timer()
    sampling_frequency = 1000
    counter = 0

    Num1 = make_obs('Num1', (15,), ctypes.c_double)

    def read(self):
        while default_timer() - self.t0 < (1.0/self.sampling_frequency):
            pass
        val = self.counter
        self.counter += 1
        self.t0 = default_timer()
        t = self.clock()
        return self.Num1(t, np.random.random(self.Num1.shape))
