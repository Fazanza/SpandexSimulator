from core.llc import *
from utility.llc_debug_utility import *

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
            addr = line_tag[i] * self.llc.cache.total_sets * self.llc.cache.line_size + index * self.llc.cache.line_size + offset
            print(f"Addr : {addr}, Line State : {line_state[i]}")
            



