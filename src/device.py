from enum import Enum
from cache import Cache
from cache_controller import CacheController

class DeviceType(Enum):

    CPU = 1
    GPU = 2
    ACCELERATOR = 3

class CacheConfig:
    def __init__(self, size, ways, line_size, memory_size):
        self.size = size
        self.ways = ways
        self.line_size = line_size
        self.memory_size = memory_size


class Device:
    ## coherence type defined based on device type (since it is device granularity in Spandex)

    ## instantiate cache hierachy here  
    def __init__(self, type: DeviceType):
        self.type = type

    def perform_operation(self):
        raise NotImplementedError("This method should be overridden by subclasses.")

class CPU(Device):
    ## instantiate cache hierachy here  
    cpu_cache_config = CacheConfig(size=1024, ways=4, line_size=16, memory_size=65536)
    cpu_cache = Cache(cpu_cache_config.size, cpu_cache_config.ways, cpu_cache_config.line_size, cpu_cache_config.memory_size)
    cpu_cache_ctrl = CacheController(cpu_cache)

    # parse memory trace

    def perform_operation(self):
        return "Performing CPU-specific operation."

class GPU(Device):

    gpu_cache_config = CacheConfig(size=2048, ways=8, line_size=32, memory_size=65536)
    gpu_cache = Cache(gpu_cache_config.size, gpu_cache_config.ways, gpu_cache_config.line_size, gpu_cache_config.memory_size)

    def perform_operation(self):
        return "Performing GPU-specific operation."

class Accelerator(Device):
    
    accelerator_cache_config = CacheConfig(size=512, ways=2, line_size=8, memory_size=65536)
    accelerator_cache = Cache(accelerator_cache_config.size, accelerator_cache_config.ways, accelerator_cache_config.line_size, accelerator_cache_config.memory_size)


    def perform_operation(self):
        return "Performing Accelerator-specific operation."
    