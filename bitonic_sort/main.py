# TODO
# * Modularity
#   * Abstract out `red`
#   * Give RNG list of attributes to fill, and distributions to do it.
# * Let dev choose between the current explicit dispatches, and
#   in-scenegraph ones.
# * Make workgroup size settable.
# * Bitonic sort: Make it work on other sizes than power-of-2s.



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
        source += "};"
        return source
            

class SSBO:
    def __init__(self, buffer_name, struct, array_name, num_elements, initial_data=None):
        if initial_data is None:
            size_or_data = struct.get_byte_size() * num_elements
        else:
            size_or_data = struct.convert_to_bytes(initial_data)
        self.ssbo = ShaderBuffer(
            'DataBuffer',
            size_or_data,
            GeomEnums.UH_static,
        )
        self.buffer_name = buffer_name
        self.struct = struct
        self.array_name = array_name
        self.num_elements = num_elements

    def get_buffer(self):
        return self.ssbo

    def get_num_elements(self):
        return self.num_elements

    def glsl(self):
        array_name = 'data'
        source = f"layout(std430) buffer {self.buffer_name} {{\n"
        source += f"  {self.struct.type_name} {self.array_name}[];\n"
        source += "};"
        return source


ShowBase()
base.cam.set_pos(0.5, -2.0, 0.5)
base.accept('escape', base.task_mgr.stop)


num_elements = 2**16
struct = Struct('Data', red='f')
#initial_data = [random.random() for i in range(num_elements)]
ssbo = SSBO('DataBuffer', struct, 'data', num_elements)
card = SSBOCard(base.render, ssbo)
rng = PermutedCongruentialGenerator(ssbo, 'red')
sorter = BitonicSort(ssbo, 'red')
total_time = 0
rng.fill()
#tic = time.perf_counter()
#for i in range(100):
sorter.sort()
data = base.win.gsg.get_engine().extract_shader_buffer_data(
    ssbo.get_buffer(),
    base.win.gsg,
)
#toc = time.perf_counter()
#total_time = toc-tic
#print(total_time/100)
#data_2 = array('f', data).tolist()
# print(data_2)
base.run()
