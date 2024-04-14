import math
from enum import Enum, auto
import random
from collections import deque
from gpu_utility import *



class GPU_Controller:

    def __init__(self, cache_size, ways, line_size, memory_size, req_box_size, res_box_size):
        self.cache      = GPU_cache(cache_size, ways, line_size, memory_size)
        self.req_msg_box    =  MessageBuffer(req_box_size)
        self.res_msg_box    =  MessageBuffer(res_box_size)

    # for getting new request from another node
    def receieve_req_msg(self, msg_type, addr, src, dst, ackCnt, word_num):
        msg(msg_type, addr, src, dst, ackCnt, word_num)
        if self.req_msg_box.isfull():
            return False
        else:
            self.req_msg_box.enqueue(msg)
            return True

    def get_new_req(self):
        if self.req_msg_box.is_empty():
            return False
        else:
            msg = self.req_msg_box.dequeue(self)
            return msg

    # for getting new response from another node
    def receieve_res_msg(self, msg_type, addr, src, dst, ackCnt, word_num):
        msg(msg_type, addr, src, dst, ackCnt, word_num)
        if self.res_msg_box.isfull():
            return False
        else:
            self.re_msg_box.enqueue(msg)
            return True

    def get_new_res(self):
        if self.res_msg_box.is_empty():
            return False
        else:
            msg = self.res_msg_box.dequeue(self)
            return msg

    def get_state(msg):
        return 0
        
    def do_transition(self, current_state, input_msg):
        