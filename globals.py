from enum import Enum

CACHE_SIZE = 1024
BLOCK_SIZE = 4

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

traces = [
    Trace(Inst.load, ProcType.CPU, 10, 0x1000, 0, 0),
    Trace(Inst.store, ProcType.CPU, 9, 0x1004, 0, 1),
    Trace(Inst.load, ProcType.CPU, 4, 0x1004, 0, 2),
    Trace(Inst.load, ProcType.GPU, 8, 0x1000, 0, 3),
    Trace(Inst.load, ProcType.CPU, 10, 0x1004, 0, 4),
    Trace(Inst.store, ProcType.GPU, 10, 0x1000, 0, 5),
    Trace(Inst.load, ProcType.CPU, 10, 0x1004, 0, 6),
]
