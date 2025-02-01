from jinja2 import Template

from panda3d.core import NodePath
from panda3d.core import Shader
from panda3d.core import ShaderAttrib


pcg_rng_template = """#version 430
#extension GL_ARB_gpu_shader_int64 : require

layout (local_size_x = 32, local_size_y = 1) in;

{{struct}}

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
    def __init__(self, ssbo, key):
        render_args = dict(
            struct=ssbo.struct.glsl(),
            ssbo=ssbo.glsl(),
            type_name=ssbo.struct.type_name,
            array_name=ssbo.array_name,
            key=key,
        )
        template = Template(pcg_rng_template)
        source = template.render(**render_args)
        shader = Shader.make_compute(Shader.SL_GLSL, source)
        np = NodePath("dummy")
        np.set_shader(shader)
        np.set_shader_input(ssbo.buffer_name, ssbo.get_buffer())
        workgroups = (ssbo.get_num_elements() // 32, 1, 1)
        self.np = np
        self.workgroups = workgroups

    def fill(self):
        sattr = self.np.get_attrib(ShaderAttrib)
        base.graphicsEngine.dispatch_compute(
            self.workgroups,
            sattr,
            base.win.get_gsg(),
        )
