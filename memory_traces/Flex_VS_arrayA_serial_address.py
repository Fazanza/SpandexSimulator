"""
After inspecting the code, I think this should capture the properties that can be exploited by fine-grain coherence specialization. A good way to test this would be to run the traces through some simulated caches and see if different coherence request types result in expected hit rate changes. Some additional points:

1. I assume when you simulate these traces, you'll interleave requests from the parallel cores that are active for each phase - is that right?
2. There is some indirection in the densely accessed patterns which might lead to not-so-dense accesses in practice 
(it looks like you're randomly selecting from an array with 90% of the array partition, which can lead to <90% density). 
This kind of randomness could be realistic for some patterns/architectures, but for simplicity it might be easiest to just access every element in the partition serially.

3.The cpu load with overlapped sharing is probably more complex than it needs to be (I also made it more complex than it needed to be in the microbenchmark in the paper). A simple solution would be to have both cores densely access an entire array densely.

4.A common criticism of microbenchmarks is that they aren't representative of useful applications in the real world. 
Although the microbenchmarks are useful for showing the range of access patterns in a single workload, here are some more recent examples of applications that could exhibit each of the communication patterns discussed:
Array A - dense reads with sharing and reuse, sparse writes: Graph workloads, GNNs, and ML training on categorical inputs (embedding updates) can exhibit this pattern. These workloads sparsely load embeddings (vectors) from an embedding table in a forward pass, and the indices accessed often follow a power law distribution (e.g., when processing natural graphs, 80% of indices are to 20% of embeddings). Because of this reuse, these loads can exhibit high reuse and and sharing, motivating ReqS. When training ML workloads or applying updates in dynamic graph algorithms, such embeddings are often sparsely updated such that some cached embeddings would need to be invalidated from the dense reader, but most could remain in S state in the reader caches.
Array B - dense reads with no reuse, dense writes with reuse: In GNNs and graph workloads, some data structures also exhibit dense access patterns. This is the case for MLPs, which are often interleaved with sparse kernels in GNNs, and sparse representations often require densely reading an edge list or streaming list of input indices that will be used to sparsely index into a graph structure or embedding table. Such densely accessed structures may exhibit reuse for a producer but not for a consumer if, for example, the structure is too large to fit in the producer but not the consumer (e.g., because the producer cache is larger, or because the producer layer is parallelized and the consumer layer is not), or if the producer task is statically distributed (each producer outputs to its own local buffer) while the consumer task is dynamically distributed for load balancing (e.g., using a shared task queue).

"""

import random

## Flex V/S memory traces

output_directory = "output"
array_length_A = 1000
# array_length_B = 1000

# Parameters
cpu_cores = 2
gpu_cores = 5
iteration_no = gpu_cores
# more_actions = 500
dense_stride = 1
sparse_stride = 10

## CPU cores, dense read array A, share and reuse

last_cpu_start = 500
per_cpu_range = array_length_A - last_cpu_start
increment = int(last_cpu_start/cpu_cores)

partition_index_pattern = {}

mem_type = "ld"

for iter in range(iteration_no):
    for cpu_id in range(cpu_cores):
        mode = "w" if (iter == 0) else "a"
        density_cnt = 0
        with open(f"cpu_core_{cpu_id}_read_A_dense_overlap.txt", mode) as fh:
            # index_start = cpu_id*increment
            # index_end = index_start + increment
            index_start = 0
            index_end = array_length_A-1
            current_index = index_start
            while (current_index) < int(array_length_A*0.9): # Dense or sparse access
                address = current_index * 4
                fh.write(f"{mem_type} {address}\n")
                current_index += dense_stride
            fh.write(f"Phase {iter*2} End\n")
            fh.write(f"Phase {iter*2+1} Barrier {gpu_cores}\n")


## GPU cores, spare write array A, no share and no reuse

mem_type = "st"
increment = int(array_length_A/gpu_cores)

access_partition_start = [i for i in range(gpu_cores)]
access_partition = access_partition_start.copy()

for iter in range(iteration_no):
    equal = True if iter != 0 and access_partition == access_partition_start else False
    if equal:
        break
        
    for gpu_id in range(gpu_cores):
        cnt = 0
        key_name = f"gpu_core_{gpu_id}"
        mode = "w" if (iter == 0) else "a"
        start_index = access_partition[gpu_id]*increment
        end_index = start_index + increment
        with open(key_name+"_write_A_sparse_no_reuse.txt",mode) as fh:
            if iter == 0:
                fh.write(f"Phase 0 Barrier {cpu_cores}\n") ## phase 0 barrier needs two Ends for it to proceed
            else:
                fh.write(f"Phase {iter*2} Barrier {cpu_cores}\n")
            # previous_index = []
            current_index = start_index
            while current_index < end_index:
                # index = random.randint(start_index, end_index)
                address = current_index*4
                value = random.randint(1,100)
                fh.write(f"{mem_type} {address} {value}\n")
                current_index += sparse_stride
                # if index not in previous_index:
                #     previous_index.append(index)
                #     cnt = cnt + 1
            fh.write(f"Phase {iter*2+1} End\n")
            # fh.write(f"Phase {(iter+1)*2} Barrier {cpu_cores}\n")
    head = access_partition.pop(0)
    access_partition.append(head)