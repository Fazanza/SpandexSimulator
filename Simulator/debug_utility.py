from llc import *
from gpu import *
from debug_utility import *

class llc_debug:
    def __init__(self, llc):
        self.llc = llc
        
    def print_current_msg(self):
        print(f"### current meessage for LLC at clk {self.llc.clk_cnt - 1} ###")
        if self.llc.current_rep_msg == None:
            print("No Rep msg")
        else:
            self.llc.current_rep_msg.print_msg()
        if self.llc.current_mem_msg == None:
            print("No Mem msg")
        else:
            self.llc.current_mem_msg.print_msg()
        if self.llc.current_req_msg == None:
            print("No Req msg")
        else:
            self.llc.current_req_msg.print_msg()

    
    def print_cache_state(self, addr):
        print(f"### cache state for {addr} ###")
        print(f"line_state: {self.llc.cache.getState_line(addr)}")
        print(f"word_state: {self.llc.cache.getState_word(addr)}")
        print(f"all_word state: {self.llc.cache.getState_allword(addr)}")
    
    def print_cache_sharer(self, addr):
        print(f"### cache sharer for {addr} ###")
        print(self.llc.cache.get_sharer(addr))
    
    def print_cache_owner(self, addr):
        print(f"### cache owner for {addr} ###")
        print(self.llc.cache.getOwner(addr))
        
    def print_LLC_request_box(self):
        self.llc.req_msg_box.print_all()
        
    def print_LLC_response_box(self):
        self.llc.rep_msg_box.print_all()
        
    def print_LLC_mem_queue(self):
        self.llc.mem_req_queue.print_all()
        
    def print_LLC_generated_msg_queue(self):
        self.llc.generated_msg_queue.print_all()
        
    def print_LLC_cache_set(self, addr):
        print()
        tag, index, offset = self.llc.cache.parseAddr(addr)
        print(f"### LLC cache set contain {addr} ###")
        line_state = self.llc.cache.line_state[index]
        line_tag = self.llc.cache.line_tag[index]
        for i in range(len(line_state)):
            addr = line_tag[i] * self.gpu.cache.total_sets * self.gpu.cache.line_size + index * self.gpu.cache.line_size + offset
            print(f"Addr : {addr}, Line State : {line_state[i]}")
            
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
            print(f"Type: {Item.inst_type}, Addr: {Item.addr}, Barrier_name: {Item.barrier_name}")
    
    def print_GPU_cache_set(self, addr):
        print()
        tag, index, offset = self.gpu.cache.parseAddr(addr)
        print(f"### GPU cache set contain {addr} ###")
        line_state = self.gpu.cache.line_state[index]
        line_tag = self.gpu.cache.line_tag[index]
        for i in range(len(line_state)):
            addr = line_tag[i] * self.gpu.cache.total_sets * self.gpu.cache.line_size + index * self.gpu.cache.line_size + offset
            print(f"Addr : {addr}, Line State : {line_state[i]}")