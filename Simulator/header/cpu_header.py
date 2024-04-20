from enum import Enum, auto

class State(Enum):
    I = auto()
    IS_D = auto()
    IM_D = auto()
    S = auto()
    SM_D = auto()
    M = auto()
    MI_A = auto()
    SI_A = auto()
    II_A = auto()

class gpu_msg_type(Enum):
    # req send to LLC
    ReqV = auto()
    ReqWT = auto()
    # rep from 
    RepV = auto()
    RepWT = auto()