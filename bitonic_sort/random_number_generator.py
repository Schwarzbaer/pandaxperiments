from jinja2 import Template

from panda3d.core import BoundingVolume
from panda3d.core import NodePath
from panda3d.core import ComputeNode
from panda3d.core import Shader
from panda3d.core import ShaderAttrib


pcg_rng_template = """#version 430
#extension GL_ARB_gpu_shader_int64 : require

layout (local_size_x = 32, local_size_y = 1) in;

{{ssbo}}

uint64_t state = 0;
const uint64_t multiplier = 6364136223846793005ul;
const uint64_t increment = 1442695040888963407ul;

uint rotr32(uint x, uint r)
{
    return (x >> r) | (x << (32 - r));
}

uint pcg32()
{
    uint64_t x = state;
    uint count = uint(x >> 59);

    state = x * multiplier + increment;
    x ^= x >> 18;
    return rotr32(uint(x >> 27), count);
}

void pcg32_init(uint64_t seed)
{
    state = seed + increment;
    pcg32();
}

void main() {
  int idx = int(gl_GlobalInvocationID.x);
  pcg32_init(uint64_t(idx));
  {{array_name}}[idx].{{key}} = float(pcg32()) / float((2<<62) - 1) / 2;

}
"""


class PermutedCongruentialGenerator:
    def __init__(self, ssbo, array_and_key):
        array_name, key = array_and_key
        render_args = dict(
            ssbo=ssbo.glsl(),
            type_name=ssbo[array_name].type_name,
            array_name=array_name,
            key=key,
        )
        template = Template(pcg_rng_template)
        source = template.render(**render_args)
        shader = Shader.make_compute(Shader.SL_GLSL, source)
        workgroups = (ssbo.get_num_elements(array_name) // 32, 1, 1)
        self.ssbo = ssbo
        self.shader = shader
        self.workgroups = workgroups

    def dispatch(self):
        np = NodePath("dummy")
        np.set_shader(self.shader)
        np.set_shader_input(self.ssbo.buffer_name, self.ssbo.get_buffer())
        sattr = np.get_attrib(ShaderAttrib)
        base.graphicsEngine.dispatch_compute(
            self.workgroups,
            sattr,
            base.win.get_gsg(),
        )

    def attach(self, np, bin_sort=0):
        cn = ComputeNode(f"PermutedCongruentialGenerator")
        cn.add_dispatch(self.workgroups)
        cnnp = np.attach_new_node(cn)
        cnnp.set_shader(self.shader)
        cnnp.set_shader_input(self.ssbo.buffer_name, self.ssbo.get_buffer())
        cnnp.set_bin("preliminary_compute_pass", bin_sort, 0)
        cn.set_bounds_type(BoundingVolume.BT_box)
        cn.set_bounds(np.get_bounds())
