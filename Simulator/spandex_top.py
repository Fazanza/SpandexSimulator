from llc import *
from global_utility import *
from gpu import *

## Global parameter definition, remain unchange during simulation
CPU_CNT = 1
GPU_CNT = 1
MEMORY_SPACE = 65536    # Number of words in whole memory, word addressable
LINE_SIZE = 4           # Number of words in a line
WAYS_ASSOC = 4          # Cache way associativity, same for all cache
CPU_CACHE_SIZE = 4096   # Number of words in each CPU cache
GPU_CACHE_SIZE = 4096   # Number of words in each GPU cache
LLC_SIZE = 16384        # Number of words in LLC
LLC_REQ_BOX_SIZE = 8    # Maximum number of message in llc req box
PROC_REQ_BOX_SIZE = 8   # Maximum number of message in cpu or gpu req box
MIN_NET_DELAY = 2       # Minimum network delay in cycle
MAX_NET_DELAY = 5       # Maximum network delay in cycle
MEM_DELAY = 10          # Main memory accessing delay

# Memory trace for each node
GPU_TRACE = "GPU_trace.txt"

## Build phase
# In build phase, instantiate each all simulation component which
# will be non transient during simulation

# Last level cache
llc = LLC_Controller(LLC_SIZE, WAYS_ASSOC, LINE_SIZE, MEMORY_SPACE, LLC_REQ_BOX_SIZE, MIN_NET_DELAY, MAX_NET_DELAY, MEM_DELAY)
# CPU node
cpu0 = cpu(CPU_CACHE_SIZE, WAYS_ASSOC, LINE_SIZE, MEMORY_SPACE)
cpu1 = cpu(CPU_CACHE_SIZE, WAYS_ASSOC, LINE_SIZE, MEMORY_SPACE)
cpu2 = cpu(CPU_CACHE_SIZE, WAYS_ASSOC, LINE_SIZE, MEMORY_SPACE)
cpu3 = cpu(CPU_CACHE_SIZE, WAYS_ASSOC, LINE_SIZE, MEMORY_SPACE)
gpu = GPU_Controller(GPU_CACHE_SIZE, WAYS_ASSOC, LINE_SIZE, MEMORY_SPACE, GPU_TRACE)

# Global clock counter
clk_cnt = 0

# Message counter
msg_cnt = 0


## Connect phase
# Due to the given situation, has to use stupid hard coded function to handle connection

## Send message to llc
def sendToLLC(msg):
    # Response message
    if(msg.msg_type == msg_type.InvAck | msg.msg_type == msg_type.RepRvkO | msg.msg_type == msg_type.MemRep):
        llc.rep_msg_box.enqueue(msg)
    # Request message
    elif(not llc.req_msg_box.is_full):
        llc.req_msg_box.enqueue(msg)
    # Request box in llc is full
    else:
        return False
        

## Send message to cpu
def sendToCPU(node, msg):
    print("Not implemented")

## Send message to gpu
def sendToGPU(node, msg):
    gpu.receieve_rep_msg(msg.msg_type, msg.addr, msg.src, msg.dst, msg.ack_cnt, msg.fwd_dst)

def delivery_message_queue(msg_queue):
    while(not msg_queue.empty()):
        msg = msg_queue.get()
        if(msg.dst == Node.LLC):
            sendToLLC(msg)
        elif(msg.dst == Node.CPU0):
            sendToCPU(cpu0, msg)
        elif(msg.dst == Node.CPU1):
            sendToCPU(cpu1, msg)
        elif(msg.dst == Node.CPU2):
            sendToCPU(cpu2, msg)
        elif(msg.dst == Node.CPU3):
            sendToCPU(cpu3, msg)
        elif(msg.dst == Node.GPU):
            sendToGPU(gpu, msg)
        else:
            print("ERROR! Invalid destination!")
            quit()
        msg_cnt = msg_cnt + 1

## Run phase

# GPU run function
def GPU_run():
    gpu_message, gpu_barrier = gpu.GPU_run()
    # Delivery message gpu to llc
    if(gpu_message != None):
        if(gpu_message.dst == Node.LLC):
            gpu.GPU_POST_RUN(sendToLLC(gpu_message))
        else:
            print("ERROR! Invalid destination for GPU!")
            quit()
        msg_cnt = msg_cnt + 1
    if(gpu_barrier != None):
        cpu0.receieve_barrier(gpu_barrier)
        cpu1.receieve_barrier(gpu_barrier)
        cpu2.receieve_barrier(gpu_barrier)
        cpu3.receieve_barrier(gpu_barrier)

# CPU run function
def CPU_run(this_cpu):
    cpu_message_queue, cpu_barrier = this_cpu.CPU_run()
    if(cpu_message_queue != None):
        delivery_message_queue(cpu_message_queue)
    if(cpu_barrier != None):
        if(this_cpu != cpu0):
            cpu0.receieve_barrier(cpu_barrier)
        if(this_cpu != cpu1):
            cpu1.receieve_barrier(cpu_barrier)
        if(this_cpu != cpu2):
            cpu2.receieve_barrier(cpu_barrier)
        if(this_cpu != cpu3):
            cpu3.receieve_barrier(cpu_barrier)
        gpu.receive_barrier(cpu_barrier)

# LLC run function
def LLC_run():
    llc_message_queue = llc.LLC_run()
    delivery_message_queue(llc_message_queue)

while True:
    CPU_run(cpu0)
    CPU_run(cpu1)
    CPU_run(cpu2)
    CPU_run(cpu3)
    GPU_run()
    LLC_run()
    clk_cnt = clk_cnt + 1

    # Check finish
    if(gpu.finish & cpu0.finish & cpu1.finish & cpu2.finish & cpu3.finish):
        break
    

## Report phase
print("Simulation done! Total cycle: ", clk_cnt, "; Total message delivered: ", msg_cnt, ";")