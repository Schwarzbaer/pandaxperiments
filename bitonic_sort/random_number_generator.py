from panda3d.core import NodePath
from panda3d.core import Shader
from panda3d.core import ShaderAttrib


pcg_rng_source = """#version 430
#extension GL_ARB_gpu_shader_int64 : require

layout (local_size_x = 128, local_size_y = 1) in;

struct Data {
  float red;
};

layout(std430) buffer DataBuffer {
  Data data[];
};

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
  // data[idx].red = float(pcg32()) / float(0xFFFFFFFFFFFFFFFFul);
  data[idx].red = float(pcg32()) / float((2<<62) - 1) / 2;

}
"""


class PermutedCongruentialGenerator:
    def __init__(self, ssbo):
        pcg_shader = Shader.make_compute(Shader.SL_GLSL, pcg_rng_source)
        np = NodePath("dummy")
        np.set_shader(pcg_shader)
        np.set_shader_input("DataBuffer", ssbo.get_buffer())
        workgroups = (ssbo.get_num_elements() // 128, 1, 1)
        self.np = np
        self.workgroups = workgroups

    def fill(self):
        sattr = self.np.get_attrib(ShaderAttrib)
        base.graphicsEngine.dispatch_compute(
            self.workgroups,
            sattr,
            base.win.get_gsg(),
        )
