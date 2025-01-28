from math import log2

from panda3d.core import NodePath
from panda3d.core import Shader
from panda3d.core import ShaderAttrib


# FIXME
# * Abstract out `red` to key field.
# * Make workgroup size settable.


sorter_source = """#version 430
layout (local_size_x = 32, local_size_y = 1) in;

struct Data {
  float red;
};

layout(std430) buffer DataBuffer {
  Data data[];
};

uniform int span;
uniform int reverseSpan;

void compare(int low, int high) {
  Data dataLow = data[low];
  Data dataHigh = data[high];
  if (dataLow.red > dataHigh.red) {
    data[low] = dataHigh;
    data[high] = dataLow;
  }
}

void main() {
  // From where to shere is this span?
  int idx = int(gl_GlobalInvocationID.x);
  int idxOfSpan = int(floor(idx / span));
  int spanBoundLow = idxOfSpan * span * 2;
  int spanBoundHigh = (idxOfSpan + 1) * span * 2 - 1;

  // In what direction does this span go, and where is its start *really*?
  int reversed = int(round(mod(idxOfSpan / reverseSpan, 2))) * (-2) + 1;  // +1 = straight, -1 = reversed
  int spanStart = abs(min(spanBoundLow * reversed, spanBoundHigh * reversed));

  // Which pair of elements do we compare?
  int idxInSpan = int(round(mod(idx, span)));
  int idxLow = spanStart + idxInSpan * reversed;
  int idxHigh = idxLow + span * reversed;

  // Compare, and switch if necessary.
  compare(idxLow, idxHigh);
}
"""


class BitonicSort:
    def __init__(self, ssbo, key):
        num_elements = ssbo.get_num_elements()
        sort_shader = Shader.make_compute(Shader.SL_GLSL, sorter_source)
        np = NodePath("dummy")
        np.set_shader(sort_shader)
        np.set_shader_input("DataBuffer", ssbo.get_buffer())
        workgroups = (num_elements // 32, 1, 1)
        sorter_arrays = []
        for e in range(int(log2(num_elements))):
            for s in range(e, -1, -1):
                sorter_arrays.append((2**s, 2**(e-s)))
        self.np = np
        self.workgroups = workgroups
        self.sorter_arrays = sorter_arrays

    def sort(self):
        for span, reverse_span in self.sorter_arrays:
            np = self.np
            np.set_shader_input('span', span)
            np.set_shader_input('reverseSpan', reverse_span)
            sattr = np.get_attrib(ShaderAttrib)
            base.graphicsEngine.dispatch_compute(
                self.workgroups,
                sattr,
                base.win.get_gsg(),
            )
