import math
from enum import Enum, auto
import random
from collections import deque
from header.cpu_header import *
from utility.global_utility import *


## for GPU cache
## 1. if evicted, no wb will be happen, just invalidate the line
class CPU_cache:
    cache_size = 0 # number of words in whole cache
    memory_size = 0 # number of words in whole memory
    line_size = 0 # number of words in a line
    ways = 0 # cache way associativity
    total_sets = 0 # number of sets in cache
    line_state = []
    line_tag = []
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
        self.line_tag = [[-1 for j in range(self.ways)] for k in range(self.total_sets)]

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


    def getState_line(self, addr):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        # miss
        if (match_way == -1):
            return State.I
        else:
            ##updateAccesing
            return self.line_state[index][match_way]


    def updateState_line(self, addr, new_state):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        ## only use updateState when the line exist in cache
        assert match_way != -1, "Error! CPU line miss in cache during updating state"
        self.line_state[index][match_way] = new_state


    ## Adding new address line into cache but need to modified state later
    def addNewLine(self, addr):
        tag, index, offset = self.parseAddr(addr)
        empty_way = -1
        match_way = self.searchSet(index, tag)
        if(match_way != -1):
            return True
        for i in range(self.ways):
            line_occupied = False
            if self.line_state[index][i] != State.I:
                line_occupied = True
            if not line_occupied:
                empty_way = i
                break
        if(empty_way == -1):
            return False
        else:
            self.line_tag[index][empty_way] = tag
            self.renewAccess(addr)
            return True

    ## Only use when making sure the address is in cache
    def renewAccess(self, addr):
        tag, index, offset = self.parseAddr(addr)
        match_way = self.searchSet(index, tag)
        assert match_way != -1, "Error! CPU line miss in cache during renew access"
        temp_line_state = self.line_state[index][match_way]
        for i in range(match_way - 1, -1, -1):
            self.line_state[index][i+1] = self.line_state[index][i]
            self.line_tag[index][i+1] = self.line_tag[index][i]
        self.line_state[index][0] = temp_line_state
        self.line_tag[index][0] = tag

    ## Return LRU tag and state
    ## Only use when eviction is required
    def getLRU(self, addr):
        tag, index, offset = self.parseAddr(addr)
        LRUtag = self.line_tag[index][self.ways-1]
        LRUaddr = LRUtag * self.total_sets * self.line_size + index * self.line_size + offset
        return LRUaddr, self.line_state[index][self.ways-1]
