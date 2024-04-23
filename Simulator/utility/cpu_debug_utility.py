from core.cpu import *
from utility.cpu_debug_utility import *

class cpu_debug:
    
    def __init__(self, cpu):
        self.cpu = cpu

    def print_generated_msg_queue(self):
        print()
        self.cpu.generated_msg_queue.print_all()
    
    def print_rep_msg(self):
        print()
        print("rep_msg: ")
        if self.cpu.current_rep_msg == None:
            print("No Rep msg")
        else:
            self.cpu.current_rep_msg.print_msg()
    
    def print_req_msg(self):
        print()
        print("req_msg: ")
        if self.cpu.current_req_msg == None:
            print("No Rep msg")
        else:
            self.cpu.current_req_msg.print_msg()
    
    def print_current_inst(self):
        print()
        print("current insturction: ")
        self.cpu.current_inst.print_Inst()
    
    def print_barrier(self):
        print()
        print(f"barrier observed: {self.cpu.barrier_name_observed}")
        print(f"current_barrier: {self.cpu.barrier_name}")
        cnt = self.cpu.barrier_map.search(self.cpu.barrier_name)
        print(f"barrier {self.cpu.barrier_name} has {cnt} cnt")
    
    def print_barrier_map(self, key = None):
        print()
        print("### Barrier Map for CPU ###")
        self.cpu.barrier_map.print_Map(key)
    
    def print_cpu_wait(self):
        if self.cpu.wait == True:
            print("CPU is waiting: True")
        else:
            print("CPU is waiting: False")
        
    def print_cpu_info(self):
        # print(f"### current meessage for GPU at clk {time} ###")
        self.print_rep_msg()
        self.print_req_msg()
        self.print_current_inst()
        self.print_generated_msg_queue()
        self.print_barrier()
        self.print_cpu_wait()
    
    def print_is_finished(self):
        print("CPU Finished: {self.cpu.finish}")
    
    def print_Inst_Buffer(self):
        print()
        print("### CPU INSTRUCTION BUFFER ###")
        for Item in self.cpu.inst_buffer.items:
            if Item.inst_type == Inst_type.Barrier:
                print(f"Type: {Item.inst_type}, Addr: {Item.addr}, Barrier_name: {Item.barrier_name}")
            else:
                print(f"Type: {Item.inst_type}, Addr: {Item.addr}, PC: {Item.barrier_name}")
    
    def print_cpu_cache_set(self, addr):
        print()
        tag, index, offset = self.cpu.cache.parseAddr(addr)
        print(f"### CPU cache set contain {addr} ###")
        line_state = self.cpu.cache.line_state[index]
        line_tag = self.cpu.cache.line_tag[index]
        for i in range(len(line_state)):
            addr = line_tag[i] * self.cpu.cache.total_sets * self.cpu.cache.line_size + index * self.cpu.cache.line_size + offset
            print(f"Addr : {addr}, Line State : {line_state[i]}")