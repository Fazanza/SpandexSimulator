from collections import deque
from utility.global_utility import *
from core.llc import *
from core.gpu import *
from core.cpu import *
from core.llc_cpu_translation import *
from core.msg_classify import *
from core.System import *


def main_test1():
    llc_cache_size = 512
    cpu_cache_size = 512
    gpu_cache_size = 512
    ways = 2
    line_size = 16
    memory_size = 8192

    llc_req_box_size = 10  # max pending request LLC can take
    llc_min_delay = 1
    llc_max_delay = 2
    llc_mem_delay = 3
    #
    # gpu_trace = "../gpu_t2.txt"
    # cpu0_trace = "../cpu0_t2.txt"
    # cpu1_trace = "../cpu1_t2.txt"
    # cpu2_trace = "../cpu2_t2.txt"
    # cpu3_trace = "../cpu3_t2.txt"

    gpu0_trace = "../Testcase/1c1g/gpu0.txt"
    cpu0_trace = "../Testcase/1c1g/cpu0.txt"
    cpu1_trace = "../Testcase/1c1g/cpu1.txt"

    # instantiate the object
    LLC = LLC_Controller(llc_cache_size, ways, line_size, memory_size, llc_req_box_size, llc_min_delay, llc_max_delay, llc_mem_delay)
    GPU0 = GPU_Controller(gpu_cache_size, ways, line_size, memory_size, gpu0_trace, Node.GPU0)
    CPU0 = CPU_Controller(cpu_cache_size, ways, line_size, memory_size, cpu0_trace, Node.CPU0)  # to fix: add line size and way

    TPU = Translation(LLC)
    # add devices to Map
    Device_Map = Map()
    Device_Map.insert(Node.LLC, LLC)
    Device_Map.insert(Node.GPU0, GPU0)
    Device_Map.insert(Node.CPU0, CPU0)

    Device_List = [Node.LLC, Node.GPU0, Node.CPU0]
    Core_List = [Node.GPU0, Node.CPU0]
    CPU_List = [Node.CPU0]
    GPU_List = [Node.GPU0]

    system = System(Device_Map, Device_List, Core_List, CPU_List, GPU_List, TPU, 5000)

    system.SYSTEM_RUN()

    return 0

def main_test2():
    llc_cache_size = 512
    cpu_cache_size = 512
    gpu_cache_size = 512
    ways = 2
    line_size = 16
    memory_size = 8192

    llc_req_box_size = 10  # max pending request LLC can take
    llc_min_delay = 1
    llc_max_delay = 2
    llc_mem_delay = 3
    #
    # gpu_trace = "../gpu_t2.txt"
    # cpu0_trace = "../cpu0_t2.txt"
    # cpu1_trace = "../cpu1_t2.txt"
    # cpu2_trace = "../cpu2_t2.txt"
    # cpu3_trace = "../cpu3_t2.txt"

    gpu0_trace = "../Testcase/1c4g/gpu0.txt"
    gpu1_trace = "../Testcase/1c4g/gpu1.txt"
    gpu2_trace = "../Testcase/1c4g/gpu2.txt"
    gpu3_trace = "../Testcase/1c4g/gpu3.txt"
    cpu0_trace = "../Testcase/1c4g/cpu0.txt"

    # instantiate the object
    LLC = LLC_Controller(llc_cache_size, ways, line_size, memory_size, llc_req_box_size, llc_min_delay, llc_max_delay, llc_mem_delay)
    GPU0 = GPU_Controller(gpu_cache_size, ways, line_size, memory_size, gpu0_trace, Node.GPU0)
    GPU1 = GPU_Controller(gpu_cache_size, ways, line_size, memory_size, gpu1_trace, Node.GPU1)
    GPU2 = GPU_Controller(gpu_cache_size, ways, line_size, memory_size, gpu2_trace, Node.GPU2)
    GPU3 = GPU_Controller(gpu_cache_size, ways, line_size, memory_size, gpu3_trace, Node.GPU3)
    CPU0 = CPU_Controller(cpu_cache_size, ways, line_size, memory_size, cpu0_trace, Node.CPU0)  # to fix: add line size and way

    TPU = Translation(LLC)
    # add devices to Map
    Device_Map = Map()
    Device_Map.insert(Node.LLC, LLC)
    Device_Map.insert(Node.GPU0, GPU0)
    Device_Map.insert(Node.GPU1, GPU1)
    Device_Map.insert(Node.GPU2, GPU2)
    Device_Map.insert(Node.GPU3, GPU3)
    Device_Map.insert(Node.CPU0, CPU0)

    Device_List = [Node.LLC, Node.GPU0, Node.GPU1, Node.GPU2, Node.GPU3, Node.CPU0]
    Core_List = [Node.GPU0, Node.GPU1, Node.GPU2, Node.GPU3, Node.CPU0]
    CPU_List = [Node.CPU0]
    GPU_List = [Node.GPU0, Node.GPU1, Node.GPU2, Node.GPU3]

    system = System(Device_Map, Device_List, Core_List, CPU_List, GPU_List, TPU, 5000)

    system.SYSTEM_RUN()

    return 0

def main_test5():

    llc_cache_size = 512
    cpu_cache_size = 512
    gpu_cache_size = 512
    ways = 2
    line_size = 16
    memory_size = 8192

    llc_req_box_size = 10  # max pending request LLC can take
    llc_min_delay = 1
    llc_max_delay = 2
    llc_mem_delay = 3
    #
    # gpu_trace = "../gpu_t2.txt"
    # cpu0_trace = "../cpu0_t2.txt"
    # cpu1_trace = "../cpu1_t2.txt"
    # cpu2_trace = "../cpu2_t2.txt"
    # cpu3_trace = "../cpu3_t2.txt"

    gpu0_trace = "../Testcase/2c1g_5/gpu0.txt"
    cpu0_trace = "../Testcase/2c1g_5/cpu0.txt"
    cpu1_trace = "../Testcase/2c1g_5/cpu1.txt"
    
    # instantiate the object
    LLC     = LLC_Controller(llc_cache_size, ways, line_size, memory_size, llc_req_box_size, llc_min_delay, llc_max_delay, llc_mem_delay)
    GPU0     = GPU_Controller(gpu_cache_size, ways, line_size, memory_size, gpu0_trace, Node.GPU0)
    CPU0    = CPU_Controller(cpu_cache_size, ways, line_size, memory_size, cpu0_trace, Node.CPU0) # to fix: add line size and way
    CPU1    = CPU_Controller(cpu_cache_size, ways, line_size, memory_size, cpu1_trace, Node.CPU1) # to fix: add line size and way


    TPU     = Translation(LLC)
    # add devices to Map
    Device_Map = Map()
    Device_Map.insert(Node.LLC, LLC)
    Device_Map.insert(Node.GPU0, GPU0)
    Device_Map.insert(Node.CPU0, CPU0)
    Device_Map.insert(Node.CPU1, CPU1)

    
    Device_List = [Node.LLC, Node.GPU0, Node.CPU0, Node.CPU1]
    Core_List   = [Node.GPU0, Node.CPU0, Node.CPU1]
    CPU_List    = [Node.CPU0, Node.CPU1]
    GPU_List    = [Node.GPU0]

    
    system = System(Device_Map, Device_List, Core_List, CPU_List, GPU_List, TPU, 5000)

    system.SYSTEM_RUN()
    
    return 0

def main_test6():
    
    llc_cache_size = 512
    cpu_cache_size = 512
    gpu_cache_size = 512
    ways = 2
    line_size = 16
    memory_size = 8192

    llc_req_box_size = 10  # max pending request LLC can take
    llc_min_delay = 1
    llc_max_delay = 2
    llc_mem_delay = 3
    #
    # gpu_trace = "../gpu_t2.txt"
    # cpu0_trace = "../cpu0_t2.txt"
    # cpu1_trace = "../cpu1_t2.txt"
    # cpu2_trace = "../cpu2_t2.txt"
    # cpu3_trace = "../cpu3_t2.txt"

    gpu0_trace = "../Testcase/2c1g_6/gpu0.txt"
    cpu0_trace = "../Testcase/2c1g_6/cpu0.txt"
    cpu1_trace = "../Testcase/2c1g_6/cpu1.txt"
    
    # instantiate the object
    LLC     = LLC_Controller(llc_cache_size, ways, line_size, memory_size, llc_req_box_size, llc_min_delay, llc_max_delay, llc_mem_delay)
    GPU0     = GPU_Controller(gpu_cache_size, ways, line_size, memory_size, gpu0_trace, Node.GPU0)
    CPU0    = CPU_Controller(cpu_cache_size, ways, line_size, memory_size, cpu0_trace, Node.CPU0) # to fix: add line size and way
    CPU1    = CPU_Controller(cpu_cache_size, ways, line_size, memory_size, cpu1_trace, Node.CPU1) # to fix: add line size and way


    TPU     = Translation(LLC)
    # add devices to Map
    Device_Map = Map()
    Device_Map.insert(Node.LLC, LLC)
    Device_Map.insert(Node.GPU0, GPU0)
    Device_Map.insert(Node.CPU0, CPU0)
    Device_Map.insert(Node.CPU1, CPU1)

    
    Device_List = [Node.LLC, Node.GPU0, Node.CPU0, Node.CPU1]
    Core_List   = [Node.GPU0, Node.CPU0, Node.CPU1]
    CPU_List    = [Node.CPU0, Node.CPU1]
    GPU_List    = [Node.GPU0]

    
    system = System(Device_Map, Device_List, Core_List, CPU_List, GPU_List, TPU, 5000)

    system.SYSTEM_RUN()
    
    return 0

if __name__ == '__main__':
    main_test2()