# TODO
#
# * Give RNG list of attributes to fill, and distributions to do it.
# * Let dev choose between the current explicit dispatches, and
#   in-scenegraph ones.
# * Make workgroup size settable.
# * Bitonic sort: Make it work on other sizes than power-of-2s.
# * Add spatial hash grids.
# * Add particle visualization.
# * SSBO.extract_data()


from direct.showbase.ShowBase import ShowBase

from ssbo import Struct
from ssbo import SSBO
from random_number_generator import PermutedCongruentialGenerator
from bitonic_sort import BitonicSort
from ssbo_card import SSBOCard


ShowBase()
base.cam.set_pos(0.5, -2.0, 0.5)
base.accept('escape', base.task_mgr.stop)


num_elements = 2**16
data_struct = Struct('Particle', value='f')
ssbo = SSBO('ParticlePool', ('particle', data_struct, num_elements))
rng = PermutedCongruentialGenerator(ssbo, ('particle', 'value'))
sorter = BitonicSort(ssbo, ('particle', 'value'))
rng.fill()
sorter.sort()
card = SSBOCard(base.render, ssbo, ('d', 'value'))
#data = base.win.gsg.get_engine().extract_shader_buffer_data(
#    ssbo.get_buffer(),
#    base.win.gsg,
#)

base.run()
