from math import floor
from random import random

from panda3d.core import PStatClient
from panda3d.core import Vec3

from direct.showbase.ShowBase import ShowBase

from ssbo import Struct
from ssbo import SSBO
from random_number_generator import PermutedCongruentialGenerator
from bitonic_sort import BitonicSort
from ssbo_card import SSBOCard


ShowBase()
base.cam.set_pos(0.5, -2.0, 0.5)
base.accept('escape', base.task_mgr.stop)
PStatClient.connect()


# The data
num_elements = 2**8
lines = 7.0
initial_data = [floor((i / (num_elements - 1)) * lines) / lines for i in range(num_elements)]
struct = Struct(
    'Data',
    value=float,
)
ssbo = SSBO('DataBuffer', ('data', struct, num_elements), initial_data=initial_data)


# Visualization
card = SSBOCard(base.render, ssbo, ('data', 'value'))


# The compute shaders
rng = PermutedCongruentialGenerator(
    ssbo,
    ('data', 'value'),
    debug=True,
)
sorter = BitonicSort(ssbo, ('data', 'value'))


#rng.dispatch()
sorter.dispatch()


# Data extraction
#data = base.win.gsg.get_engine().extract_shader_buffer_data(
#    ssbo.get_buffer(),
#    base.win.gsg,
#)


base.run()
