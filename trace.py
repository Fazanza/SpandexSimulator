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



