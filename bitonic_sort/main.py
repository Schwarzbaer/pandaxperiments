# TODO
#
# * SSBOs can have multiple arrays.
# * Give RNG list of attributes to fill, and distributions to do it.
# * Let dev choose between the current explicit dispatches, and
#   in-scenegraph ones.
# * Make workgroup size settable.
# * Bitonic sort: Make it work on other sizes than power-of-2s.
# * Add spatial hash grids.
# * Add particle visualization.

import random
import time
from array import array

from panda3d.core import ShaderBuffer
from panda3d.core import GeomEnums

from direct.showbase.ShowBase import ShowBase

from random_number_generator import PermutedCongruentialGenerator
from bitonic_sort import BitonicSort
from ssbo_card import SSBOCard


class Struct:
    types_array2glsl = dict(
        f="float",
    )
    
    def __init__(self, type_name, **fields):
        self.type_name = type_name
        self.fields = fields
        self.array_string = ''.join(self.fields.values())

    def convert_to_bytes(self, data):
        return array(self.array_string, data).tobytes()

    def get_byte_size(self):
        return array(self.array_string).itemsize

    def glsl(self):
        source = f"struct {self.type_name} {{\n"
        for field_name, field_type in self.fields.items():
            glsl_type = self.types_array2glsl[field_type]
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
            'DataBuffer',
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


ShowBase()
base.cam.set_pos(0.5, -2.0, 0.5)
base.accept('escape', base.task_mgr.stop)


num_elements = 2**16
data_struct = Struct(
    'Data',
    red='f',
)
fnord_struct = Struct(
    'Fnord',
    red='f',
)
ssbo = SSBO(
    'DataBuffer',
    ('data', data_struct, num_elements),
    ('fnord', fnord_struct, 10000),
)
rng = PermutedCongruentialGenerator(ssbo, ('data', 'red'))
sorter = BitonicSort(ssbo, ('data', 'red'))
rng.fill()
sorter.sort()
#data = base.win.gsg.get_engine().extract_shader_buffer_data(
#    ssbo.get_buffer(),
#    base.win.gsg,
#)

card = SSBOCard(base.render, ssbo, ('data', 'red'))
base.run()
