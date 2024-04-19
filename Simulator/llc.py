from enum import Enum, auto
import random
from collections import deque
from llc_utility import *
from global_utility import *
from llc import *


## for request there is always an time stamp
class LLC_Controller:

    def __init__(self, cache_size, ways, line_size, memory_size, req_box_size, min_delay, max_delay, mem_delay):
        self.cache      = dir_cache(cache_size, ways, line_size, memory_size)
        self.req_msg_box    =  MessageBuffer(req_box_size) # the request to LLC
        self.generated_msg_queue = Queue() # queue for msg generated after LLC has processed one msg, it should be dequeued if msg has been taken out from queue
        self.mem_req_queue = Queue()
        self.rep_msg_box   = Queue() # only get reply msg, InvAck RepRvkO MemRep
        self.min_delay      = min_delay
        self.max_delay      = max_delay
        self.mem_delay      = mem_delay
        self.prev_req_blocked = None # the req which is blocked last cycle should not be active in next cycle
        self.current_rep_msg = None
        self.current_mem_msg = None
        self.current_req_msg = None
        self.clk_cnt = 0
        self.inv_cnt = 0

    ###### come from Request queue
    ## return a list of elemenr which has timestamp + max_delay < current_time_stamp
    
    ## llc can not taken a new request if there is a pending request on this addr
    ## if cache do not has this line, will getState_line() will return State.I
    ##  whether eviction can be happen will be handle by is_evict_valid()
    def is_req_qualify(self, addr):
        state = self.cache.getState_line(addr)
        #print(state)
        if state == State.I or state == State.O or state == State.V or state == State.S or state == State.VI:
            return True
        else:
            return False
    
    ## qualified request : time stamp longer than min delay, can not target on addr with pending request
    def get_qualify_req(self, req_list):
        qualified_list = []
        for msg in req_list:
            # print(msg.time_stamp + self.min_delay, self.clk_cnt)
            if (msg.time_stamp + self.min_delay) < self.clk_cnt:
                if self.is_req_qualify(msg.msg.addr) or msg.msg.msg_type == msg_type.ReqWB or msg.msg.msg_type == msg_type.ReqWT:
                    if msg != self.prev_req_blocked:
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
        if len(qualified_list) != 0:
            selected_element = random.choice(qualified_list)
            return selected_element
        return None

    def get_new_req(self):
        if self.req_msg_box.is_empty():
            return None
        else:
            new_req = self.pick(self.req_msg_box.get_content())
            return new_req


    ###### come from Response Queue

    def get_new_rep(self):
        if self.rep_msg_box.is_empty():
            return None
        else:
            msg = self.rep_msg_box.dequeue()
            return msg

    ###### get mem response form Memory Queue
    def get_mem_msg(self):
        if self.mem_req_queue.is_empty():
            return None
        msg = self.mem_req_queue.peek()
        msg.msg_type = msg_type.MemRep
        if msg.ack_cnt == self.clk_cnt:
            self.mem_req_queue.dequeue()
            return msg
        else:
            return None

    ## put State.I on evict addr, and put new address in cache
    def cache_replace(self, new_addr):
        evict_addr, evict_line_state, evict_word_state, evict_sharer, evict_owner= self.cache.getLRU(new_addr)
        self.cache.updateState_line_word(evict_addr, State.I)
        self.cache.addNewLine(new_addr)
        self.cache.renewAccess(new_addr)

    # return True represent to not need to send Inv to other node, evict can proceed
    # return False represent that evict not complete, need to go to transient state
    def cache_evict(self, addr):
        evict_addr, evict_line_state, evict_word_state, evict_sharer, evict_owner= self.cache.getLRU(addr)
        if evict_line_state == State.S:
            sharer = self.cache.get_sharer(evict_addr)
            for dst in sharer:
                msg = Msg(msg_type.Inv, evict_addr, Node.LLC, dst, 0, Node.NULL, addr)
                self.generated_msg_queue.enqueue(msg)
            self.cache_replace(addr)
            self.inv_cnt = len(sharer)
            return False
        # elif evict_line_state == State.O:
        #     msg = Msg(msg_type.Inv, evict_addr, Node.LLC, self.cache.getOwner(addr), 0, Node.NULL, addr)
        #     self.generated_msg_queue.enqueue(msg)
        #     self.cache_replace(addr)
        #     self.inv_cnt = 1
        #     return False
        elif evict_line_state == State.O:
            self.cache.updateState_line_word(evict_addr, State.I)
            self.cache.updateState_line(evict_addr, State.OV)
            # self.cache.updateState_line_word(evict_addr, State.OV)
            self.cache.updateMsgDst(evict_addr, Node.LLC)
            msg = Msg(msg_type.FwdReqV_E, evict_addr, Node.LLC, self.cache.getOwner(addr), 0, Node.LLC)
            self.generated_msg_queue.enqueue(msg)
            return type.Block
        elif evict_line_state == State.V:
            self.cache_replace(addr)
            return True
        elif evict_line_state == State.VI:
            self.cache_replace(addr)
            return True
        elif evict_line_state == State.I:
            self.cache_replace(addr)
            return True
    
    # evict can only happen when is_evict_valid return true
    def is_evict_valid(self, addr):
        evict_addr, evict_line_state, evict_word_state, evict_sharer, evict_owner= self.cache.getLRU(addr)
        print(evict_addr)
        if self.is_req_qualify(evict_addr):
            return True
        else:
            return False

    # if there is empty way, directly put addr into cache
    # if there is no empty way, first set evict addr to State.I and then put addr into cache
    def add_new_line(self, addr):
        if self.cache.addNewLine(addr) == True:
            print(addr)
            self.cache.renewAccess(addr)
            return True
        else:
            if self.is_evict_valid(addr) == False:
                return type.Block
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
            mem_msg = Msg(msg_type.MemReq, msg_addr, Node.LLC, Node.MEM, self.clk_cnt + self.mem_delay, Node.NULL)
            ###
            if input_msg.msg_type == msg_type.ReqV:
                add_cache_result = self.add_new_line(msg_addr)
                if add_cache_result == False:
                    self.cache.updateState_line(msg_addr, State.I_I_V)
                    self.cache.updateMsgDst(msg_addr, msg_src)
                elif add_cache_result == True:
                    self.cache.updateState_line_word(msg_addr, State.IV)
                    self.mem_req_queue.enqueue(mem_msg)
                    self.cache.updateMsgDst(msg_addr, msg_src)
                elif add_cache_result == type.Block: # can not proceed with the replacement
                    return type.Block
            ###
            elif input_msg.msg_type == msg_type.ReqS:
                add_cache_result = self.add_new_line(msg_addr)
                if add_cache_result == False:
                    self.cache.updateState_line(msg_addr, State.I_I_S)
                    self.cache.updateMsgDst(msg_addr, msg_src)
                elif add_cache_result == True:
                    self.cache.updateState_line_word(msg_addr, State.IS)
                    self.mem_req_queue.enqueue(mem_msg)
                    self.cache.updateMsgDst(msg_addr, msg_src)
                elif add_cache_result == type.Block:
                    return type.Block
            ###
            elif input_msg.msg_type == msg_type.ReqWT:
                add_cache_result = self.add_new_line(msg_addr)
                if add_cache_result == False:
                    self.cache.updateState_line(msg_addr, State.I_I_VI)
                    self.cache.updateMsgDst(msg_addr, msg_src)
                elif add_cache_result == True:
                    self.cache.updateState_line(msg_addr, State.VI)
                    self.cache.updateState_word(msg_addr, State.V)
                    self.cache.updateOwner(msg_src, Node.LLC)
                    msg = Msg(msg_type.RepWT, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                    self.generated_msg_queue.enqueue(msg)
                elif add_cache_result == type.Block:
                    return type.Block
            ###
            elif input_msg.msg_type == msg_type.ReqOdata:
                add_cache_result = self.add_new_line(msg_addr)
                if add_cache_result == False:
                    self.cache.updateState_line(msg_addr, State.I_I_O)
                    self.cache.updateMsgDst(msg_addr, msg_src)
                elif add_cache_result == True:
                    self.cache.updateState_line_word(msg_addr, State.IO)
                    self.mem_req_queue.enqueue(mem_msg)
                    self.cache.updateMsgDst(msg_addr, msg_src)
                elif add_cache_result == type.Block:
                    return type.Block
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.InvAck:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.MemReq:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
        
        ###########################################################
        elif current_state == State.I_I_V:
            ###
            if input_msg.msg_type == msg_type.ReqWT:
                self.cache.updateState_word(msg_addr, State.V)
                msg = Msg(msg_type.RepWT, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.InvAck:
                self.inv_cnt = self.inv_cnt - 1
                if self.inv_cnt == 0:
                    mem_msg = Msg(msg_type.MemReq, msg_addr, Node.LLC, Node.MEM, self.clk_cnt + self.mem_delay, Node.NULL)
                    self.mem_req_queue.enqueue(mem_msg)
                    self.cache.updateState_line_word(msg_addr, State.IV)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemReq:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.I_I_S:
            ###
            if input_msg.msg_type == msg_type.InvAck:
                self.inv_cnt = self.inv_cnt - 1
                if self.inv_cnt == 0:
                    mem_msg = Msg(msg_type.MemReq, msg_addr, Node.LLC, Node.MEM, self.clk_cnt + self.mem_delay, Node.NULL)
                    self.mem_req_queue.enqueue(mem_msg)
                    self.cache.updateState_line_word(msg_addr, State.IS)
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemReq:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
        
        ###########################################################
        elif current_state == State.I_I_O:
            ###
            if input_msg.msg_type == msg_type.InvAck:
                self.inv_cnt = self.inv_cnt - 1
                if self.inv_cnt == 0:
                    mem_msg = Msg(msg_type.MemReq, msg_addr, Node.LLC, Node.MEM, self.clk_cnt + self.mem_delay, Node.NULL)
                    self.mem_req_queue.enqueue(mem_msg)
                    self.cache.updateState_line_word(msg_addr, State.IO)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemReq:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
        
        ###########################################################
        elif current_state == State.I_I_VI:
            ###
            if input_msg.msg_type == msg_type.InvAck:
                self.inv_cnt = self.inv_cnt - 1
                if self.inv_cnt == 0:
                    dst = self.cache.getMsgDst(msg_addr)
                    msg = Msg(msg_type.RepWT, msg_addr, Node.LLC, dst, 0, Node.NULL)
                    self.generated_msg_queue.enqueue(msg)
                    self.cache.updateState_line_word(msg_addr, State.VI)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemReq:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.V:
            ###
            if input_msg.msg_type == msg_type.ReqV:
                msg = Msg(msg_type.RepV, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqS:
                self.cache.updateState_line_word(msg_addr, State.S)
                msg = Msg(msg_type.RepS, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
                self.cache.clear_sharer(msg_addr)
                self.cache.add_sharer(msg_addr, msg_src) # can only be cpu
            ###
            elif input_msg.msg_type == msg_type.ReqWT:
                self.cache.updateState_word(msg_addr, State.V)
                msg = Msg(msg_type.RepWT, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqOdata:
                self.cache.updateState_line_word(msg_addr, State.O)
                msg = Msg(msg_type.RepOdata, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemReq:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.S:
            ###
            if input_msg.msg_type == msg_type.ReqV:
                msg = Msg(msg_type.RepV, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqS:
                msg = Msg(msg_type.RepS, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
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
                    msg = Msg(msg_type.Inv, msg_addr, Node.LLC, dst, 0, Node.NULL)
                    self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqOdata:
                self.cache.updateState_line_word(msg_addr, State.SO)
                self.cache.updateMsgDst(msg_addr, msg_src)
                sharer = self.cache.get_sharer(msg_addr)
                self.inv_cnt = len(sharer)
                self.cache.clear_sharer(msg_addr)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemReq:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.O:
            ###
            if input_msg.msg_type == msg_type.ReqV:
                self.cache.updateState_line_word(msg_addr, State.OS)
                # self.cache.updateState_line(msg_addr, State.OV)
                self.cache.updateMsgDst(msg_addr, msg_src)
                msg = Msg(msg_type.FwdReqV, msg_addr, Node.LLC, owner, 0, msg_src)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqS:
                self.cache.updateState_line_word(msg_addr, State.OS)
                msg = Msg(msg_type.FwdReqS, msg_addr, Node.LLC, owner, 0, Node.NULL)
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
                msg = Msg(msg_type.FwdRvkO, msg_addr, Node.LLC, owner, 0, Node.LLC) # Remote O should forward data to LLC
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqOdata:
                msg = Msg(msg_type.FwdReqOdata, msg_addr, Node.LLC, owner, 0, msg_src)
                self.generated_msg_queue.enqueue(msg)
                self.cache.updateOwner(msg_addr, msg_src)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    self.cache.updateState_line_word(msg_addr, State.V)
                    self.cache.updateOwner(msg_addr, Node.LLC)
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemReq:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.VI:
            mem_msg = Msg(msg_type.MemReq, msg_addr, Node.LLC, Node.MEM, self.clk_cnt + self.mem_delay, Node.NULL)
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
                    word_state = self.cache.getState_allword(msg_addr)
                    to_V = True
                    for state in word_state:
                        if state != State.V:
                            to_V = False
                    if to_V == True:
                        self.updateState_line(msg_addr, State.V)
                    msg = Msg(msg_type.RepWT, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                    self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqOdata:
                self.cache.updateState_line_word(msg_addr, State.VI_O)
                self.mem_req_queue.enqueue(mem_msg)
                self.cache.updateMsgDst(msg_addr, msg_src)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemReq:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
        
        ###########################################################
        elif current_state == State.IV:
            ###
            if input_msg.msg_type == msg_type.ReqWT:
                    self.cache.updateState_word(msg_addr, State.V)
                    msg = Msg(msg_type.RepWT, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                    self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemRep:
                self.cache.updateState_line_word(msg_addr, State.V)
                self.cache.updateOwner(msg_addr, Node.LLC)
                msg = Msg(msg_type.RepV, msg_addr, Node.LLC, self.cache.getMsgDst(msg_addr), 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
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
                msg = Msg(msg_type.RepS, msg_addr, Node.LLC, msg_dst, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.IO:
            ###
            if input_msg.msg_type == msg_type.MemRep:
                msg_dst = self.cache.getMsgDst(msg_addr)
                self.cache.updateState_line_word(msg_addr, State.O)
                self.cache.updateOwner(msg_addr, msg_dst)
                msg = Msg(msg_type.RepOdata, msg_addr, Node.LLC, msg_dst, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.SO:
            ###
            if input_msg.msg_type == msg_type.InvAck:
                self.inv_cnt = self.inv_cnt - 1
                if self.inv_cnt == 0:
                    msg = Msg(msg_type.RepOdata, msg_addr, Node.LLC, self.cache.getMsgDst(msg_addr), 0 , Node.NULL)
                    self.cache.updateOwner(msg_addr, self.cache.getMsgDst(msg_addr))
                    self.generated_msg_queue.enqueue(msg)
                    self.cache.updateState_line_word(msg_addr, State.O)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemReq:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.SV:
            ###
            if input_msg.msg_type == msg_type.InvAck:
                self.inv_cnt = self.inv_cnt - 1
                if self.inv_cnt == 0:
                    msg = Msg(msg_type.RepWT, msg_addr, Node.LLC, self.cache.getMsgDst(msg_addr), 0 , Node.NULL)
                    self.generated_msg_queue.enqueue(msg)
                    self.cache.updateState_line_word(msg_addr, State.V)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemReq:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
        
        ###########################################################
        elif current_state == State.OS:
            ###
            if input_msg.msg_type == msg_type.RepRvkO:
                msg = Msg(msg_type.RepS, msg_addr, Node.LLC, self.cache.getMsgDst(msg_addr), 0 , Node.NULL)
                self.generated_msg_queue.enqueue(msg)
                self.cache.updateState_line_word(msg_addr, State.S)
                self.cache.updateOwner(msg_src, Node.LLC)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Block
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                self.cache.updateState_line_word(msg_addr, State.S)
                msg = Msg(msg_type.RepV, msg_addr, Node.LLC, self.cache.getMsgDst(msg_addr), 0 , Node.NULL)
                self.generated_msg_queue.enqueue(msg)
                self.cache.updateOwner(msg_addr, Node.LLC)
            ###
            elif input_msg.msg_type == msg_type.MemReq:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.OV:
            ###
            if input_msg.msg_type == msg_type.RepRvkO:
                msg = Msg(msg_type.RepWT, msg_addr, Node.LLC, self.cache.getMsgDst(msg_addr), 0 , Node.NULL)
                self.generated_msg_queue.enqueue(msg)
                self.cache.updateState_line_word(msg_addr, State.V)
                self.cache.updateOwner(msg_src, Node.LLC)
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E: # only for cache eviction situation
                self.cache.updateState_line_word(msg_addr, State.V)
                self.cache.updateOwner(msg_addr, Node.LLC)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Block
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemReq:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            else:
                return type.Block
        
        ###########################################################
        elif current_state == State.VI_S:
            ###
            if input_msg.msg_type == msg_type.ReqWT:
                msg = Msg(msg_type.RepWT, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemRep:
                self.cache.updateState_line_word(msg_addr, State.S)
                self.cache.clear_sharer(msg_addr)
                msg_dst = self.cache.getMsgDst(msg_addr)
                self.cache.add_sharer(msg_addr, msg_dst)
                msg = Msg(msg_type.RepS, msg_addr, Node.LLC, msg_dst, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
            
        ###########################################################
        elif current_state == State.VI_O:
            ###
            if input_msg.msg_type == msg_type.ReqWT:
                msg = Msg(msg_type.RepWT, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.MemRep:
                self.cache.updateState_line_word(msg_addr, State.O)
                msg_dst = self.cache.getMsgDst(msg_addr)
                self.cache.updateOwner(msg_addr, msg_dst)
                msg = Msg(msg_type.RepOdata, msg_addr, Node.LLC, msg_dst, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.ReqWB:
                if msg_src == owner:
                    return type.Error
                msg = Msg(msg_type.RepWB, msg_addr, Node.LLC, msg_src, 0, Node.NULL)
                self.generated_msg_queue.enqueue(msg)
            ###
            elif input_msg.msg_type == msg_type.RepRvkO:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV:
                return type.Error
            ###
            elif input_msg.msg_type == msg_type.RepFwdV_E:
                return type.Error
            else:
                return type.Block
        
        ##########################################################
        else:
            print(f"Error! there is unexpected state in state transaction{current_state}")

        return type.Success

    ################### The Functions should be called at Top Level ###################
    
    # should be called when another Node has generated_msg to LLC
    def receieve_rep_msg(self, msg):
        # msg = Msg(msg_type, addr, src, dst, ackcnt, fwd_dst)
        self.rep_msg_box.enqueue(msg)
    
    # for getting new request from another node
    def receieve_req_msg(self, msg):
        req_msg = req_msg(msg.msg_type, msg.addr, msg.src, msg.dst, msg.ackcnt, msg.fwd_dst, self.clk_cnt)
        if self.req_msg_box.is_full():
            return False
        else:
            self.req_msg_box.enqueue(req_msg)
            return True
    
    def get_generated_msg(self):
        if self.generated_msg_queue.is_empty():
            return None
        else:
            return self.generated_msg_queue.peek()
        
    def take_generated_msg(self):
        assert self.generated_msg_queue.is_empty() == False, "Error! Can not take instruction out from LLC generated msg queue"
        self.generated_msg_queue.dequeue()
    
    def LLC_run(self):
        print(f"#################### LLC Run at Clk Cnt {self.clk_cnt} ####################")
        ## first handle one response from req_msg_box
        rep_msg = self.get_new_rep()
        self.current_rep_msg = rep_msg
        if rep_msg != None:
            assert rep_msg.msg_type == msg_type.InvAck  or rep_msg.msg_type == msg_type.RepRvkO or rep_msg.msg_type == msg_type.RepFwdV or rep_msg.msg_type == msg_type.RepFwdV_E, "LLC response box has wrong msg_type"
            current_state, owner = self.get_current_state(rep_msg)
            result = self.do_transition(current_state, rep_msg, owner)
            print(current_state)
            rep_msg.print_msg()
            assert result != type.Error, "Error! LLC have error when to execute response"
            
            
        ## second handle one response from mem_msg_queue
        mem_msg = self.get_mem_msg()
        self.current_mem_msg = mem_msg
        if mem_msg != None:
            #mem_msg.print_msg()
            assert mem_msg.msg_type == msg_type.MemRep, "LLC mem box has wrong msg_type"
            current_state, owner = self.get_current_state(mem_msg)
            result = self.do_transition(current_state, mem_msg, owner)
            assert result != type.Error, "Error! LLC have error when to execute mem"
            
        ## third randomly picking one message from req_msg_box, and handle request from outside
        req_msg = self.get_new_req()
        self.current_req_msg = req_msg
        if req_msg != None:
            #req_msg.print_msg()
            current_state, owner = self.get_current_state(req_msg.msg)
            result = self.do_transition(current_state, req_msg.msg, owner)
            if result == type.Success:
                self.req_msg_box.remove(req_msg)
                assert self.cache.getState_line(req_msg.msg.addr) != State.I, "Error! LLC cache do not has this cache line when update LRU"
                self.cache.renewAccess(req_msg.msg.addr)
                self.prev_req_blocked = None
            elif result == type.Block:
                self.prev_req_blocked = req_msg
            else:
                assert result != type.Error, "Error! LLC have error when to execute request"
        
        ## clk_cnt ++
        self.clk_cnt = self.clk_cnt + 1