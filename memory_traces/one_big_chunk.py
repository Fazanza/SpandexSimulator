from enum import Enum
from typing import Optional
from Flex_VS_Heuristic_test import parsed_trace


"""
Core Part

"""

class Inst(Enum):
    load = 1
    store = 2
    barrier = 3
    acquire = 4
    release = 5


class ProcType(Enum):
    CPU = 1
    GPU = 2


class Trace:
    def __init__(
            self,
            _inst: Inst,
            _proctype: ProcType,
            _value: int,
            _addr: int,
            _core: int,
            _index: int,
    ):
        self.inst = _inst
        self.proctype = _proctype
        self.value = _value
        self.addr = _addr
        self.core = _core
        self.index = _index




CACHE_SIZE = 1024
BLOCK_SIZE = 4


class Core:
    def __init__(self, _id: int):
        self.id = _id
        self.cache_capacity = CACHE_SIZE
        self.block_size = BLOCK_SIZE

    '''
    Returns whether data accessed by X will still be in the cache
    when access Y is executed (true only if number of unique bytes
    accessed between X and Y is less than 75% of cache capacity)
    '''

    @staticmethod
    def reuse_possible(self, t1: Trace, t2: Trace) -> bool:
        assert (t1.core == t2.core)
        if t1.index > t2.index:
            return self.reuse_helper(t1, t2.index)
        return self.reuse_helper(t2, t1.index)

    '''
    T2 is the larger trace index, goes from T2 to index and sees
    how many times it finds a address that doesn't match the other 
    address
    '''
    @staticmethod
    def reuse_helper(self, t2: Trace, index: int) -> bool:
        usedAddrs = {t2.addr}
        count = t2.index
        while count >= index + 1:
            count = count - 1
            if parsed_trace[count].core != t2.core:
                continue
            if parsed_trace[count].addr in usedAddrs:
                continue
            usedAddrs.add(parsed_trace[count].addr)
            if len(usedAddrs) > (CACHE_SIZE * 0.75):
                return False
        return True


"""
Trace Helper functions
"""



class Helper:
    @staticmethod
    def is_load(t: Trace) -> bool:
        return t.inst == Inst.load

    @staticmethod
    def is_store(t: Trace) -> bool:
        return t.inst == Inst.store

    @staticmethod
    def from_cpu(t: Trace) -> bool:
        return t.proctype == ProcType.CPU

    @staticmethod
    def from_gpu(t: Trace) -> bool:
        return t.proctype == ProcType.GPU

    @staticmethod
    def same_core(t1: Trace, t2: Trace) -> bool:
        return t1.core == t2.core

    @staticmethod
    def diff_core(t1: Trace, t2: Trace) -> bool:
        return t1.core != t2.core

    @staticmethod
    def same_inst(t1: Trace, t2: Trace) -> bool:
        return t1.inst == t2.inst

    '''
    Returns the next access to the same address as t1 following
    t1 in the dynamic trace
    '''
    @staticmethod
    def next_conflict(t1: Trace) -> Optional[Trace]:
        curIndex: int = t1.index + 1
        while curIndex < len(parsed_trace):
            if t1.addr == parsed_trace[curIndex].addr:
                return parsed_trace[curIndex]
        return None

    '''
    Returns the next access to any address in the cache block 
    following t1 in the dynamic trace
    '''
    @staticmethod
    def next_block_conflict(t1: Trace) -> Optional[Trace]:
        curIndex: int = t1.index
        while curIndex < len(parsed_trace) - 1:
            curIndex = curIndex + 1
            if parsed_trace[curIndex].core != t1.core:
                continue
            if parsed_trace[curIndex].addr % BLOCK_SIZE == 0:
                return parsed_trace[curIndex]
        return None

    '''
    Returns the most recent access preceding t1 in the dynamic trace
    '''
    @staticmethod
    def prev_acc(t1: Trace) -> Optional[Trace]:
        if not t1.index:
            return None
        return parsed_trace[t1.index - 1]

    '''
    Returns the most recent access to same address as t1 preceding t1
    in the dynamic trace
    '''
    @staticmethod
    def prev_conflict(t1: Trace) -> Optional[Trace]:
        curIndex: int = t1.index - 1
        while curIndex >= 0:
            if t1.addr == parsed_trace[curIndex].addr:
                return parsed_trace[curIndex]
            curIndex = curIndex - 1
        return None

    '''
    Returns true if t1 and t2 are issued from the same core and there exists a 
    synchronization operation S between X and Y in program order such that
    1) t1 or t2 is an atomic access
    2) t1 is a load and S is an acquire operation (start of a new kernel)
    3) t1 is a store and S is a release operation (completion of a kernel)
    '''
    @staticmethod
    def sync_possible(t1: Trace, t2: Trace) -> bool:
        if t1.core != t2.core:
            return False

        if t1.inst == Inst.load and t2.inst == Inst.acquire:
            return True

        if t1.inst == Inst.store and t2.inst == Inst.release:
            return True

        return False

    '''
    Returns a value that represents the estimated performance criticality of X
    '''
    @staticmethod
    def criticality(t1: Trace) -> int:
        if t1.inst != Inst.load:
            return 1

        if t1.proctype == ProcType.CPU:
            return 6

        if t1.proctype == ProcType.GPU:
            return 2


"""
Heuristic Functions
"""

'''
Returns true if ownership for t1 is likely to improve overall performance
Basically checks whether t1 obtaining ownership will help or hurt performance for t2
'''


def owner_benefit(t1: Trace) -> bool:
    phase: int = 5
    x_score: int = 0
    t2: Trace = Helper.next_conflict(t1)
    t2_prev: Trace = t1
    prevList: Trace = t1
    while t2:
        if Helper.diff_core(t2_prev, t2) or Helper.sync_possible(t2_prev, t2):
            phase = phase - 1

            if phase < 0 or (Helper.same_core(t1, t2) and not Core.reuse_possible(t1, t2)):
                break

            y_val = 0
            if Helper.same_core(t2, prevList):
                y_val = 2 * Helper.criticality(t2)
            else:
                y_val = 0.5 * Helper.criticality(t2)

            if Helper.same_core(t1, t2):
                x_score = x_score + y_val
            else:
                x_score = x_score - y_val
                prevList = t2

        t2_prev = t2
        t2 = Helper.next_conflict(t2)

    if x_score > 0:
        return True
    return False


'''
Returns true if obtaining shared state for t1 would improve performance
based on expected reuse effects. Assume that obtaining shared state is
beneficial if the issuing core is a CPU and it can lead to at least one
future cache hit
'''


def shared_state_benefit(t1: Trace) -> bool:
    if t1.proctype == ProcType.GPU:
        return False
    t2: Trace = Helper.next_block_conflict(t1)
    t2_prev: Trace = t1
    while t2:
        if Helper.diff_core(t2_prev, t2) or Helper.sync_possible(t2_prev, t2):
            if Helper.is_load(t2) and Helper.same_core(t1, t2):
                return True
            if Helper.is_store(t2) and Helper.diff_core(t1, t2):
                return False
        t2_prev = t2
        t2 = Helper.next_block_conflict(t2)
    return False


'''
Return true if using owner prediction is likely to be successful for the
given prediction mechanism based on execution history
'''


def owner_pred_benefit(t1: Trace) -> bool:
    x_score: int = 0
    phase: int = 4
    t1_prev: Trace = Helper.prev_conflict(t1)
    t2: Trace = Helper.prev_acc(t1)
    while t2:
        t2_prev: Trace = Helper.prev_conflict(t2)
        if Helper.same_core(t1, t2) and Helper.same_inst(t1, t2):
            phase = phase - 1

            if phase < 0:
                break

            if Helper.same_core(t2_prev, t1_prev):
                x_score = x_score + 1
            else:
                x_score = x_score - 1
        t2 = Helper.prev_acc(t2)

    if x_score > 0:
        return True
    return False



"""
Selection Functions

"""

class Type(Enum):
    ReqO_Data = 0
    ReqS = 1
    ReqVo = 2
    ReqV = 3
    ReqO = 4
    ReqWTo = 5
    ReqWTfwd = 6
    ReqWTo_Data = 7
    ReqWTfwd_Data = 8


'''
Load request type selection
'''


def load_request_type(t1: Trace) -> Type:
    if owner_benefit(t1):
        return Type.ReqO_Data
    elif shared_state_benefit(t1):
        return Type.ReqS
    elif owner_pred_benefit(t1):
        return Type.ReqVo
    else:
        return Type.ReqV


'''
Store request type selection
'''


def store_request_type(t1: Trace) -> Type:
    if owner_benefit(t1):
        return Type.ReqO
    elif owner_pred_benefit(t1):
        return Type.ReqWTo
    else:
        return Type.ReqWTfwd


'''
RMW request type selection
'''


def RMW_request_type(t1: Trace) -> Type:
    if owner_benefit(t1):
        return Type.ReqO_Data
    elif owner_pred_benefit(t1):
        return Type.ReqWTo_Data
    else:
        return Type.ReqWTfwd_Data
