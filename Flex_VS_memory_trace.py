## data race free, do I need to take care of the accesses that are not going ot


import random

## Flex V/S memory traces

array_length_A = 1000
array_length_B = 1000

# Parameters
cpu_cores = 2
gpu_cores = 2
phase_no = 2
iteration_no = 20
more_actions = 500

increment = int(array_length_B/cpu_cores)
mem_type = "ld"

## CPU cores, dense read array B, no share no reuse

partition_index_pattern = {}

for iter in range(iteration_no):
    for phase in range(phase_no):
        access_partition = random.sample(range(cpu_cores), cpu_cores)  # random partition shuffle
        for cpu_id in range(cpu_cores):
            key_name = f"cpu_core_{cpu_id}_read_B_dense_no_share_reuse.txt"
            index_start = access_partition[cpu_id]*increment
            index_end = index_start + increment
            mode = "w" if (phase == 0 and iter == 0) else "a"
            density_cnt = 0
            with open(key_name,mode) as fh:
                if (iter == 0 and phase == 0):
                    prev_index = []
                    while density_cnt < int(increment*0.9): # count density
                        index = random.randint(index_start, index_end)
                        address = index*4
                        fh.write(f"{mem_type} {address}\n")  # output unique value address value
                        if index not in prev_index:
                            prev_index.append(index)
                            density_cnt = density_cnt + 1
                    for i in range(more_actions): # write more values
                        address = random.choice(prev_index) * 4
                        fh.write(f"{mem_type} {address}\n")
                        partition_index_pattern[access_partition[cpu_id]] = prev_index
                else:
                    prev_index = partition_index_pattern[access_partition[cpu_id]]
                    for i in range(more_actions):
                        address = random.choice(prev_index) * 4
                        fh.write(f"{mem_type} {address}\n")
                fh.write(f"Iter:{iter} Phase {phase} End\n")


## CPU cores, dense read array A, share and reuse

last_cpu_start = 500
per_cpu_range = array_length_A - last_cpu_start
increment = int(last_cpu_start/cpu_cores)

partition_index_pattern = {}

mem_type = "ld"

for iter in range(iteration_no):
    for phase in range(phase_no):
        for cpu_id in range(cpu_cores):
            mode = "w" if (phase == 0 and iter == 0) else "a"
            density_cnt = 0
            with open(f"cpu_core_{cpu_id}_read_A_dense_overlap.txt", mode) as fh:
                if (iter == 0 and phase == 0):
                    index_start = cpu_id*increment
                    index_end = index_start + increment
                    prev_index = []

                    while density_cnt < int(increment*0.9): # Dense or sparse access
                        index = random.randint(index_start, index_end)
                        address = index * 4
                        fh.write(f"{mem_type} {address}\n")
                        if index not in prev_index:
                            density_cnt += 1
                            prev_index.append(index)
                    for i in range(more_actions):
                        address = random.choice(prev_index) * 4
                        fh.write(f"{mem_type} {address}\n")
                    partition_index_pattern[cpu_id] = prev_index
                else:  # choose from previous index pattern
                    prev_index = partition_index_pattern[cpu_id]
                    for i in range(more_actions+500):
                        address = random.choice(prev_index) * 4
                        fh.write(f"{mem_type} {address}\n")
                fh.write(f"Iter:{iter} Phase {phase} End\n")



## GPU cores, spare write, no share and no reuse

mem_type = "st"
increment = int(array_length_A/gpu_cores)

partition_index_pattern = {}

for iter in range(iteration_no):
    for phase in range(phase_no):
        access_partition = random.sample(range(gpu_cores), gpu_cores)
        for gpu_id in range(gpu_cores):
            cnt = 0
            key_name = f"gpu_core_{gpu_id}"
            mode = "w" if (phase == 0 and iter == 0) else "a"
            start_index = access_partition[gpu_id]*increment
            end_index = start_index + increment
            with open(key_name+"write_A_sparse_no_reuse.txt",mode) as fh:
                if (iter == 0 and phase == 0):
                    previous_index = []
                    while cnt < int(increment*0.1):
                        index = random.randint(start_index, end_index)
                        address = index*4
                        value = random.randint(1,100)
                        fh.write(f"{mem_type} {address} {value}\n")
                        if index not in previous_index:
                            previous_index.append(index)
                            cnt = cnt + 1
                    for i in range(more_actions):
                        address = random.choice(previous_index) * 4
                        fh.write(f"{mem_type} {address}\n")
                    partition_index_pattern[access_partition[gpu_id]] = previous_index
                else:
                    for i in range(more_actions+500):
                        previous_index = partition_index_pattern[access_partition[gpu_id]]
                        address = random.choice(previous_index) * 4
                        fh.write(f"{mem_type} {address}\n")
                fh.write(f"Iter:{iter} Phase {phase} End\n")


## Dense Read and write array B with high reuse across GPU cores

increment = int(array_length_B/gpu_cores)
partition_index_pattern = {}

for iter in range(iteration_no):
    for phase in range(phase_no):
        mode = "w" if ((phase == 0 and iter == 0)) else "a"
        for gpu_id in range(gpu_cores):
            cnt = 0
            key_name = f"gpu_core_{gpu_id}"
            start_idx = gpu_id*increment
            end_idx = start_idx+increment

            with open(key_name+"read_write_B_dense_read_write_high_reuse.txt",mode) as fh:
                if (iter == 0 and phase == 0):
                    previous_index = []
                    while cnt < int(increment*0.9):
                        index = random.randint(start_idx, end_idx)
                        address = index*4
                        value = random.randint(1,100)
                        fh.write(f"ld {address}\n")
                        fh.write(f"st {address} {value}\n")
                        if index not in previous_index:
                            previous_index.append(index)
                            cnt = cnt + 1
                    for i in range(more_actions):
                        address = random.choice(previous_index) * 4
                        fh.write(f"{mem_type} {address}\n")
                    partition_index_pattern[gpu_id] = prev_index
                else:
                    previous_index = partition_index_pattern[gpu_id]
                    for i in range(more_actions):
                        address = random.choice(previous_index) * 4
                        fh.write(f"{mem_type} {address}\n")
                fh.write(f"Iter:{iter} Phase {phase} End\n")

