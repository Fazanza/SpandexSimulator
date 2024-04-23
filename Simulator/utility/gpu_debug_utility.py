from core.gpu import *
from utility.gpu_debug_utility import *

class gpu_debug:
    
    def __init__(self, gpu):
        self.gpu = gpu

    def print_generated_msg(self):
        print()
        print("generated msg: ")
        if self.gpu.generated_msg == None:
            print("No generated msg")
        else:
            self.gpu.generated_msg.print_msg()
    
    def print_rep_msg(self):
        print()
        print("rep_msg: ")
        if self.gpu.current_rep_msg == None:
            print("No Rep msg")
        else:
            self.gpu.current_rep_msg.print_msg()
    
    def print_current_inst(self):
        print()
        print("current insturction: ")
        self.gpu.current_inst.print_Inst()
    
    def print_barrier(self):
        print()
        print(f"barrier observed: {self.gpu.barrier_name_observed}")
        print(f"current_barrier: {self.gpu.barrier_name}")
        cnt = self.gpu.barrier_map.search(self.gpu.barrier_name)
        print(f"barrier {self.gpu.barrier_name} has {cnt} cnt")
    
    def print_barrier_map(self, key = None):
        print()
        print("### Barrier Map for GPU ###")
        self.gpu.barrier_map.print_Map(key)
    
    def print_gpu_wait(self):
        if self.gpu.wait == True:
            print("GPU is waiting: True")
        else:
            print("GPU is waiting: False")
        
    def print_gpu_info(self):
        # print(f"### current meessage for GPU at clk {time} ###")
        self.print_rep_msg()
        self.print_current_inst()
        self.print_generated_msg()
        self.print_barrier()
        self.print_gpu_wait()
    
    def print_is_finished(self):
        print("GPU Finished: {self.gpu.finish}")
    
    def print_Inst_Buffer(self):
        print()
        print("### GPU INSTRUCTION BUFFER ###")
        for Item in self.gpu.inst_buffer.items:
            if Item.inst_type == Inst_type.Barrier:
                print(f"Type: {Item.inst_type}, Addr: {Item.addr}, Barrier_name: {Item.barrier_name}")
            else:
                print(f"Type: {Item.inst_type}, Addr: {Item.addr}, PC: {Item.barrier_name}")
    
    def print_GPU_cache_set(self, addr):
        print()
        tag, index, offset = self.gpu.cache.parseAddr(addr)
        print(f"### GPU cache set contain {addr} ###")
        line_state = self.gpu.cache.line_state[index]
        line_tag = self.gpu.cache.line_tag[index]
        for i in range(len(line_state)):
            addr = line_tag[i] * self.gpu.cache.total_sets * self.gpu.cache.line_size + index * self.gpu.cache.line_size + offset
            print(f"Addr : {addr}, Line State : {line_state[i]}")