import math
from enum import Enum, auto
import random
from collections import deque
from header.llc_header import *
from utility.global_utility import *


class req_msg:
    def __init__(self, msg, time_stamp):
        self.msg = Msg(msg.msg_type, msg.addr, msg.src, msg.dst, msg.ack_cnt, msg.fwd_dst, msg.target_addr)
        self.time_stamp = time_stamp
    
    def print_msg(self):
            if self == None:
                print(None)
            else:
                print(f"msg_type: {self.msg.msg_type}, addr: {self.msg.addr}, time_stamp: {self.time_stamp}, src: {self.msg.src}, dst: {self.msg.dst}, fwd_dst: {self.msg.fwd_dst}, ack_cnt: {self.msg.ack_cnt}")

class MessageBuffer:
    def __init__(self, max_size):
        self.max_size = max_size
        self.buffer = []

    def enqueue(self, message):
        if len(self.buffer) < self.max_size:
            self.buffer.append(message)

    def dequeue(self):
        if self.buffer:
            return self.buffer.pop(0)

    def is_empty(self):
        return len(self.buffer) == 0
    
    def get_content(self):
        return self.buffer
    
    def is_full(self):
        if len(self.buffer) >= self.max_size:
            return True
        else:
            return False
        
    def remove(self, element):
        self.buffer.remove(element)

    def peek(self):
        if not self.is_empty():
            return self.buffer[0]
        else:
            raise IndexError("peek from an empty queue")

    def clear(self):
        self.buffer.clear()

    def size(self):
        return len(self.buffer)

    def print_all(self):
        print("Request message box")
        for item in self.buffer:
            item.print_msg()


class dir_cache:
    cache_size = 0 # number of words in whole cache
    memory_size = 0 # number of words in whole memory
    line_size = 0 # number of words in a line
    ways = 0 # cache way associativity
    total_sets = 0 # number of sets in cache
    line_state = []
    words_state = []
    inv_cnt = 0
    owner = []
    sharer = []
    line_tag = []
    msg_dst = []
    addr_bits = 0
    index_bits = 0
    tag_bits = 0
    offset_bits = 0

    ## cache size = line_size * ways * total_sets
    ## address = [tag, set index, block offset]

    def __init__(self, cache_size, ways, line_size, memory_size):
        self.cache_size = cache_size
        self.ways = ways
        self.line_size = line_size
        self.memory_size = memory_size
        self.total_sets = cache_size//ways//line_size
        self.offset_bits = math.frexp(line_size)[1]-1
        self.addr_bits = math.frexp(memory_size)[1]-1
        self.index_bits = math.frexp(self.total_sets)[1]-1
        self.tag_bits = self.addr_bits - self.index_bits - self.offset_bits
        self.line_state = [[State.I for j in range(self.ways)] for k in range(self.total_sets)]
        self.words_state = [[[State.I for i in range(self.line_size)] for j in range(self.ways)] for k in range(self.total_sets)]
        self.owner = [[Node.MEM for j in range(self.ways)] for k in range(self.total_sets)]
        self.sharer = [[[] for j in range(self.ways)] for k in range(self.total_sets)]
        self.line_tag = [[-1 for j in range(self.ways)] for k in range(self.total_sets)]
        self.msg_dst = [[Node.NULL for j in range(self.ways)] for k in range(self.total_sets)]
        self.inv_cnt = [[0 for j in range(self.ways)] for k in range(self.total_sets)]
    ## Separate address into tag, index and offset
    def parseAddr(self, addr):
        tag = addr >> (self.index_bits + self.offset_bits)
        index = (addr - tag * self.total_sets * self.line_size) >> self.offset_bits
        offset = addr - tag * self.total_sets * self.line_size - index * self.line_size
        return tag, index, offset

    ## search in the set to find matching tag, if no matching tag return -1
    def searchSet(self, index, tag):
        match_way = -1
        for i in range(self.ways):
            if(self.line_tag[index][i] == tag):
                match_way = i
                break
        return match_way

    ## Read a word in the cache, will return the state of the word
    def getState_word(self, addr):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        # miss
        if (match_way == -1):
            return State.I
        else:
            ##updateAccesing
            return self.words_state[index][match_way][offset]
    
    def getState_allword(self, addr):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        # miss
        if (match_way == -1):
            return State.I
        else:
            ##updateAccesing
            return self.words_state[index][match_way]

    def getState_line(self, addr):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        # miss
        if (match_way == -1):
            return State.I
        else:
            ##updateAccesing
            return self.line_state[index][match_way]

    ## Only use when making sure the address is in cache
    def updateState_word(self, addr, new_state):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        ## only use updateState when the line exist in cache
        assert match_way != -1, "Error! LLC line miss in cache during updating word state"
        self.words_state[index][match_way][offset] = new_state

    def updateState_line(self, addr, new_state):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        ## only use updateState when the line exist in cache
        assert match_way != -1, "Error! LLC line miss in cache during updating line state"
        self.line_state[index][match_way] = new_state

    def updateState_line_word(self, addr, new_state):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        ## only use updateState when the line exist in cache
        assert match_way != -1, "Error! LLC line miss in cache during updating line word state"
        self.line_state[index][match_way] = new_state
        for i in range(len(self.words_state[index][match_way])):
            self.words_state[index][match_way][i] = new_state

    def updateOwner(self, addr, new_owner):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        ## only use updateState when the line exist in cache
        assert match_way != -1, "Error! LLC line miss in cache during updating owner"
        self.owner[index][match_way] = new_owner

    def getOwner(self, addr):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        if (match_way == -1):
            #print("Error! line miss in cache during getting owner")
            return Node.MEM
        else:
            return self.owner[index][match_way]
    
    def getInvCnt(self, addr):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        assert match_way != -1, "Error! LLC line miss in cache during get inv_cnt"
        return self.inv_cnt[index][match_way]
    
    def UpdateInvCnt(self, addr, cnt):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        assert match_way != -1, "Error! LLC line miss in cache during update inv_cnt"
        self.inv_cnt[index][match_way] = cnt
    
    def MinusInvCnt(self, addr):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        assert match_way != -1, "Error! LLC line miss in cache during decrease inv_cnt"
        self.inv_cnt[index][match_way] = self.inv_cnt[index][match_way] - 1
        
    def updateMsgDst(self, addr, new_dst):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        ## only use updateState when the line exist in cache
        assert match_way != -1, "Error! LLC line miss in cache during updating msg dst"
        self.msg_dst[index][match_way] = new_dst

    def getMsgDst(self, addr):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        assert match_way != -1, "Error! LLC line miss in cache during getting msg dst"
        return self.msg_dst[index][match_way]

    ## Adding new address line into cache but need to modified state later
    def addNewLine(self, addr):
        tag, index, offset = self.parseAddr(addr)
        empty_way = -1
        match_way = self.searchSet(index, tag)
        if(match_way != -1):
            return True
        for i in range(self.ways):
            line_occupied = False
            for j in range(self.line_size):
                if(self.words_state[index][i][j] != State.I or self.line_state[index][i] != State.I):
                    line_occupied = True
                    break
            if not line_occupied:
                empty_way = i
                break
        if(empty_way == -1):
            return False
        else:
            self.line_tag[index][empty_way] = tag
            self.renewAccess(addr)
            return True

    def clear_sharer(self, addr):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        if match_way == -1:
            print("Error! line miss in cache during clear sharer")
        else:
            self.sharer[index][match_way] = []

    def add_sharer(self, addr, src):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        assert match_way != -1, "Error! LLC line miss in cache during clear sharer"
        self.sharer[index][match_way].append(src)

    def get_sharer(self, addr):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        assert match_way != -1, "Error! LLC line miss in cache during clear sharer"
        return self.sharer[index][match_way]

    ## Only use when making sure the address is in cache
    def renewAccess(self, addr):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        assert match_way != -1, "Error! line miss in cache during renew access"
        temp_word_state = self.words_state[index][match_way][:]
        temp_line_state = self.line_state[index][match_way]
        temp_sharer = self.sharer[index][match_way][:]
        temp_owner = self.owner[index][match_way]
        temp_msg_dst = self.msg_dst[index][match_way]
        temp_inv_cnt = self.inv_cnt[index][match_way]
        for i in range(match_way - 1, -1, -1):
            self.words_state[index][i+1] = self.words_state[index][i][:]
            self.line_state[index][i+1] = self.line_state[index][i]
            self.line_tag[index][i+1] = self.line_tag[index][i]
            self.sharer[index][i+1] = self.sharer[index][i][:]
            self.owner[index][i+1] = self.owner[index][i]
            self.msg_dst[index][i+1] = self.msg_dst[index][i]
            self.inv_cnt[index][i+1] = self.inv_cnt[index][i]
        self.words_state[index][0] = temp_word_state[:]
        self.line_state[index][0] = temp_line_state
        self.line_tag[index][0] = tag
        self.sharer[index][0] = temp_sharer
        self.owner[index][0] = temp_owner
        self.msg_dst[index][0] = temp_msg_dst
        self.inv_cnt[index][0] = temp_inv_cnt

    ## Return LRU tag and state
    ## Only use when eviction is required
    def getLRU(self, addr):
        tag, index, offset = self.parseAddr(addr)
        LRUtag = self.line_tag[index][self.ways-1]
        LRUaddr = LRUtag * self.total_sets * self.line_size + index * self.line_size + offset
        return LRUaddr, self.line_state[index][self.ways-1], self.words_state[index][self.ways-1][:], self.words_state[index][self.ways-1][:], self.owner[index][self.ways-1]