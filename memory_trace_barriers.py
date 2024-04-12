"""
Each cores accessing different regions on array
Multiple barriers, at least two cores waiting on one barrier
Still need acquire and release for gpu traces?

"""

import random


array_length = 1600
cpu_cores = 4
gpu_cores = 4
total_cores = cpu_cores + gpu_cores
iteration = 2
## generate access patterns
partition_range = int(array_length/(total_cores))
mem_type = ["ld","st"]
more_actions = int(partition_range/5)


def check_total_core_for_barrier(barrier_allocations):
    if sum(barrier_allocations) != total_cores:
       raise Exception("Barrier Allocation Wrong. Not equal to total core number")

def check_cores_per_barrier(barrier_allocations):
    for i in range(len(barrier_allocations)):
        if barrier_allocations[i] == 1:
            raise Exception(f"cores per Barrier Wrong. Barrier_{i} has only one core.")

# print(current_access)


max_barrier_num = int(total_cores/2) # need at least 2 cores for one barrier
print(f"max_barrier_num:{max_barrier_num}")

for iter in range(iteration):

    ## generate and distribute barriers
    barrier_num = random.randint(1,max_barrier_num)
    print(f"iter: {iter}, barrier_num: {barrier_num}")
    barrier_allocations = []
    total_cores_left = total_cores
    for barrier in range(barrier_num):
        core_num_per_barrier_upper_limit = total_cores_left - ((barrier_num-barrier-1) * 2)
        
        core_num_per_barrier = random.randint(2,core_num_per_barrier_upper_limit)
        # print(f"iter: {iter}, total_cores_left: {total_cores_left}, barrier: {barrier}, upper_limit: {core_num_per_barrier_upper_limit}, actual_num: {core_num_per_barrier}")
        if barrier == barrier_num-1:
            barrier_allocations.append(total_cores_left)
        else:
            barrier_allocations.append(core_num_per_barrier)
        total_cores_left = total_cores_left - core_num_per_barrier
    
    ## check exceptions
    check_total_core_for_barrier(barrier_allocations)
    check_cores_per_barrier(barrier_allocations)

    ## generate random access partition for cores
    current_access_partition = random.sample(range(total_cores), total_cores)

    mode = "w" if iter == 0 else "a"

    remain_barriers = barrier_allocations
    # print(remain_barriers)

    ## randomly choose cores for barrier
    for cpu_id in range(cpu_cores):
        assigned_barrier = random.choice(range(len(remain_barriers)))
        while remain_barriers[assigned_barrier] == 0:
            assigned_barrier = random.choice(range(len(remain_barriers)))
        
        unique_address = []
        density_count = 0
        stored_value = cpu_id*10 + 1

        with open(f"cpu_{cpu_id}.txt", mode) as fh:
            start_index = current_access_partition[cpu_id] * partition_range
            end_index = start_index + partition_range
            fh.write(f"current_partition:{current_access_partition[cpu_id]}\n")

            while density_count < int(0.9*partition_range):
                address = random.randint(start_index, end_index)
                if address not in unique_address:
                    unique_address.append(address)
                op_type = random.choice(mem_type)
                if op_type == "ld":
                    fh.write(f"{op_type} {address} cpu_{cpu_id}\n")
                else:
                    fh.write(f"{op_type} {address} {stored_value} cpu_{cpu_id}\n")
                density_count += 1

            for more in range(more_actions):
                op_type = random.choice(mem_type)
                address = random.choice(unique_address)
                if op_type == "ld":
                    fh.write(f"{op_type} {address} cpu_{cpu_id}\n")
                else:
                    fh.write(f"{op_type} {address} {stored_value} cpu_{cpu_id}\n")
            
            fh.write(f"barrier_{assigned_barrier} {barrier_allocations[assigned_barrier]}\n")
            remain_barriers[assigned_barrier] = remain_barriers[assigned_barrier] - 1
            print(remain_barriers)
    

    for gpu_id in range(gpu_cores):
        assigned_barrier = random.choice(range(len(remain_barriers)))
        while remain_barriers[assigned_barrier] == 0:
            assigned_barrier = random.choice(range(len(remain_barriers)))
        
        unique_address = []
        density_count = 0

        stored_value = (cpu_cores + gpu_id)*10 + 1
        with open(f"gpu_{gpu_id}.txt", mode) as fh:
            start_index = current_access_partition[gpu_id+cpu_cores] * partition_range
            end_index = start_index + partition_range
            fh.write(f"current_partition:{current_access_partition[gpu_id+cpu_cores]}\n")

            while density_count < int(0.9*partition_range):
                address = random.randint(start_index, end_index)
                if address not in unique_address:
                    unique_address.append(address)
                op_type = random.choice(mem_type)
                if op_type == "ld":
                    fh.write(f"{op_type} {address} gpu_{gpu_id}\n")
                else:
                    fh.write(f"{op_type} {address} {stored_value} gpu_{gpu_id}\n")
                density_count += 1

            for more in range(more_actions):
                op_type = random.choice(mem_type)
                address = random.choice(unique_address)
                if op_type == "ld":
                    fh.write(f"{op_type} {address} gpu_{gpu_id}\n")
                else:
                    fh.write(f"{op_type} {address} {stored_value} gpu_{gpu_id}\n")
            
            fh.write(f"barrier_{assigned_barrier} {barrier_allocations[assigned_barrier]}\n")
            remain_barriers[assigned_barrier] = remain_barriers[assigned_barrier] - 1
            print(remain_barriers)

    if sum(remain_barriers) != 0:
       raise Exception("Incorrect Barrier Distribution.")
