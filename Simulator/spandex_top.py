from llc import *

## Global parameter definition, remain unchange during simulation
CPU_CNT = 1
GPU_CNT = 1
MEMORY_SPACE = 65536    # Number of words in whole memory, word addressable
LINE_SIZE = 4           # Number of words in a line
WAYS_ASSOC = 4          # Cache way associativity, same for all cache
CPU_CACHE_SIZE = 4096   # Number of words in each CPU cache
GPU_CACHE_SIZE = 4096   # Number of words in each GPU cache
LLC_SIZE = 16384        # Number of words in LLC

## Build phase
# In build phase, instantiate each all simulation component which
# will be non transient during simulation



## Connect phase

## Run phase

## Report phase