from enum import Enum, auto
import random
from collections import deque
from global_utility import *
from llc import *
from gpu import *
from llc_cpu_translation import *
from msg_classify import *
from msi_coherence import *

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

def round_robin(queue):
    temp = queue[0]
    for i in range(1, len(queue)):
        queue[i-1] = queue[i]
    queue[len(queue)-1] = temp
    return queue

def is_member(element, list):
    return element in list

### Every Node do not require any msg, it just send msg to the other Node
### when Every Node run, it just read it's own req and rep queue
def LLC_RUN(LLC_Node, Device_map, TPU, Msg_Classify, GPU_List, CPU_List):
    LLC = Device_map.search(LLC_Node)
    LLC.LLC_run()
    while LLC.get_generated_msg() != None:
        generated_msg = LLC.get_generated_msg()
        msg_class = Msg_Classify.get_value(generated_msg.msg_type)
        #
        if msg_class == msg_class.Request: # send request to other Node
            assert(generated_msg.dst != Node.GPU), "Error! LLC is sending request to GPU"
            Device_map.search(generated_msg.dst).receieve_req_msg(TPU.translate_msg(generated_msg))
            LLC.taken_generated_msg() # pop from LLC generated_msg_queue
        #
        elif msg_class == msg_class.Response: # send response to other Node
            if is_member(generated_msg.dst, GPU_List):
                Device_map.search(generated_msg.dst).receieve_rep_msg(generated_msg)
            elif is_member(generated_msg.dst, CPU_List):
                Device_map.search(generated_msg.dst).receieve_rep_msg(TPU.translate_msg(generated_msg))
            LLC.taken_generated_msg() # pop from LLC generated_msg_queue

def GPU_RUN(GPU_Node, Device_map, Msg_Classify, CPU_List):
    GPU = Device_map.search(GPU_Node)
    GPU.GPU_run()
    # do barrier
    GPU_barrier = GPU.get_barrier()
    if GPU_barrier != None:
        for CPU in CPU_List:
            Device_map.search(CPU).update_barrier(GPU_barrier)
    # do generate msg
    if GPU.get_generated_msg() != None:
        generated_msg = GPU.get_generated_msg()
        msg_class = Msg_Classify.get_value(generated_msg.msg_type)
        assert msg_class == msg_class.request, "Error! GPU is generated Response type of msg"
        assert generated_msg.dst == Node.LLC, "Error! GPU is sending Request to Node other than LLC"
        req_msg_taken = Device_map.search(Node.LLC).receieve_req_msg # check if LLC req_msg_box has enough space to enqueue
        if req_msg_taken == True:
            GPU.taken_generated_msg()
        GPU.GPU_POST_RUN()

def CPU_RUN(CPU_Node, Device_map, TPU, Msg_Classify, GPU_List, CPU_List):
    CPU = Device_map.search(CPU_Node)
    CPU.runCPU()
    # do barrier
    CPU_barrier = CPU.get_barrier()
    if CPU_barrier != None:
        for GPU in GPU_List:
            Device_map.search(GPU).update_barrier(CPU_barrier)
        for CPUs in CPU_List:
            if Device_map.search(CPUs) != CPU:
                Device_map.search(CPUs).update_barrier(CPU_barrier)

    # do generate msg
    while CPU.get_generated_msg() != None:
        generated_msg = CPU.get_generated_msg()
        msg_class = Msg_Classify.get_value(generated_msg.msg_type)
        
        if msg_class == msg_class.Request: # send request to other Node
            assert(generated_msg.dst == Node.LLC), "Error! CPU is sending request to Node other than LLC"
            if Device_map.search(Node.LLC).receieve_req_msg(TPU.translate_msg(generated_msg)) == True:
                CPU.taken_generated_msg() # pop from LLC generated_msg_queue
        #
        elif msg_class == msg_class.Response: # send response to other Node
            if is_member(generated_msg.dst, CPU_List):
                Device_map.search(generated_msg.dst).receieve_rep_msg(generated_msg)
            else:
                Device_map.search(generated_msg.dst).receieve_rep_msg(TPU.translate_msg(generated_msg))
            CPU.taken_generated_msg() # pop from LLC generated_msg_queue

def main():
    
    # instantiate the object
    LLC = LLC_Controller(llc_cache_size, ways, line_size, memory_size, llc_req_box_size, llc_min_delay, llc_max_delay, llc_mem_delay)
    GPU = GPU_Controller(gpu_cache_size, ways, line_size, memory_size, gpu_trace)
    CPU0 = CacheController(cpu_cache_size, Node.CPU0) # to fix: add line size and way
    CPU1 = CacheController(cpu_cache_size, Node.CPU1) # to fix: add line size and way
    CPU2 = CacheController(cpu_cache_size, Node.CPU2) # to fix: add line size and way
    CPU3 = CacheController(cpu_cache_size, Node.CPU2) # to fix: add line size and way
    TPU = Translation(LLC) # used to translate request between CPU and LLC
    MsgClassify = msg_classify()
    
    # add devices to Map
    Device_Map = Map()
    Device_Map.insert(Node.LLC, LLC)
    Device_Map.insert(Node.GPU, GPU)
    Device_Map.insert(Node.CPU0, CPU0)
    Device_Map.insert(Node.CPU1, CPU1)
    Device_Map.insert(Node.CPU2, CPU2)
    Device_Map.insert(Node.CPU3, CPU3)
    
    Device_List = [Node.LLC, Node.GPU, Node.CPU0, Node.CPU1, Node.CPU2, Node.CPU3]
    Core_List = [Node.GPU, Node.CPU0, Node.CPU1, Node.CPU2, Node.CPU3]
    CPU_List = [Node.CPU0, Node.CPU1, Node.CPU2, Node.CPU3]
    GPU_List = [Node.GPU]
    global_clk = 0
    
    # Run 
    while True:
        is_finish = True
        for core in Core_List:
            is_finish = is_finish and Device_Map.search(core).is_finish()
        if is_finish == True:
            print("All Program Finish ! ! !")
            return 0
        
        for i in len(Core_List):
            if is_member(Core_List[i], CPU_List):
                CPU_RUN(Core_List[i], Device_Map, TPU, MsgClassify, GPU_List, CPU_List)
            elif is_member(Core_List[i], GPU_List):
                GPU_RUN(Core_List[i], Device_Map, MsgClassify, CPU_List)
        LLC_RUN(Node.LLC, Device_Map, TPU, MsgClassify, GPU_List, CPU_List)
                
        Core_List = round_robin(Core_List)
        global_clk = global_clk + 1
        
    return 0

if __name__ == '__main__':
    main()