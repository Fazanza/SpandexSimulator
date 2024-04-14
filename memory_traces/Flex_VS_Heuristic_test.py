import re
from enum import Enum
from typing import Optional
# import sys
# sys.path.append('/home/shengwsw/SpandexSimulator')
# print(sys.path)

# import selection
# import one_big_chunk
# from one_big_chunk import Trace
# from one_big_chunk import Inst
# from one_big_chunk import ProcType


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
    
    def print_Trace(self):
        print(f"inst:{self.inst} device:{self.proctype} value:{self.value} address:{self.addr} device_id:{self.core} index:{self.index}")



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




# Sample memory trace
memory_trace = """
ld 889 cpu_1
ld 890 cpu_1
ld 891 cpu_1
ld 892 cpu_1
ld 893 cpu_1
ld 894 cpu_1
ld 895 cpu_1
ld 896 cpu_1
ld 897 cpu_1
ld 898 cpu_1
ld 899 cpu_1
Phase 0 End
st 333 gpu_1
st 0 gpu_0
st 343 gpu_1
st 10 gpu_0
st 20 gpu_0
st 30 gpu_0
st 666 gpu_2
st 676 gpu_2
st 686 gpu_2
st 40 gpu_0
"""

# Define regex patterns
load_pattern = re.compile(r"ld (\d+) (\w+)_(\d+)")
store_pattern = re.compile(r"st (\d+) (\d+) (\w+)_(\d+)")
phase_pattern = re.compile(r"Phase (\d+) End")

# Function to translate phase numbers
def translate_phase(phase_number):
    if int(phase_number) % 2 == 0:
        return Inst.acquire
    else:
        return Inst.release

# Parse the memory trace
parsed_trace = []
with open("total_order.txt", "r") as file:
    lines = file.readlines()
    for i, line in enumerate(lines):
    # for line in file:
        if line.strip():
            load_match = load_pattern.match(line)
            store_match = store_pattern.match(line)
            phase_match = phase_pattern.match(line)
            if load_match:
                operation = "load"
                inst = Inst.load
                address = load_match.group(1)
                value = -1
                device = 1 if load_match.group(2) == "cpu" else 2
                device_type = ProcType(device) 
                device_id = load_match.group(3)
            elif store_match:
                operation = "store"
                inst = Inst.store
                address = store_match.group(1)
                value = store_match.group(2)
                device = 1 if store_match.group(3) == "cpu" else 2
                device_type = ProcType(device)
                device_id = store_match.group(4)
            elif phase_match:
                inst = translate_phase(phase_match.group(1))
                address = None
                value = -1
                device_type = ProcType.GPU
                device_id = 0
            # print(line)
            # print("inst:{} device:{} value:{} address:{} device_id:{}".format(inst, device_type, value, address, device_id))
            # print("\n")
            # print("My name is {} and I am {} years old.".format(name, age))
            # print(inst)
            # print(device)
            # print(value)
            # print(address)
            # print(device_id)
            parsed_trace.append(Trace(inst,device_type,value,address,device_id,i))
        # for below_line in lines[i+1:]:



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
        # print("entering next_conflict")
        # t1.print_Trace()
        curIndex: int = t1.index + 1
        while curIndex < len(parsed_trace):
            if t1.addr == parsed_trace[curIndex].addr:
                return parsed_trace[curIndex]
            curIndex += 1
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
    # print("entering Next conflict\n")
    t2: Trace = Helper.next_conflict(t1)
    # print("checking returned value")
    # t2.print_Trace()
    t2_prev: Trace = t1
    prevList: Trace = t1
    while t2:
        if Helper.diff_core(t2_prev, t2) or Helper.sync_possible(t2_prev, t2):
            phase = phase - 1

            if phase < 0 or (Helper.same_core(t1, t2) and not Core.reuse_possible(t1, t2)):
                break

            # print(Helper.criticality(t2))
            # t2.print_Trace()
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



"""
Obtaining Type

"""

with open("total_order.txt", "r") as file_in:
    # Read the lines
    lines = file_in.readlines()


pattern = re.compile(r"(ld|st).*$")

with open("total_order_out.txt", "w") as file:
    # lines = file.readlines()
    for i, line in enumerate(lines):
        print(f"Current epoch:{i}")
        if parsed_trace[i].inst == 1:
            type = load_request_type(parsed_trace[i])
        else:
            type = store_request_type(parsed_trace[i])

        file.write(f"{line} {type}\n")

# print(len(parsed_trace))

# print(parsed_trace)
# for item in parsed_trace:
#     item.print_Trace()

