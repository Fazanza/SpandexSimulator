import math
from enum import Enum, auto
import random
from collections import deque
from gpu_utility import *
from gpu import *



class GPU_Controller:

    def __init__(self, cache_size, ways, line_size, memory_size, file_name):
        self.cache      = GPU_cache(cache_size, ways, line_size, memory_size)
        self.rep_msg_box = Queue()
        self.inst_buffer = Queue()
        self.barrier_map = Map()
        self.finish = False
        self.clk_cnt = 0
        self.generated_msg = None
        self.generated_msg_send = None # the message which send to LLC
        self.wait = False
        self.current_inst = None
        
    def Fill_Inst(self, file_name):
        with open(file_name, 'r') as file:
            for line in file:
                elements = line.split()
                inst = []
                if elements[0] == "ld":
                    inst_type = Inst_type.Load
                    addr = int(elements[1])
                    inst = Inst(inst_type, addr, 0)
                elif elements[0] == "st":
                    inst_type = Inst_type.Store
                    addr = int(elements[1])
                    inst = Inst(inst_type, addr, 0)
                elif elements[0] == "Barrier":
                    inst_type = Inst_type.Barrier
                    barrier_name = int(elements[1])
                    inst = Inst(inst_type, 0, barrier_name)
                    self.barrier_map.inst(barrier_name, int(elements[2]))
                else:
                    print("There is undefine instruction type")
                self.barrier_map.enqueue(inst)

    def get_new_rep(self):
        if self.rep_msg_box.is_empty():
            return None
        else:
            msg = self.rep_msg_box.dequeue(self)
            return msg
        
    # get new instruction from instruction buffer
    def get_new_inst(self):
        if self.inst_buffer.is_empty():
            self.finish = True
            return None
        else:
            return self.inst_buffer.peek()

    ## check if instruction can be executed, if there are still pending request on target address, the instruction can not be executed
    def is_inst_qualified(self, addr):
        state = self.cache.getState_line(addr)
        if state == State.I or state == State.V or state == State.VI:
            return True
        else:
            return False

    def get_current_state(self, input_msg):
        line_state = self.cache.getState_line(input_msg.addr)
        return line_state
    
        
    def do_transition(self, current_state, input_msg):
        msg_addr = input_msg.addr
        self.generated_msg = None
        ###########################
        if current_state == State.I:
            ###
            if input_msg.msg_type == msg_type.Load:
                self.generated_msg = Msg(msg_type.ReqV, msg_addr, Node.GPU, Node.LLC, 0, Node.NULL)
                self.cache.updateState_line_word(msg_addr, State.IV)
            ###
            elif input_msg.msg_type == msg_type.Store:
                self.generated_msg = Msg(msg_type.ReqWT, msg_addr, Node.GPU, Node.LLC, 0, Node.NULL)
                self.cache.updateState_word(msg_addr, State.WTV)
                self.cache.updateState_line(msg_addr, State.WTV)
            ###
            else:
                return type.Block
            
        ###########################
        elif current_state == State.V:
            ###
            if input_msg.msg_type == msg_type.Load:
               return type.Success
            ###
            elif input_msg.msg_type == msg_type.Store:
                self.generated_msg = Msg(msg_type.ReqWT, msg_addr, Node.GPU, Node.LLC, 0, Node.NULL)
                self.cache.updateState_word(msg_addr, State.WTV)
                self.cache.updateState_line(msg_addr, State.WTV)
            ###
            else:
                return type.Error
            
        ###########################
        elif current_state == State.IV:
            ###
            if input_msg.msg_type == msg_type.RepV:
                self.cache.updateState_line_word(msg_addr, State.V)
            ###
            elif input_msg.msg_type == msg_type.Load:
                return type.Block
            ###
            elif input_msg.msg_type == msg_type.Store:
                return type.Block
            ###
            else:
                return type.Error
        
        ###########################
        elif current_state == State.VI:
            ###
            if input_msg.msg_type == msg_type.Load:
                self.cache.updateState_line_word(msg_addr, State.IV)
                self.generated_msg = Msg(msg_type.ReqV, msg_addr, Node.GPU, Node.LLC, 0, Node.NULL)
            ###
            elif input_msg.msg_type == msg_type.Store:
                self.cache.updateState_line(msg_addr, State.WTV)
                self.cache.updateState_word(msg_addr, State.WTV)
                self.generated_msg = Msg(msg_type.ReqWT, msg_addr, Node.GPU, Node.LLC, 0, Node.NULL)
            ###
            else:
                return type.Error
        ##########################
        elif current_state == State.WTV:
            if input_msg.msg_type == msg_type.Load:
                return type.Block
            ###
            elif input_msg.msg_type == msg_type.Store:
                return type.Block
            ###
            elif input_msg.msg_type == msg_type.RepWT:
                self.cache.updateState_word(msg_addr, State.V)
                word_state = self.cache.getState_all_word(msg_addr)
                all_V = True
                for item in word_state:
                    if item != State.V:
                        all_V = False
                if all_V == False:
                    self.cache.updateState_line(msg_addr, State.VI)
                else:
                    self.cache.updateState_line(msg_addr, State.V)
            else:
                return type.Error
        else:
            return type.Error
        return type.Success
    
    # for getting response from LLC
    def receieve_rep_msg(self, msg_type, addr, src, dst, ack_cnt, fwd_dst):
        assert src == Node.LLC, "Error! GPU is getting response outside LLC"
        msg = Msg(msg_type, addr, src, dst, ack_cnt, fwd_dst)
        self.rep_msg_box.enqueue(msg)
        
    # receiece barrier info from top, call one time if One Node send a barrier before GPU execution in the same cycle
    def receieve_barrier(self, barrier_name):
        if barrier_name != None:
            current_value = self.barrier_map.search(barrier_name)
            self.barrier_map.change(barrier_name, current_value-1)
            if current_value == 1:
                self.wait = False

    def GPU_run(self):
        # First execute response
        rep_msg = self.get_new_rep()
        if rep_msg != None:
            current_state = self.get_current_state(rep_msg)
            result = self.do_transition(current_state, rep_msg)
            if result == type.Error:
                print("Error when GPU receieve response")
        assert self.generated_msg == None, "Error! GPU generate new message when execute response"
        
        # Second execute an instruction
        # 1. wait for barrier
        # 2. wait for LLC message queue available
        if self.wait == True:
            if self.current_inst.inst_type == Inst_type.Barrier:
                assert self.generated_msg_send == None, "Error! GPU if current instruction is Barrier, should not send any instruction"
            return self.generated_msg_send, None

        inst = self.get_new_inst()
        if inst == None:
            self.finish = True
            print("GPU finish execution")
            return None, None;
        self.current_inst = inst
        if inst.inst_type == Inst_type.Load:
            if self.is_inst_qualified(inst.addr) == True:
                inst_msg = Msg(msg_type.Load, inst.addr, Node.GPU, Node.GPU, 0, Node.NULL)
                current_state = self.get_current_state(inst_msg)
                assert self.do_transition(current_state, inst_msg) == type.Success, "Error! GPU wrong when execute Load instruction"
        elif inst.inst_type == Inst_type.Store:
            if self.is_inst_qualified(inst.addr) == True:
                inst_msg = Msg(msg_type.Store, inst.addr, Node.GPU, Node.GPU, 0, Node.NULL)
                current_state = self.get_current_state(inst_msg)
                assert self.do_transition(current_state, inst_msg) == type.Success, "Error! GPU wrong when execute Store instruction"
        elif inst.inst_type == Inst_type.Barrier:
            self.receieve_barrier(inst.barrier_name)
            if self.barrier_map.search(inst.barrier_name) != 0:
                self.wait = True
            else:
                self.wait  = False
                self.inst_buffer.dequeue()
                self.cache.clear() # self invalidation after pass barrier
            return None, inst.barrier_name
                
        self.generated_msg_send = self.generated_msg
        return self.generated_msg_send, None
    
    ## this function should take the response from Top, have to follow GPU_RUN(), after receieve_barrier
    #  whether the previous generated msg can be taken by LLC
    #  msg_taken should be None if self.generated_msg_send == None
    def GPU_POST_RUN(self, msg_taken):
        if msg_taken == True:
            assert self.current_inst.inst_type == Inst_type.Load or self.current_inst.inst_type == Inst_type.Store
            self.wait  = False
            self.inst_buffer.dequeue()
        elif msg_taken == False:
            self.wait = True

    #############
    # 1. Every Node before GPU execution, Call receieve_barrier()
    # 2. When GPU execution
    #   2.1 first call receieve_rep_msg()
    #   2.2 Then call GPU_RUN()
    #   2.3 After check LLC req_msg_Box is full or not, call GPU_POST_RUN()