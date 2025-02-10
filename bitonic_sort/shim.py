from jinja2 import Template

from panda3d.core import Vec3
from panda3d.core import BoundingVolume
from panda3d.core import NodePath
from panda3d.core import ComputeNode
from panda3d.core import Shader
from panda3d.core import ShaderAttrib


shim_template = """#version 430

layout (local_size_x = 32, local_size_y = 1) in;

{{ssbo}}

{{header}}

void main() {
{{shim}}
}
"""


class Shim:
    def __init__(self, ssbo, header, shim, workgroups, debug=False):
        render_args = dict(
            ssbo=ssbo.glsl(),
            header=header,
            shim=shim,
        )
        template = Template(shim_template)
        source = template.render(**render_args)
        if debug:
            for line_nr, line_txt in enumerate(source.split('\n')):
                print(f"{line_nr:4d}  {line_txt}")
        shader = Shader.make_compute(Shader.SL_GLSL, source)
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

    def attach(self, np, bin_sort=0, **inputs):
        cn = ComputeNode(f"PermutedCongruentialGenerator")
        cn.add_dispatch(self.workgroups)
        cnnp = np.attach_new_node(cn)
        cnnp.set_shader(self.shader)
        cnnp.set_shader_input(self.ssbo.buffer_name, self.ssbo.get_buffer())
        cnnp.set_bin("preliminary_compute_pass", bin_sort, 0)
        cn.set_bounds_type(BoundingVolume.BT_box)
        cn.set_bounds(np.get_bounds())
        self.np = cnnp
        self.update(**inputs)

    def update(self, **inputs):
        for name, value in inputs.items():
            self.np.set_shader_input(name, value)
