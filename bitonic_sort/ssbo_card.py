from panda3d.core import CardMaker
from panda3d.core import Shader


vertex_source = """#version 430
uniform mat4 p3d_ModelViewProjectionMatrix;

in vec4 vertex;
in vec2 texcoord;
out vec2 v_texcoord;

void main() {
  gl_Position = p3d_ModelViewProjectionMatrix * vertex;
  v_texcoord = texcoord;
}
"""

fragment_source = """#version 430
uniform sampler2D p3d_Texture0;

in vec2 v_texcoord;

out vec4 p3d_FragColor;

struct Data {
  float red;
};

layout(std430) buffer DataBuffer {
  Data data[];
};

void main() {
  int idx = int(floor(v_texcoord.x * float(data.length())));
  p3d_FragColor = vec4(data[idx].red, 0, 0, 1);
}
"""


class SSBOCard:
    def __init__(self, parent, ssbo):
        cm = CardMaker('card')
        card = parent.attach_new_node(cm.generate())
        vis_shader = Shader.make(
            Shader.SL_GLSL,
            vertex = vertex_source,
            fragment = fragment_source,
        )
        card.set_shader(vis_shader)
        card.set_shader_input("DataBuffer", ssbo.get_buffer())
