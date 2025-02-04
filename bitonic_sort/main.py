# TODO
#
# * Let dev choose between the current explicit dispatches, and
#   in-scenegraph ones.
# * Give RNG list of attributes to fill, and distributions to do it.
# * Add particle visualization.
# * Make workgroup size settable.
# * Bitonic sort: Make it work on other sizes than power-of-2s.
# * Add spatial hash grids.
# * SSBO.extract_data()

from panda3d.core import PStatClient

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
num_elements = 2**16
struct = Struct('Color', value='f')
ssbo = SSBO('VerticalLines', ('line', struct, num_elements))


# Visualization
card = SSBOCard(base.render, ssbo, ('line', 'value'))


# The compute shaders
from panda3d.core import CullBinManager
compute_bin = CullBinManager.get_global_ptr().add_bin("preliminary_compute_pass", CullBinManager.BT_fixed, 0)
rng = PermutedCongruentialGenerator(ssbo, ('line', 'value'))
sorter = BitonicSort(ssbo, ('line', 'value'))


#rng.dispatch()
rng.attach(card.get_np(), bin_sort=0)
sorter.attach(card.get_np(), bin_sort=1)


# Data extraction
#data = base.win.gsg.get_engine().extract_shader_buffer_data(
#    ssbo.get_buffer(),
#    base.win.gsg,
#)


base.run()
