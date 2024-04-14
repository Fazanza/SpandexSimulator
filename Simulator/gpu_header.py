from enum import Enum, auto

class State(Enum):
    I = auto()
    V = auto()
    IV = auto()
    VI = auto()
    WTV = auto()

class Inst_type(Enum):
    Load = auto()
    Store = auto()
    Sync = auto()

class Inst():
    def __init__(self, inst_type, addr, sync_cnt):
        self.inst_type = inst_type
        self.addr = addr
        self.sync_cnt = sync_cnt

class gpu_msg_type(Enum):
    # req send to LLC
    ReqV = auto()
    ReqWT = auto()
    RepV = auto()
    RepWT = auto()
    
class Type(Enum):
    Success = auto()
    Block = auto()