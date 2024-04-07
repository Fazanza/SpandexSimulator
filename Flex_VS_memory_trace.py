import random

## Flex V/S memory traces

array_length_A = 1000
array_length_B = 1000

stride_dense = 1
stride_sparse = 4
cpu_cores = 4
gpu_cores = 4
phase_no = 2

increment = int(array_length_B/cpu_cores)
# print(increment)
mem_type = "ld"
phase = 0


## CPU cores, dense read array B, no share no reuse
# dense_access_non_overlap = {}
while phase < phase_no:
  for i in range(cpu_cores):
    key_name = f"cpu_core_{i}_dense_no_share_reuse.txt"
    access_partition = random.sample(range(cpu_cores), cpu_cores)
    index_start = access_partition[i]*increment
    index_end = index_start + increment
    mode = "w" if (phase == 0) else "a"
    density_cnt = 0
    with open(key_name,mode) as fh:
      # cpu_address = []

      prev_index = []
      while density_cnt < int(increment*0.9):
      # for j in range(increment):
      # index = index_start+stride_dense
        index = random.randint(index_start, index_end)
        address = index*4
        fh.write(f"{mem_type} {address}\n")
        # cpu_address.append(address)
        if index not in prev_index:
          prev_index.append(index)
          density_cnt = density_cnt + 1
      # index_start = index
      fh.write(f"Phase {phase} End\n")
  phase = phase + 1

  # dense_access_non_overlap[key_name] = cpu_address


## CPU cores, dense read array A, share and reuse
# 0 - 400
# 25 - 400

dense_access_overlap = {}

last_start = 500
per_cpu_range = array_length_A - last_start
increment = int(last_start/cpu_cores)

mem_type = "ld"
phase = 0

while phase < phase_no:
  for i in range(cpu_cores):
    # key_name = f"cpu_core_{i}"
    mode = "w" if (phase == 0) else "a"
    density_cnt = 0
    with open(f"cpu_core_{i}_dense_overlap.txt", mode) as fh:
      index_start = i*increment
      index_end = index_start + increment
      prev_index = []
      while density_cnt < int(increment*0.9):
      # for j in range(per_cpu_range):
        index = random.randint(index_start, index_end) # (index_start + stride_dense)
        address = index * 4
        fh.write(f"{mem_type} {address}\n")
        if index not in prev_index:
          density_cnt += 1
          prev_index.append(index)
      fh.write(f"Phase {phase} End\n")
  phase = phase + 1



## GPU cores, spare write, no share and no reuse

mem_type = "st"
increment = int(array_length_A/gpu_cores)
print(increment)
phase = 0

while phase < phase_no:
  for i in range(gpu_cores):
    # print(phase)
    cnt = 0
    key_name = f"gpu_core_{i}"
    mode = "w" if (phase == 0) else "a"
    access_partition = random.sample(range(gpu_cores), cpu_cores)
    start_index = access_partition[i]*increment
    end_index = start_index + increment
    with open(key_name+"_sparse_no_reuse.txt",mode) as fh:
      previous_index = []
      while cnt < int(increment*0.1):
        index = random.randint(start_index, end_index)
        address = index*4
        value = random.randint(1,100)
        fh.write(f"{mem_type} {address} {value}\n")
        if index not in previous_index:
          previous_index.append(index)
          cnt = cnt + 1
      fh.write(f"Phase {phase} End\n")
  phase = phase + 1



## Dense Read and write array B with high reuse across GPU cores

increment = int(array_length_B/gpu_cores)
phase = 0

while phase < phase_no:
  mode = "w" if (phase == 0) else "a"
  for i in range(gpu_cores):
    cnt = 0
    key_name = f"gpu_core_{i}"
    start_idx = i*increment
    end_idx = start_idx+increment

    with open(key_name+"_dense_read_write_high_reuse.txt",mode) as fh:
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
      fh.write(f"Phase {phase} End\n")
  phase = phase + 1
