from enum import Enum
from typing import Optional

from main import traces


class Inst(Enum):
    load = 1
    store = 2


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
        return False

    '''
    Returns a value that represents the estimated performance criticality of X
    '''
    @staticmethod
    def criticality(t1: Trace) -> int:
        if t1.inst != Inst.load:
            return 2

        if t1.proctype == ProcType.CPU:
            return 6
        if t1.proctype == ProcType.GPU:
            return 2



