# Assign CPU loads and non-release atomic RMW accesses a criticality weight of 6
# Assign GPU loads and non-release atomic RMW accesses a criticality weight of 2
# Assign all other accesses a criticality weight of 1

from trace import Inst
from trace import ProcType
from trace import Trace

# Define Global Trace
traces = [
    Trace(Inst.load, ProcType.CPU, 10, 0x1000, 0, 0),
    Trace(Inst.store, ProcType.CPU, 9, 0x1004, 0, 1),
    Trace(Inst.load, ProcType.CPU, 4, 0x1004, 0, 2),
    Trace(Inst.load, ProcType.GPU, 8, 0x1000, 0, 3),
    Trace(Inst.load, ProcType.CPU, 10, 0x1004, 0, 4),
    Trace(Inst.store, ProcType.GPU, 10, 0x1000, 0, 5),
    Trace(Inst.load, ProcType.CPU, 10, 0x1004, 0, 6),
]

if __name__ == '__main__':
    print("hi")

