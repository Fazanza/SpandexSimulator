from enum import Enum, auto
import random
from collections import deque
from llc_utility import *
from llc import *


## for request there is always an time stamp
class LLC_Controller:

    offset = 0
    generated_msg_queue = Queue() # queue for msg generated after LLC has processed one msg, it should be dequeued if msg has been taken out from queue
    mem_req_queue = Queue()
    rep_msg_box   = Queue() # only get reply msg
    inv_cnt = 0
    clk_cnt = 0


    def __init__(self, cache_size, ways, line_size, memory_size, req_box_size, min_delay, max_delay, mem_delay):
        self.cache      = dir_cache(cache_size, ways, line_size, memory_size)
        self.req_msg_box    =  MessageBuffer(req_box_size) # the request to LLC
        self.min_delay      = min_delay
        self.max_delay      = max_delay
        self.mem_delay      = mem_delay

    ###### come from Request queue
    ## return a list of elemenr which has timestamp + max_delay < current_time_stamp
    
    ## llc can not taken a new request if there is a pending request on this addr
    def is_req_qualify(self, addr):
        state = self.cache.getState_line(addr)
        if state == State.I or state == State.O or state == State.V or state == State.S or state == State.VI:
            return True
        else:
            return False
    
    ## qualified request : time stamp longer than min delay, can not target on addr with pending request
    def get_qualify_req(self, req_list):
        qualified_list = []
        for msg in req_list:
            if (msg.time_stamp + self.min_delay) < self.clk_cnt:
                if self.is_req_qualify(msg.addr):
                    qualified_list.append(msg)
        return qualified_list
    
    def find_latest_element(self, qualified_list):
        temp = []
        latest = None
        for item in qualified_list:
            if item.time_stamp + self.max_delay < self.clk_cnt:
                temp.append(item)
        for item in temp:
            if latest == None:
                latest = item
            elif latest.time_stamp < item.time_stamp:
                latest = item
        return latest

    def pick(self, req_list):
        qualified_list = self.get_qualify_req(req_list)
        selected_element = self.find_latest_element(qualified_list)
        if selected_element!= None:
            return selected_element
        if len(self.qualified_list) != 0:
            selected_element = random.choice(qualified_list)
            return selected_element
        return None
    
    # for getting new request from another node
    def receieve_req_msg(self, msg_type, addr, src, dst, ackcnt, fwd_dst):
        msg = req_msg(msg_type, addr, src, dst, ackcnt, fwd_dst, self.clk_cnt)
        if self.req_msg_box.isfull():
            return False
        else:
            self.req_msg_box.enqueue(msg)
            return True

    def get_new_req(self):
        if self.req_msg_box.is_empty():
            return None
        else:
            new_req = self.pick(self.req_msg_box.get_content())
            return new_req


    ###### come from Response Queue
    # receieve invalidate ackowledge from other node
    def receieve_rep_msg(self, msg_type, addr, src, dst, ackcnt, fwd_dst):
        msg = msg(msg_type, addr, src, dst, ackcnt, fwd_dst)
        self.rep_msg_box.enqueue(msg)

    def get_new_rep(self):
        if self.rep_msg_box.is_empty():
            return None
        else:
            msg = self.rep_msg_box.dequeue()
            return msg

    ###### get mem response form Memory Queue
    def get_mem_msg(self):
        msg = self.mem_req_queue.peek()
        if msg.ack_cnt == self.clk_cnt:
            self.mem_req_queue.dequeue()
            return msg
        else:
            return None

    def pop_generated_msg_queue(self):
        if not self.generated_msg_queue.is_empty():
            self.generated_msg_queue.dequeue()


    ## put State.I on evict addr, and put new address in cache
    def cache_replace(self, new_addr):
        evict_addr, evict_line_state, evict_word_state, evict_sharer, evict_owner= self.cache.getLRU(new_addr)
        self.cache.updateState_line_word(self, evict_addr, State.I)
        self.cache.addNewLine(self, new_addr)
        self.cache.renewAccess(new_addr)

    # return True represent to not need to send Inv to other node, evict can proceed
    # return False represent that evict not complete, need to go to transient state
    def cache_evict(self, addr):
        evict_addr, evict_line_state, evict_word_state, evict_sharer, evict_owner= self.cache.getLRU(addr)
        if evict_line_state == State.S:
            sharer = self.cache.get_sharer()
            for dst in sharer:
                msg = msg(msg_type.Inv, addr, Node.LLC, dst, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            self.cache_replace(addr)
            self.inv_cnt = len(sharer)
            return False
        elif evict_line_state == State.O:
            msg = msg(msg_type.Inv, addr, Node.LLC, self.cache.getOwner(addr), 0, Node.NULL)
            self.generated_msg_queue.enqueue(msg)
            self.cache_replace(addr)
            self.inv_cnt = 1
            return False
        elif evict_line_state == State.V:
            self.cache_replace(addr)
            return True
        elif evict_line_state == State.VI:
            self.cache_replace(addr)
            return True
        elif evict_line_state == State.I:
            self.cache_replace(addr)
            return True

    # if there is empty way, directly put addr into cache
    # if there is no empty way, first set evict addr to State.I and then put addr into cache
    def add_new_line(self, addr):
        if self.cache.addNewLine(addr) == True:
            self.cache.renewAccess(addr)
            return True
        else:
            return self.cache_evict(addr)
        
    def get_current_state(self, input_msg):
        line_state = self.cache.getState_line(input_msg.addr)
        owner = self.cache.getOwner(input_msg.addr)
        return line_state, owner


    # do state transition and generate reponse and send to generated_msg_queue
    def do_transition(self, current_state, input_msg, old_owner):
        self.generated_msg_queue.clear()
        msg_src = input_msg.src
        msg_addr = input_msg.addr
        owner = old_owner
        
        ###########################################################
        if current_state == State.I:
            mem_msg = msg(msg_type.MemReq, msg_addr, Node.LLC, Node.MEM, self.clk_cnt + self.mem_delay, Node.NULL)
            ###
            if input_msg.msg_type == msg_type.ReqV:
                if self.add_new_line(msg_addr) == False:
                    self.cache.updateState_line(msg_addr, State.I_I_V)
                else:
                    self.cache.updateState_line_word(msg_addr, State.IV)
                    self.mem_req_queue.enqueue(mem_msg)
                self.cache.updateMsgDst(msg_addr, msg_src)
            ###
            elif input_msg.msg_type == msg_type.ReqS:
                if self.add_new_line(msg_addr) == False:
                    self.cache.updateState_line(msg_addr, State.I_I_S)
                else:
                    self.cache.updateState_line_word(msg_addr, State.IS)
                    self.mem_req_queue.enqueue(mem_msg)
                self.cache.updateMsgDst(msg_addr, msg_src)
            ###
            elif input.msg.msg_type == msg_type.ReqWT:
                if self.add_new_line(msg_addr) == False:
                    self.cache.updateState_line(msg_addr, State.I_I_VI)
                else:
                    self.cache.updateState_line(msg_addr, State.VI)
                    self.cache.updateState_word(msg_addr, State.V)
                    self.cache.updateOwner(msg_src, Node.LLC)
                    msg = msg(msg_type.RepWT, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                    self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqOdata:
                if self.add_new_line(msg_addr) == False:
                    self.cache.updateState_line(msg_addr, State.I_I_O)
                else:
                    self.cache.updateState_line_word(msg_addr, State.IO)
                    self.mem_req_queue.enqueue(mem_msg)
                self.cache.updateMsgDst(msg_addr, msg_src)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
        
        ###########################################################
        elif current_state == State.I_I_V:
            ###
            if input.msg_type == msg_type.ReqWT:
                self.cache.updateState_word(msg_addr, State.V)
                msg = msg(msg_type.RepWT, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input.msg_type == msg_type.InvAck:
                self.inv_cnt = self.inv_cnt - 1
                if self.inv_cnt == 0:
                    mem_msg = msg(msg_type.MemReq, msg_addr, Node.LLC, Node.MEM, self.clk_cnt + self.mem_delay, Node.NULL)
                    self.mem_req_queue.enqueue(mem_msg)
                    self.cache.updateState_line_word(msg_addr, State.IV)
            ###
            elif input.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.I_I_S:
            ###
            if input.msg_type == msg_type.InvAck:
                self.inv_cnt = self.inv_cnt - 1
                if self.inv_cnt == 0:
                    mem_msg = msg(msg_type.MemReq, msg_addr, Node.LLC, Node.MEM, self.clk_cnt + self.mem_delay, Node.NULL)
                    self.mem_req_queue.enqueue(mem_msg)
                    self.cache.updateState_line_word(msg_addr, State.IS)
            ###
            elif input.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
        
        ###########################################################
        elif current_state == State.I_I_O:
            ###
            if input.msg_type == msg_type.InvAck:
                self.inv_cnt = self.inv_cnt - 1
                if self.inv_cnt == 0:
                    mem_msg = msg(msg_type.MemReq, msg_addr, Node.LLC, Node.MEM, self.clk_cnt + self.mem_delay, Node.NULL)
                    self.mem_req_queue.enqueue(mem_msg)
                    self.cache.updateState_line_word(msg_addr, State.IO)
            ###
            elif input.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
        
        ###########################################################
        elif current_state == State.I_I_VI:
            ###
            if input.msg_type == msg_type.InvAck:
                self.inv_cnt = self.inv_cnt - 1
                if self.inv_cnt == 0:
                    mem_msg = msg(msg_type.MemReq, msg_addr, Node.LLC, Node.MEM, self.clk_cnt + self.mem_delay, Node.NULL)
                    self.mem_req_queue.enqueue(mem_msg)
                    self.cache.updateState_line_word(msg_addr, State.VI)
            ###
            elif input.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.V:
            ###
            if input_msg.msg_type == msg_type.ReqV:
                msg = msg(msg_type.RepV, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqS:
                self.cache.updateState_line_word(msg_addr, State.S)
                msg = msg(msg_type.RepS, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
                self.cache.clear_sharer(msg_addr)
                self.cache.add_sharer(msg_addr, msg_src) # can only be cpu
            ###
            elif input_msg.msg_type == msg_type.ReqWT:
                self.cache.updateState_word(msg_addr, State.V)
                msg = msg(msg_type.RepWT, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqOdata:
                self.cache.updateState_line_word(msg_addr, State.O)
                msg = msg(msg_type.RepOdata, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.S:
            ###
            if input_msg.msg_type == msg_type.ReqV:
                msg = msg(msg_type.RepV, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqS:
                msg = msg(msg_type.RepS, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
                self.cache.add_sharer(msg_addr, msg_src) # can only be cpu
            ###
            elif input_msg.msg_type == msg_type.ReqWT:
                self.cache.updateState_line_word(msg_addr, State.I)
                self.cache.updateState_line(msg_addr, State.SV) # line state should be SV
                self.cache.updateState_word(msg_addr, State.V)
                self.cache.updateMsgDst(msg_addr, msg_src)
                sharer = self.cache.get_sharer(msg_addr)
                self.inv_cnt = len(sharer) # wait for enough inv ack to go to V
                self.cache.clear_sharer(msg_addr)
                for dst in sharer:
                    msg = msg(msg_type.Inv, msg_addr, Node.LLC, dst, 0, Node.NULL)
                    self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqOdata:
                self.cache.updateState_line_word(msg_addr, State.SO)
                self.cache.updateMsgDst(msg_addr, msg_src)
                sharer = self.cache.get_sharer(msg_addr)
                self.inv_cnt = len(sharer)
                self.cache.clear_sharer(msg_addr)
            ###
            elif input.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.O:
            ###
            if input_msg.msg_type == msg_type.ReqV:
                msg = msg(msg_type.FwdReqV, msg_addr, Node.LLC, owner, 0, msg_src)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqS:
                self.cache.updateState_line_word(msg_addr, State.OS)
                msg = msg(msg_type.FwdReqS, msg_addr, Node.LLC, owner, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
                self.cache.updateMsgDst(msg_addr, msg_src)
                self.cache.clear_sharer(msg_addr)
                self.cache.add_sharer(msg_addr, owner)
                self.cache.add_sharer(msg_addr, msg_src)
            ###
            elif input_msg.msg_type == msg_type.ReqWT:
                self.cache.updateState_line_word(msg_addr, State.I)
                self.cache.updateState_line(msg_addr, State.OV) # line state should be SV
                self.cache.updateState_word(msg_addr, State.V)
                self.cache.updateMsgDst(msg_addr, msg_src)
                msg = msg(msg_type.FwdRvkO, msg_addr, Node.LLC, owner, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqOdata:
                msg = msg(msg_type.FwdReqOdata, msg_addr, Node.LLC, owner, 0, msg_src)
                self.generated_msg_queue.enqueue(msg)
                self.cache.updateOwner(msg_addr, msg_src)
            ###
            elif input.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    self.cache.updateState_line_word(msg_addr, State.V)
                    self.cache.updateOwner(msg_addr, Node.LLC)
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.VI:
            mem_msg = msg(msg_type.MemReq, msg_addr, Node.LLC, Node.MEM, self.clk_cnt + self.mem_delay, Node.NULL)
            ###
            if input_msg.msg_type == msg_type.ReqV:
                self.cache.updateState_line_word(msg_addr, State.IV)
                self.mem_req_queue.enqueue(mem_msg)
                self.cache.updateMsgDst(msg_addr, msg_src)
            ###
            elif input_msg.msg_type == msg_type.ReqS:
                    self.cache.updateState_line_word(msg_addr, State.VI_S)
                    self.mem_req_queue.enqueue(mem_msg)
                    self.cache.updateMsgDst(msg_addr, msg_src)
            ###
            elif input_msg.msg_type == msg_type.ReqWT:
                    self.cache.updateState_word(msg_addr, State.V)
                    msg = msg(msg_type.RepWT, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                    self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqOdata:
                self.cache.updateState_line_word(msg_addr, State.VI_O)
                self.mem_req_queue.enqueue(mem_msg)
                self.cache.updateMsgDst(msg_addr, msg_src)
            ###
            elif input.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
        
        ###########################################################
        elif current_state == State.IV:
            ###
            if input_msg.msg_type == msg_type.ReqWT:
                    self.cache.updateState_word(msg_addr, State.V)
                    msg = msg(msg_type.RepWT, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                    self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemRep:
                self.cache.updateState_line_word(msg_addr, State.V)
                self.cache.updateOwner(msg_addr, Node.LLC)
                msg = msg(msg_type.RepV, msg_addr, Node.LLC, self.cache.getMsgDst(msg_addr), 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.IS:
            ###
            if input_msg.msg_type == msg_type.MemRep:
                self.cache.updateState_line_word(msg_addr, State.S)
                self.cache.updateOwner(msg_addr, Node.LLC)
                self.cache.clear_sharer(msg_addr)
                msg_dst = self.cache.getMsgDst(msg_addr)
                self.cache.add_sharer(msg_addr, msg_dst)
                msg = msg(msg_type.RepS, msg_addr, Node.LLC, msg_dst, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.IO:
            ###
            if input_msg.msg_type == msg_type.MemRep:
                msg_dst = self.cache.getMsgDst(msg_addr)
                self.cache.updateState_line_word(msg_addr, State.O)
                self.cache.updateOwner(msg_addr, msg_dst)
                msg = msg(msg_type.RepO, msg_addr, Node.LLC, msg_dst, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.SO:
            ###
            if input.msg_type == msg_type.InvAck:
                self.inv_cnt = self.inv_cnt - 1
                if self.inv_cnt == 0:
                    msg = msg(msg_type.RepOdata, msg_addr, Node.LLC, self.cache.getMsgDst(msg_addr), 0 , Node.NULL)
                    self.generated_msg_queue.enqueue(msg)
                    self.cache.updateState_line_word(msg_addr, State.O)
            ###
            elif input.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.SV:
            ###
            if input.msg_type == msg_type.InvAck:
                self.inv_cnt = self.inv_cnt - 1
                if self.inv_cnt == 0:
                    msg = msg(msg_type.RepWT, msg_addr, Node.LLC, self.cache.getMsgDst(msg_addr), 0 , Node.NULL)
                    self.generated_msg_queue.enqueue(msg)
                    self.cache.updateState_line_word(msg_addr, State.V)
            ###
            elif input.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
        
        ###########################################################
        elif current_state == State.OS:
            ###
            if input.msg_type == msg_type.RepRvkO:
                msg = msg(msg_type.RepS, msg_addr, Node.LLC, self.cache.getMsgDst(msg_addr), 0 , Node.NULL)
                self.generated_msg_queue.enqueue(msg)
                self.cache.updateState_line_word(msg_addr, State.S)
                self.cache.updateOwner(msg_src, Node.LLC)
            ###
            elif input.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Block
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.OV:
            ###
            if input.msg_type == msg_type.RepRvkO:
                msg = msg(msg_type.RepWT, msg_addr, Node.LLC, self.cache.getMsgDst(msg_addr), 0 , Node.NULL)
                self.generated_msg_queue.enqueue(msg)
                self.cache.updateState_line_word(msg_addr, State.V)
                self.cache.updateOwner(msg_src, Node.LLC)
            ###
            elif input.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Block
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
        
        ###########################################################
        elif current_state == State.VI_S:
            ###
            if input.msg_type == msg_type.ReqWT:
                msg = msg(msg_type.RepWT, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input.msg_type == msg_type.MemRep:
                self.cache.updateState_line_word(msg_addr, State.S)
                self.cache.clear_sharer(msg_addr)
                msg_dst = self.cache.getMsgDst(msg_addr)
                self.cache.add_sharer(msg_addr, msg_dst)
                msg = msg(msg_type.RepS, msg_addr, Node.LLC, msg_dst, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.VI_O:
            ###
            if input.msg_type == msg_type.ReqWT:
                msg = msg(msg_type.RepWT, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input.msg_type == msg_type.MemRep:
                self.cache.updateState_line_word(msg_addr, State.O)
                msg_dst = self.cache.getMsgDst(msg_addr)
                self.cache.updateOwner(msg_addr, msg_dst)
                msg = msg(msg_type.RepO, msg_addr, Node.LLC, msg_dst, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input.msg_type == msg_type.ReqWB:
                msg = msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            else:
                return type.Block
        
        ##########################################################
        else:
            print(f"Error! there is unexpected state in state transaction{current_state}")

        return type.Success

    def LLC_run(self):
        ## first handle one response from req_msg_box
        rep_msg = self.get_new_rep()
        if rep_msg != None:
            assert rep_msg.msg_type == msg_type.InvAck  or rep_msg.msg_type == msg_type.RepRvkO, "LLC response box has wrong msg_type"
            current_state, owner = self.get_current_state(rep_msg)
            self.do_transition(current_state, rep_msg, owner)
            
            
        ## second handle one response from mem_msg_queue
        mem_msg = self.get_mem_msg
        if mem_msg != None:
            assert mem_msg.msg_type == msg_type.MemRep, "LLC mem box has wrong msg_type"
            current_state, owner = self.get_current_state(mem_msg)
            self.do_transition(current_state, mem_msg, owner)
            
        ## third randomly picking one message from req_msg_box, and handle request from outside
        req_msg = self.get_new_req()
        if req_msg != None:
            current_state, owner = self.get_current_state(req_msg)
            if self.do_transition(current_state, req_msg, owner) == type.Success:
                self.req_msg_box.remove(req_msg)
                self.cache.renewAccess(req_msg.addr)
        
        ## clk_cnt ++
        self.clk_cnt = self.clk_cnt + 1
        return self.generated_msg_queue ## outside should call pop_generated_msg_queue() to pop out the taken msg generated by LLC