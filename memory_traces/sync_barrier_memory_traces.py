### barrier implementation

import random
import math

## Parameters
cpu_core = 3
gpu_core = 1
total_barriers = 5
array_length = 100

barrier_per_core_low = 2

if total_barriers - barrier_per_core_low < cpu_core:
    additional_barrier_per_core = 1
else:
    additional_barrier_per_core = math.ceil((total_barriers - barrier_per_core_low) / cpu_core)


## Genrate barrier pattern first
## Rule: at least two cores per barrier

partition_range = int(array_length/total_barriers)
num_access_gpu = partition_range*2
mem_type = ["ld","st"]

barrier_partition = {}
barrier_num_waiter = [1 for i in range(total_barriers)]
for cpu in range(cpu_core):
    sampled_barrier = random.sample(range(total_barriers), random.randint(2,total_barriers-1))

    for item in sampled_barrier:
        barrier_num_waiter[item] += 1
    # sampled_barrier.sort()

    for addi in range(additional_barrier_per_core):
        for i, value in enumerate(barrier_num_waiter):
            if barrier_num_waiter[i] == 1:
                barrier_num_waiter[i] += 1
                sampled_barrier.append(i)
        
    sampled_barrier.sort()
    barrier_partition[cpu] = sampled_barrier

print(barrier_partition)
print(f"value num: {barrier_num_waiter}")
for value in barrier_num_waiter:
    if (value < 2) or (value > (cpu_core + gpu_core)):
        raise Exception("Barrier Allocation Incorrect")


## Generate gpu memory traces

for barrier_no in range(total_barriers):
    index_start = barrier_no*partition_range
    index_end = (barrier_no+1)*partition_range-1 if (barrier_no < total_barriers-1) else (array_length-1)

    mode = "w" if barrier_no == 0 else "a"

    with open("gpu_0.txt", mode) as fh:
        for access in range(num_access_gpu):
            address = random.randint(index_start, index_end)
            mem = random.choice(mem_type)
            # stored_value = random.randint(1,100)
            if mem == "ld":
                fh.write(f"{mem} {address}\n")
            else:
                fh.write(f"{mem} {address}\n")
        fh.write(f"Barrier {barrier_no} {barrier_num_waiter[barrier_no]}\n")


## Generate cpu memory traces

for cpu_id in range(cpu_core):

    ## Generate random barriers for cpu core
    # sampled_barrier = random.sample(range(total_barriers), random.randint(2,total_barriers-1))
    # sampled_barrier.sort()
    # print(sampled_barrier)
    sampled_barrier = barrier_partition[cpu_id]

    for idx in range(len(sampled_barrier)):
        current_barrier = sampled_barrier[idx]
        previous_barrier = -1 if idx == 0 else sampled_barrier[idx-1]

        # generate available partitions besides locked ones
        if previous_barrier == -1:
            available_partition = [i for i in range(total_barriers) if (i > current_barrier)]
        else:
            available_partition = [i for i in range(total_barriers) if (i > current_barrier or i <= previous_barrier)]

        for item in available_partition:
            if (item > previous_barrier) and (item <= current_barrier):
                raise Exception("Illegal partion accessed")

        ## access or modify available partitions 
        mode = "w" if idx == 0 else "a"
        no_opreations_necessary = len(available_partition) * partition_range * 2
        with open(f"cpu_{cpu_id}.txt", mode) as fh:
            for action in range(no_opreations_necessary):
                mem = random.choice(mem_type)
                chosen_partition = random.choice(available_partition) if mem == "st" else random.choice(range(total_barriers))
                index_start = chosen_partition * partition_range
                index_end = (chosen_partition+1) * partition_range - 1 if (chosen_partition < total_barriers) else (array_length-1)
                address = random.randint(index_start, index_end)
                if mem == "ld":
                    fh.write(f"{mem} {address}\n")
                else:
                    fh.write(f"{mem} {address}\n")
            fh.write(f"Barrier {current_barrier} {barrier_num_waiter[current_barrier]}\n")
