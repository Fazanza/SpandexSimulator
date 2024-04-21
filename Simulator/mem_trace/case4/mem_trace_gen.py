import random

# Parameters
share_start = 0
share_end = 63

secA_start = 4096 + 0
secA_end = 4096 + 127
secB_start = 4096 + 128
secB_end = 4096 + 255
secC_start = 4096 + 256
secC_end = 4096 + 383
secD_start = 4096 + 384
secD_end = 4096 + 512

mem_type = ["ld", "st"]


def cpu_write_block(sec_start, sec_end, block_size, file, core_id):
    private_start = 1024 + core_id * 128
    private_end = 1151 + core_id * 128
    for i in range(block_size):
        choice = random.randint(1, 3)
        if choice == 1:
            file.write(random.choice(['st ', 'ld ']) + str(random.randint(sec_start, sec_end)) + "\n")
        elif choice == 2:
            file.write(random.choice(['st ', 'ld ']) + str(random.randint(share_start, share_end)) + "\n")
        else:
            file.write(random.choice(['st ', 'ld ']) + str(random.randint(private_start, private_end)) + "\n")


def gpu_write_block(sec_start, sec_end, block_size, file):
    for i in range(block_size):
        file.write(random.choice(['st ', 'ld ']) + str(random.randint(sec_start, sec_end)) + "\n")


# Case 4, 4 cpu 1 gpu, the cpu dispatch task to gpu
# Higher contention than case 3
with open('cpu0.txt', 'w') as file:
    cpu_write_block(secA_start, secA_end, 200, file, 0)
    file.write("Barrier 0 2\n")
    file.write("Barrier 1 3\n")
    cpu_write_block(secA_start, secA_end, 800, file, 0)

with open('cpu1.txt', 'w') as file:
    cpu_write_block(secB_start, secB_end, 300, file, 1)
    file.write("Barrier 1 3\n")
    file.write("Barrier 2 3\n")
    cpu_write_block(secB_start, secB_end, 700, file, 1)

with open('cpu2.txt', 'w') as file:
    cpu_write_block(secC_start, secC_end, 400, file, 2)
    file.write("Barrier 2 3\n")
    file.write("Barrier 3 3\n")
    cpu_write_block(secC_start, secC_end, 600, file, 2)

with open('cpu3.txt', 'w') as file:
    cpu_write_block(secD_start, secD_end, 500, file, 3)
    file.write("Barrier 3 3\n")
    file.write("Barrier 4 2\n")
    cpu_write_block(secD_start, secD_end, 500, file, 3)

with open('gpu0.txt', 'w') as file:
    file.write("Barrier 0 2\n")
    gpu_write_block(secA_start, secA_end, 200, file)
    file.write("Barrier 1 3\n")
    gpu_write_block(secB_start, secB_end, 200, file)
    file.write("Barrier 2 3\n")
    gpu_write_block(secC_start, secC_end, 200, file)
    file.write("Barrier 3 3\n")
    gpu_write_block(secD_start, secD_end, 200, file)
    file.write("Barrier 4 2\n")
