from collections import deque
from global_utility import *
from llc import *
from gpu import *
from llc_cpu_translation import *
from msg_classify import *
from msi_coherence import *
from System import *

llc_cache_size = 256
cpu_cache_size = 256
gpu_cache_size = 256
ways = 2
line_size = 16
memory_size = 1024

llc_req_box_size = 10 # max pending request LLC can take
llc_min_delay = 1
llc_max_delay = 3
llc_mem_delay = 10

gpu_trace = "gpu.txt"


def main():
    
    # instantiate the object
    LLC     = LLC_Controller(llc_cache_size, ways, line_size, memory_size, llc_req_box_size, llc_min_delay, llc_max_delay, llc_mem_delay)
    GPU     = GPU_Controller(gpu_cache_size, ways, line_size, memory_size, gpu_trace)
    CPU0    = CacheController(cpu_cache_size, Node.CPU0) # to fix: add line size and way
    CPU1    = CacheController(cpu_cache_size, Node.CPU1) # to fix: add line size and way
    CPU2    = CacheController(cpu_cache_size, Node.CPU2) # to fix: add line size and way
    CPU3    = CacheController(cpu_cache_size, Node.CPU2) # to fix: add line size and way
    TPU     = Translation(LLC)
    # add devices to Map
    Device_Map = Map()
    Device_Map.insert(Node.LLC, LLC)
    Device_Map.insert(Node.GPU, GPU)
    Device_Map.insert(Node.CPU0, CPU0)
    Device_Map.insert(Node.CPU1, CPU1)
    Device_Map.insert(Node.CPU2, CPU2)
    Device_Map.insert(Node.CPU3, CPU3)
    
    Device_List = [Node.LLC, Node.GPU, Node.CPU0, Node.CPU1, Node.CPU2, Node.CPU3]
    Core_List   = [Node.GPU, Node.CPU0, Node.CPU1, Node.CPU2, Node.CPU3]
    CPU_List    = [Node.CPU0, Node.CPU1, Node.CPU2, Node.CPU3]
    GPU_List    = [Node.GPU]
    
    system = System(Device_Map, Device_List, Core_List, CPU_List, GPU_List, TPU)

    system.SYSTEM_RUN()
    
    return 0

if __name__ == '__main__':
    main()