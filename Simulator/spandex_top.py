from llc import *
from global_utility import *

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

## Build phase
# In build phase, instantiate each all simulation component which
# will be non transient during simulation

# Last level cache
llc = LLC_Controller(LLC_SIZE, WAYS_ASSOC, LINE_SIZE, MEMORY_SPACE, LLC_REQ_BOX_SIZE, MIN_NET_DELAY, MAX_NET_DELAY, MEM_DELAY)
# CPU node
cpu0 = cpu(CPU_CACHE_SIZE, WAYS_ASSOC, LINE_SIZE, MEMORY_SPACE, CPU_CACHE_SIZE)
cpu1 = cpu(CPU_CACHE_SIZE, WAYS_ASSOC, LINE_SIZE, MEMORY_SPACE, CPU_CACHE_SIZE)
cpu2 = cpu(CPU_CACHE_SIZE, WAYS_ASSOC, LINE_SIZE, MEMORY_SPACE, CPU_CACHE_SIZE)
cpu3 = cpu(CPU_CACHE_SIZE, WAYS_ASSOC, LINE_SIZE, MEMORY_SPACE, CPU_CACHE_SIZE)
gpu = gpu(GPU_CACHE_SIZE, WAYS_ASSOC, LINE_SIZE, MEMORY_SPACE, GPU_CACHE_SIZE)

# Global clock counter
clk_cnt = 0

# Message counter
msg_cnt = 0

## Send message to llc
def sendToLLC(msg):
    print("Not implemented")

## Send message to cpu
def sendToCPU(node, msg):
    print("Not implemented")

## Send message to gpu
def sendToGPU(node, msg):
    print("Not implemented")


## Connect phase
def delivery_message(msg_queue):
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
while True:
    cpu0.CPU_run()
    delivery_message(cpu0.)
    cpu1.CPU_run()
    cpu2.CPU_run()
    cpu3.CPU_run()
    gpu.GPU_run()
    llc.LLC_run()
    clk_cnt = clk_cnt + 1
    

## Report phase