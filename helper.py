from typing import Optional

from globals import BLOCK_SIZE
from globals import traces
from globals import Inst
from globals import ProcType
from globals import Trace

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
        if not t1 or not t2: return False
        return t1.core == t2.core

    @staticmethod
    def diff_core(t1: Trace, t2: Trace) -> bool:
        if not t1 or not t2: return False
        return t1.core != t2.core

    @staticmethod
    def same_inst(t1: Trace, t2: Trace) -> bool:
        if not t1 or not t2: return False
        return t1.inst == t2.inst

    '''
    Returns the next access to the same address as t1 following
    t1 in the dynamic trace
    '''
    @staticmethod
    def next_conflict(t1: Trace) -> Optional[Trace]:
        curIndex: int = t1.index + 1
        while curIndex < len(traces):
            if t1.addr == traces[curIndex].addr:
                return traces[curIndex]
        return None

    '''
    Returns the next access to any address in the cache block 
    following t1 in the dynamic trace
    '''
    @staticmethod
    def next_block_conflict(t1: Trace) -> Optional[Trace]:
        curIndex: int = t1.index
        while curIndex < len(traces) - 1:
            curIndex = curIndex + 1
            if traces[curIndex].core != t1.core:
                continue
            if traces[curIndex].addr % BLOCK_SIZE == 0:
                return traces[curIndex]
        return None

    '''
    Returns the most recent access preceding t1 in the dynamic trace
    '''
    @staticmethod
    def prev_acc(t1: Trace) -> Optional[Trace]:
        if not t1.index:
            return None
        return traces[t1.index - 1]

    '''
    Returns the most recent access to same address as t1 preceding t1
    in the dynamic trace
    '''
    @staticmethod
    def prev_conflict(t1: Trace) -> Optional[Trace]:
        curIndex: int = t1.index - 1
        while curIndex >= 0:
            if t1.addr == traces[curIndex].addr:
                return traces[curIndex]
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



