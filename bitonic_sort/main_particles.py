# TODO
#
# * Refactor Struct and SSBO to account for the fullness of std430.
# * SSBO.extract_data()
# * Give RNG distributions.
# * Changing inputs at runtime, e.g. seed for RNG.
# * Make workgroup size settable.
# * Bitonic sort: Make it work on other sizes than power-of-2s.
# * Add spatial hash grids.
# * ShaderWrapper.detach()
# * Evaluate only every nth frame

from panda3d.core import PStatClient
from panda3d.core import Vec3

from direct.showbase.ShowBase import ShowBase

from ssbo import Struct
from ssbo import SSBO
from random_number_generator import PermutedCongruentialGenerator
from bitonic_sort import BitonicSort
from shim import Shim
from ssbo_card import SSBOCard
from ssbo_particles import SSBOParticles


ShowBase()
#base.cam.set_pos(0.5, -2.0, 0.5)
base.accept('escape', base.task_mgr.stop)
PStatClient.connect()


# The data
num_elements = 2**14
struct = Struct(
    'Particle',
    position=Vec3,
    direction=Vec3,
    #hash=int,
)
ssbo = SSBO('ParticlePool', ('particles', struct, num_elements))


# Visualization
points = SSBOParticles(base.render, ssbo, ('particles', 'position'))


# The compute shaders
from panda3d.core import CullBinManager
compute_bin = CullBinManager.get_global_ptr().add_bin("preliminary_compute_pass", CullBinManager.BT_fixed, 0)
rng = PermutedCongruentialGenerator(
    ssbo,
    ('particles', 'position'),
    #('particles', 'direction'),
)
particle_setupper = Shim(
    ssbo,
    "",
    "particles[gl_GlobalInvocationID.x].direction = normalize(particles[gl_GlobalInvocationID.x].position - 0.5);",
    (num_elements // 32, 1, 1),
)
mover_header = "uniform float dt;"
mover_body = """
  Particle p = particles[gl_GlobalInvocationID.x];
  vec3 newPos = p.position + p.direction * 1.0/60.0/10.0;//dt;
  float distFromCenter = length(newPos - 0.5);
  float newLength = fract(distFromCenter);
  newPos = normalize(newPos - 0.5) * newLength + 0.5;
  particles[gl_GlobalInvocationID.x].position = newPos;
"""
particle_mover = Shim(
    ssbo,
    mover_header,
    mover_body,
    (num_elements // 32, 1, 1),
    debug=True,
)
#sorter = BitonicSort(ssbo, ('line', 'value'))


rng.dispatch()
particle_setupper.dispatch()


np = points.get_np()
particle_mover.attach(np, bin_sort=0)
# hash_particle_positions.attach(np, bin_sort=0)
# sort_particle_hashes.attach(np, bin_sort=1)
# boid_particles.attach(np, bin_sort=2)

# Data extraction
#data = base.win.gsg.get_engine().extract_shader_buffer_data(
#    ssbo.get_buffer(),
#    base.win.gsg,
#)


def update_shader_inputs(task):
    particle_mover.update(dt=globalClock.dt)
    return task.cont
base.task_mgr.add(update_shader_inputs, sort=-10)


camera_gimbal = base.render.attach_new_node("")
camera_gimbal.set_pos(0.5, 0.5, 0.5)
base.cam.reparent_to(camera_gimbal)
base.cam.set_y(-2.5)
def rotate_camera(task):
    camera_gimbal.set_h(camera_gimbal.get_h() + globalClock.dt * 10.0)
    return task.cont
base.task_mgr.add(rotate_camera)
base.run()
