from enum import Enum, auto

class State(Enum):
    I = auto()
    V = auto()
    IV = auto()
    VI = auto()
    WTV = auto()
    WTV_L = auto()

class Inst_type(Enum):
    Load = auto()
    Store = auto()
    Barrier = auto()

class Inst():
    def __init__(self, inst_type, addr, barrier_name):
        self.inst_type = inst_type
        self.addr = addr
        self.barrier_name = barrier_name # name for barrier
    
    def print_Inst(self):
        if self == None:
            print(None)
        else:
            print(f"inst_type: {self.inst_type}, addr: {self.addr}, barrier_name: {self.barrier_name}")

class gpu_msg_type(Enum):
    # req send to LLC
    ReqV = auto()
    ReqWT = auto()
    # rep from 
    RepV = auto()
    RepWT = auto()
    