import math
from enum import Enum, auto
import random
from collections import deque
from utility.cpu_utility import *
from core.cpu import *



class CPU_Controller:

    def __init__(self, cache_size, ways, line_size, memory_size, file_name, Node):
        self.cache      = CPU_cache(cache_size, ways, line_size, memory_size)
        self.rep_msg_box = Queue()
        self.req_msg_box = Queue()
        self.inst_buffer = Queue()
        self.generated_msg_queue = Queue() # the message which send to LLC
        self.barrier_map = Map()
        self.finish = False
        self.inst_empty = False
        self.clk_cnt = 0
        self.wait = False
        self.current_inst = None
        self.current_rep_msg = None
        self.current_req_msg = None
        self.barrier_name = None
        self.barrier_name_observed = None
        self.Node = Node
        self.Fill_Inst(file_name)
        
    def Fill_Inst(self, file_name):
        with open(file_name, 'r') as file:
            pc = 0
            for line in file:
                elements = line.split()
                inst = []
                if elements[0] == "ld":
                    inst_type = Inst_type.Load
                    addr = int(elements[1])
                    inst = Inst(inst_type, addr, pc + 1)
                elif elements[0] == "st":
                    inst_type = Inst_type.Store
                    addr = int(elements[1])
                    inst = Inst(inst_type, addr, pc + 1)
                elif elements[0] == "Barrier":
                    inst_type = Inst_type.Barrier
                    barrier_name = int(elements[1])
                    inst = Inst(inst_type, 0, barrier_name)
                    assert int(elements[2]) > 1, "Error! Barrier number is less than 2"
                    self.barrier_map.insert(barrier_name, int(elements[2]))
                else:
                    print("There is undefine instruction type")
                self.inst_buffer.enqueue(inst)
                pc = pc + 1
    
    def get_new_rep(self):
        if self.rep_msg_box.is_empty():
            print("CPU rep box empty")
            return None
        else:
            msg = self.rep_msg_box.dequeue()
            return msg
    
    def get_new_req(self): # request for CPU is not guarantee to proceed
        if self.req_msg_box.is_empty():
            print("CPU req box empty")
            return None
        else:
            msg = self.req_msg_box.peek()
            return msg
    
    def take_new_req(self): # take new request from req msg box
        self.req_msg_box.dequeue()
        
    # get new instruction from instruction buffer
    def get_new_inst(self):
        if self.inst_buffer.is_empty():
            self.inst_empty = True
            return None
        else:
            return self.inst_buffer.peek()
        
    ## check if instruction can be executed, if there are still pending request on target address, the instruction can not be executed
    def is_inst_qualified(self, addr):
        state = self.cache.getState_line(addr)
        if state == State.I or state == State.S or state == State.M:
            return True
        else:
            return False

    def get_current_state(self, input_msg):
        line_state = self.cache.getState_line(input_msg.addr)
        return line_state
    
    def cache_add_newline(self, addr):
        if self.cache.addNewLine(addr) == True: ## there is empty line
            return True
        else: # should evict the cache line
            evict_addr, evict_line_state = self.cache.getLRU(addr)
            if self.is_inst_qualified(evict_addr):
                evict_state = self.cache.getState_line(evict_addr)
                if evict_state == State.M: # block the instruction if the evict addr is in O state
                    gen_msg = Msg(msg_type.PutM, evict_addr, self.Node, Node.LLC) # only trigger when execute an instruction
                    self.cache.updateState_line(evict_addr, State.MI_A)
                    self.generated_msg_queue.enqueue(gen_msg)
                    return False
                self.cache.updateState_line(addr, State.I)
                self.cache.addNewLine(addr)
                return True
            else: # the evicted cache block is in transient state, can not evict
                return False
        
    def do_transition(self, current_state, input_msg):
        msg_addr = input_msg.addr
        gen_msg = None
        # self.generated_msg = None
        ###########################
        if current_state == State.I:
            if self.cache_add_newline(msg_addr) == False: # can not add the new line into CPU
                return type.Block, None
            ###
            if input_msg.msg_type == msg_type.Load:
                gen_msg = Msg(msg_type.GetS, msg_addr, self.Node, Node.LLC)
                self.cache.updateState_line(msg_addr, State.IS_D)
            ###
            elif input_msg.msg_type == msg_type.Store:
                gen_msg = Msg(msg_type.GetM, msg_addr, self.Node, Node.LLC)
                self.cache.updateState_line(msg_addr, State.IM_D)
            ###
            elif input_msg.msg_type == msg_type.Inv:
                assert input_msg.src == Node.LLC, "Error! Inv for CPU should only come from LLC"
                if input_msg.target_addr != None:
                    gen_msg = Msg(msg_type.InvAck, input_msg.target_addr, self.Node, Node.LLC)
                else:
                    gen_msg = Msg(msg_type.InvAck, msg_addr, self.Node, Node.LLC)
            else:
                return type.Error, None
            
        ###########################
        elif current_state == State.IS_D:
            ###
            if input_msg.msg_type == msg_type.Load:
                return type.Block, None
            ###
            elif input_msg.msg_type == msg_type.Store:
                return type.Block, None
            ###
            elif input_msg.msg_type == msg_type.Inv:
                assert input_msg.src == Node.LLC, "Error! Inv for CPU should only come from LLC"
                if input_msg.target_addr != None:
                    gen_msg = Msg(msg_type.InvAck, input_msg.target_addr, self.Node, Node.LLC)
                else:
                    gen_msg = Msg(msg_type.InvAck, msg_addr, self.Node, Node.LLC)
            ###
            elif input_msg.msg_type == msg_type.DataDir:
                self.cache.updateState_line(msg_addr, State.S)
            else:
                return type.Error, None
            
        ###########################
        elif current_state == State.IM_D:
            if self.Node == Node.CPU0:
                print("EEEE")
                print(input_msg.msg_type)
                print(input_msg.addr)
                print(input_msg.src)
            ###
            if input_msg.msg_type == msg_type.Load:
                return type.Block, None
            ###
            elif input_msg.msg_type == msg_type.Store:
                return type.Block, None
            ###
            elif input_msg.msg_type == msg_type.Inv:
                assert input_msg.src == Node.LLC, "Error! Inv for CPU should only come from LLC"
                if input_msg.target_addr != None:
                    gen_msg = Msg(msg_type.InvAck, input_msg.target_addr, self.Node, Node.LLC)
                else:
                    gen_msg = Msg(msg_type.InvAck, msg_addr, self.Node, Node.LLC)
            ###
            elif input_msg.msg_type == msg_type.FwdGetS:
                return type.Block, None
                ###
            elif input_msg.msg_type == msg_type.FwdGetM:
                return type.Block, None
            ###
            elif input_msg.msg_type == msg_type.DataDir:
                self.cache.updateState_line(msg_addr, State.M)
            ###
            elif input_msg.msg_type == msg_type.DataOwner:
                self.cache.updateState_line(msg_addr, State.M)
            else:
                return type.Error, None
        
        ###########################
        elif current_state == State.S:
            ###
            if input_msg.msg_type == msg_type.Load:
                return type.Success, None
            ###
            elif input_msg.msg_type == msg_type.Store:
                gen_msg = Msg(msg_type.GetM, msg_addr, self.Node, Node.LLC)
                self.cache.updateState_line(msg_addr, State.SM_D)
            ###
            elif input_msg.msg_type == msg_type.Inv:
                print(input_msg.src)
                assert input_msg.src == Node.LLC, "Error! Inv for CPU should only come from LLC"
                if input_msg.target_addr != None:
                    gen_msg = Msg(msg_type.InvAck, input_msg.target_addr, self.Node, Node.LLC)
                else:
                    gen_msg = Msg(msg_type.InvAck, msg_addr, self.Node, Node.LLC)
            ###
            else:
                return type.Error, None

        ##########################
        elif current_state == State.SM_D:
            if input_msg.msg_type == msg_type.Load:
                return type.Success, None
            ###
            elif input_msg.msg_type == msg_type.Store:
                return type.Block, None
            ###
            elif input_msg.msg_type == msg_type.FwdGetS:
                return type.Block, None
            ###
            elif input_msg.msg_type == msg_type.FwdGetM:
                return type.Block, None
            ###
            elif input_msg.msg_type == msg_type.Inv:
                assert input_msg.src == Node.LLC, "Error! Inv for CPU should only come from LLC"
                if input_msg.target_addr != None:
                    gen_msg = Msg(msg_type.InvAck, input_msg.target_addr, self.Node, Node.LLC)
                else:
                    gen_msg = Msg(msg_type.InvAck, msg_addr, self.Node, Node.LLC)
                self.cache.updateState_line(msg_addr, State.IM_D)
            ###
            elif input_msg.msg_type == msg_type.DataDir:
                self.cache.updateState_line(msg_addr, State.M)
            else:
                return type.Error, None
            
        ##########################
        elif current_state == State.M:
            if input_msg.msg_type == msg_type.Load:
                return type.Success, None
            ###
            elif input_msg.msg_type == msg_type.Store:
                return type.Success, None
            ###
            elif input_msg.msg_type == msg_type.FwdGetS:
                gen_msg = Msg(msg_type.Data, msg_addr, self.Node, Node.LLC)
                self.cache.updateState_line(msg_addr, State.S)
            ###
            elif input_msg.msg_type == msg_type.FwdGetM:
                assert input_msg.fwd_dst != Node.NULL, f"Error! CPU receieve GetM and forward data to Wrong Node: {input_msg.fwd_dst}"
                gen_msg = Msg(msg_type.DataOwner, msg_addr, self.Node, input_msg.fwd_dst)
                self.cache.updateState_line(msg_addr, State.I)
            ###
            elif input_msg.msg_type == msg_type.Inv:
                assert input_msg.src == Node.LLC, "Error! Inv for CPU should only come from LLC"
                if input_msg.target_addr != None:
                    gen_msg = Msg(msg_type.InvAck, input_msg.target_addr, self.Node, Node.LLC)
                else:
                    gen_msg = Msg(msg_type.InvAck, msg_addr, self.Node, Node.LLC)
            else:
                return type.Error, None
        
        ##########################
        elif current_state == State.MI_A:
            ###
            if input_msg.msg_type == msg_type.Load:
                return type.Block, None
            ###
            elif input_msg.msg_type == msg_type.Store:
                return type.Block, None
            ###
            elif input_msg.msg_type == msg_type.FwdGetS:
                gen_msg = Msg(msg_type.Data, msg_addr, self.Node, Node.LLC)
                self.cache.updateState_line(msg_addr, State.SI_A)
            ###
            elif input_msg.msg_type == msg_type.FwdGetM:
                assert input_msg.fwd_dst != Node.NULL and input_msg.fwd_dst != Node.LLC, f"Error! CPU receieve GetM and forward data to Wrong Node: {input_msg.fwd_dst}"
                gen_msg = Msg(msg_type.DataOwner, msg_addr, self.Node, input_msg.fwd_dst)
                self.cache.updateState_line(msg_addr, State.II_A)
            ###
            elif input_msg.msg_type == msg_type.Inv:
                assert input_msg.src == Node.LLC, "Error! Inv for CPU should only come from LLC"
                if input_msg.target_addr != None:
                    gen_msg = Msg(msg_type.InvAck, input_msg.target_addr, self.Node, Node.LLC)
                else:
                    gen_msg = Msg(msg_type.InvAck, msg_addr, self.Node, Node.LLC)
            ###
            elif input_msg.msg_type == msg_type.PutAck:
                self.cache.updateState_line(msg_addr, State.I)
            else:
                return type.Error, None
        
        ##########################
        elif current_state == State.SI_A:
            ###
            if input_msg.msg_type == msg_type.Load:
                return type.Block, None
            ###
            elif input_msg.msg_type == msg_type.Store:
                return type.Block, None
            ###
            elif input_msg.msg_type == msg_type.Inv:
                assert input_msg.src == Node.LLC, "Error! Inv for CPU should only come from LLC"
                if input_msg.target_addr != None:
                    gen_msg = Msg(msg_type.InvAck, input_msg.target_addr, self.Node, Node.LLC)
                else:
                    gen_msg = Msg(msg_type.InvAck, msg_addr, self.Node, Node.LLC)
                self.cache.updateState_line(msg_addr, State.II_A)
            ###
            elif input_msg.msg_type == msg_type.PutAck:
                self.cache.updateState_line(msg_addr, State.I)
            else:
                return type.Error, None
        
        ##########################
        elif current_state == State.II_A:
            ###
            if input_msg.msg_type == msg_type.Load:
                return type.Block, None
            ###
            elif input_msg.msg_type == msg_type.Store:
                return type.Block, None
            ###
            elif input_msg.msg_type == msg_type.Inv:
                assert input_msg.src == Node.LLC, "Error! Inv for CPU should only come from LLC"
                if input_msg.target_addr != None:
                    gen_msg = Msg(msg_type.InvAck, input_msg.target_addr, self.Node, Node.LLC)
                else:
                    gen_msg = Msg(msg_type.InvAck, msg_addr, self.Node, Node.LLC)
            ###
            elif input_msg.msg_type == msg_type.PutAck:
                self.cache.updateState_line(msg_addr, State.I)
            else:
                return type.Error, None
        else:
            return type.Error, None
        return type.Success, gen_msg
    
    
    ################### The Functions should be called at Top Level ###################
    # for getting response from LLC and CPU
    def receieve_rep_msg(self, msg):
        self.rep_msg_box.enqueue(msg)
        return True
    
    # for getting request from LLC and CPU
    def receieve_req_msg(self, msg):
        self.req_msg_box.enqueue(msg)
        return True
        
    def get_generated_msg(self):
        if self.generated_msg_queue.is_empty():
            return None
        else:
            return self.generated_msg_queue.peek()
    
    def take_generated_msg(self):
        assert self.generated_msg_queue.is_empty() == False, "Error! Can not take msg out from CPU generated msg queue"
        self.generated_msg_queue.dequeue()
        
    # receiece barrier info from top, call one time if One Node send a barrier before CPU execution in the same cycle
    def update_barrier(self, barrier_name):
        if barrier_name != None:
            barrier_num = self.barrier_map.search(barrier_name)
            print(barrier_num)
            self.barrier_map.change(barrier_name, barrier_num-1)
                
    def get_barrier(self):
        temp = self.barrier_name_observed
        self.barrier_name_observed = None
        return temp;
    
    def is_finish(self):
        return self.finish

    def CPU_run(self):
        print()
        print(f"#################### CPU {self.Node} Run at Clk Cnt {self.clk_cnt} ####################")
        generated_queue_empty = self.generated_msg_queue.is_empty()
        # First execute response
        rep_msg = self.get_new_rep()
        self.current_rep_msg = rep_msg
        if rep_msg != None:
            assert rep_msg.msg_type == msg_type.DataDir or rep_msg.msg_type == msg_type.DataOwner or rep_msg.msg_type == msg_type.PutAck , f"Error! CPU response box has wrong msg_type {rep_msg.msg_type}"
            if (rep_msg.msg_type == msg_type.DataDir or rep_msg.msg_type == msg_type.DataOwner):
                assert rep_msg.addr == self.current_inst.addr, "Error! CPU receieve a request which do not have match addr"

            current_state = self.get_current_state(rep_msg)
            result, gen_msg = self.do_transition(current_state, rep_msg)
            assert result != type.Error, "Error! CPU wrong when take rep msg"
            if gen_msg != None:
                if generated_queue_empty == True:
                    self.generated_msg_queue.enqueue(gen_msg)
                else:
                    self.generated_msg_queue.enqueue_front(gen_msg)
            self.cache.renewAccess(rep_msg.addr)
        
        # Second execute req
        req_msg = self.get_new_req()
        self.current_req_msg = req_msg
        if req_msg != None:
            current_state = self.get_current_state(req_msg)
            result, gen_msg = self.do_transition(current_state, req_msg)
            print(req_msg.addr)
            assert result != type.Error, f"Error! CPU wrong when taking request"
            if result == type.Success:
                assert gen_msg != None, "Error! CPU do not generate msg after execute a request"
                if generated_queue_empty == True:
                    self.generated_msg_queue.enqueue(gen_msg)
                else:
                    self.generated_msg_queue.enqueue_front(gen_msg)
                self.take_new_req()
                self.cache.renewAccess(req_msg.addr)
        
        # Third execute an instruction
        # 1. always wait if Load or Store is success and cache miss
        # 2. wait if can not do valid evict
        # 2. wait for Barrier
        if self.wait == True:
            if self.current_inst.inst_type == Inst_type.Barrier: # should not continue
                current_barrier_num = self.barrier_map.search(self.barrier_name)
                if current_barrier_num == 0: # mean this barrier is resolved, will execute next instruction in next cycle
                    self.wait = False
                return 0
            elif self.current_inst.inst_type == Inst_type.Load or self.current_inst.inst_type == Inst_type.Store:
                if rep_msg != None: # CPU wait if there is no rep on current Load or Store instruction
                    assert self.is_inst_qualified(rep_msg.addr), "Error! CPU receieve a response and not transfer to State State"
                    if rep_msg.msg_type != msg_type.PutAck: # because PutAck means current inst is blocked because invalid eviction, should retry
                        self.inst_buffer.dequeue()
                    self.wait = False
                else: # should continue stall
                    return 0
        
        # assert self.generated_msg == None, "Error! CPU generate new message when execute response"

        inst = self.get_new_inst()
        if inst == None:
            self.empty = True
            print("CPU finish execution")
            return 0
        self.current_inst = inst
        if inst.inst_type == Inst_type.Load:
            inst_msg = Msg(msg_type.Load, inst.addr, self.Node, self.Node, 0, Node.NULL)
            current_state = self.get_current_state(inst_msg)
            load_result, gen_msg = self.do_transition(current_state, inst_msg)
            assert load_result != type.Error, "Error! CPU wrong when execute Load instruction"
             # this load instruction can not proceed in this cycle
            if load_result == type.Block:
                self.wait = True
                
            elif load_result == type.Success:
                if gen_msg != None: # else mean hit
                    self.wait = True
                    self.generated_msg_queue.enqueue(gen_msg)
                else:
                    assert self.wait == False, "Error! CPU should not wait on Load hit"
                self.cache.renewAccess(inst_msg.addr)

        elif inst.inst_type == Inst_type.Store:
            inst_msg = Msg(msg_type.Store, inst.addr, self.Node, self.Node, 0, Node.NULL)
            current_state = self.get_current_state(inst_msg)
            store_result, gen_msg = self.do_transition(current_state, inst_msg)
            assert store_result != type.Error, "Error! CPU wrong when execute Load instruction"
            # this Store instruction can not proceed in this cycle
            if store_result == type.Block:
                self.wait = True
                
            elif store_result == type.Success:
                if gen_msg != None:
                    self.wait = True # else mean hit
                    self.generated_msg_queue.enqueue(gen_msg)
                else:
                    assert self.wait == False, "Error! CPU should not wait on Store hit"
                self.cache.renewAccess(inst_msg.addr)
            
        elif inst.inst_type == Inst_type.Barrier:
            print("BARRIER UPDATE")
            self.update_barrier(inst.barrier_name)
            if self.barrier_map.search(inst.barrier_name) != 0:
                self.barrier_name = inst.barrier_name
                self.wait = True
            else: # this barrier instruction has already be poped by update_barrier()
                self.wait  = False
            self.barrier_name_observed = inst.barrier_name
            return 0


    ## this function should take the response from Top, have to follow CPU_RUN() and *** have already taken generated msg ***
    #  deal with whether the previous generated msg can be taken by LLC
    def CPU_POST_RUN(self):
        self.finish = self.inst_empty and self.req_msg_box.is_empty() and  self.rep_msg_box.is_empty()
        if self.finish == True:
            return 0
        if self.wait == False:
            self.inst_buffer.dequeue()
        # if self.generated_msg_queue.is_empty() == False and self.wait == False:
        #     assert self.generated_msg_queue.size() == 1, "Error! CPU has more then one not taken generated request"
        #     self.wait = True
        self.clk_cnt = self.clk_cnt + 1
