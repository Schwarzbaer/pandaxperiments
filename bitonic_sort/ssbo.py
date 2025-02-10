from array import array

from panda3d.core import Vec3
from panda3d.core import ShaderBuffer
from panda3d.core import GeomEnums


class Struct:
    types_py2glsl = {
        float: 'float',
        Vec3: 'vec3',
    }
    types_py2array = {
        float: 'f',
        Vec3: 'ffff',
    }
    
    def __init__(self, type_name, **fields):
        self.type_name = type_name
        self.fields = fields
        self.array_string = ''.join([self.types_py2array[t] for t in fields.values()])

    def convert_to_bytes(self, data):
        return array(self.array_string, data).tobytes()

    def get_byte_size(self):
        return sum([array(c).itemsize for c in self.array_string])

    def glsl(self):
        source = f"struct {self.type_name} {{\n"
        for field_name, field_type in self.fields.items():
            glsl_type = self.types_py2glsl[field_type]
            source += f"  {glsl_type} {field_name};\n"
        source += "};\n"
        return source
            

class SSBO:
    def __init__(self, buffer_name, *array_defs, initial_data=None):
        # Store array definition for later lookup
        self.arrays = {
            array_name: struct
            for array_name, struct, _ in array_defs
        }
        self.num_elements = {
            array_name: num_elements
            for array_name, _, num_elements in array_defs
        }
        # Calculate buffer size / encode initial data
        if initial_data is None:
            size = 0
            for _, struct, num_elements in array_defs:
                size += struct.get_byte_size() * num_elements
            size_or_data = size
        else:
            data = b''
            for _, struct, num_elements in array_defs:
                head = initial_data[:num_elements]
                data += struct.convert_to_bytes(head)
                initial_data = initial_data[num_elements:]
            size_or_data = data
        # Create buffer and store additional data
        self.ssbo = ShaderBuffer(
            buffer_name,
            size_or_data,
            GeomEnums.UH_static,
        )
        self.buffer_name = buffer_name
        self.array_defs = array_defs

    def get_buffer(self):
        return self.ssbo

    def get_num_elements(self, array_name):
        return self.num_elements[array_name]

    def glsl(self):
        source = ""
        for struct in self.arrays.values():
            source += struct.glsl() + "\n"
        source += f"layout(std430) buffer {self.buffer_name} {{\n"
        for array_name, struct, num_elements in self.array_defs:
            
            source += f"  {struct.type_name} {array_name}[{num_elements}];\n"
        source += "};"
        return source

    def __getitem__(self, array_name):
        return self.arrays[array_name]
