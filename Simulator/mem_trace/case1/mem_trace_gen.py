import random

# Parameters
share_start = 0
share_end = 32

secA_start = 512 + 0
secA_end = 512 + 31
secB_start = 512 + 32
secB_end = 512 + 63
secC_start = 512 + 64
secC_end = 512 + 95
secD_start = 512 + 96
secD_end = 512 + 128

mem_type = ["ld", "st"]


def cpu_write_block(sec_start, sec_end, block_size, file, core_id):
    private_start = 128 + core_id * 32
    private_end = 159 + core_id * 32
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


# Case 1, 1 cpu 1 gpu, the cpu dispatch task to gpu
with open('cpu0.txt', 'w') as file:
    cpu_write_block(secA_start, secA_end, 10, file, 0)
    file.write("Barrier 0 2\n")
    cpu_write_block(secB_start, secB_end, 10, file, 0)
    file.write("Barrier 0 2\n")
    cpu_write_block(secC_start, secC_end, 10, file, 0)
    file.write("Barrier 0 2\n")
    cpu_write_block(secD_start, secD_end, 10, file, 0)
    file.write("Barrier 0 2\n")

with open('gpu0.txt', 'w') as file:
    file.write("Barrier 0 2\n")
    gpu_write_block(secA_start, secA_end, 100, file)
    file.write("Barrier 0 2\n")
    gpu_write_block(secB_start, secB_end, 100, file)
    file.write("Barrier 0 2\n")
    gpu_write_block(secC_start, secC_end, 100, file)
    file.write("Barrier 0 2\n")
    gpu_write_block(secD_start, secD_end, 100, file)
