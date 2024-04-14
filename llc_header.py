from enum import Enum, auto
class State(Enum):
    # stale state
    I = auto()  # Invalid
    V = auto()
    S = auto()  # Shared
    O = auto()
    VI = auto() # partially V and partially I, only for line state, there is no VI in word state
    
    # transient state
    IV = auto()
    IS = auto()
    IO = auto()
    SO = auto()
    SV = auto()
    OS = auto()
    OV = auto()
    VI_S = auto()
    VI_O = auto()
    I_I_V = auto() # invalid

    
class msg_type(Enum):
    # Snoop Req from another node
    ReqV = auto()
    ReqS = auto()
    ReqWT = auto()
    ReqOdata = auto()
    ReqWB = auto()
    ## ReqWTdata = auto()
    
    # Snoop response from another node
    InvAck = auto()
    RepRvkO = auto()
    MemRep = auto()
    
    # Req send from LLC
    MemReq = auto()
    RepS = auto()
    RepV = auto()
    RepWT = auto()
    RepWB = auto()
    RepOdata = auto()
    FwdReqS = auto()
    FwdReqV = auto()
    FwdReqO = auto()
    FwdReqOdata = auto()
    FwdRvkO = auto()
    Inv = auto()
    
class Node(Enum):
    LLC = auto()
    CPU0 = auto()
    CPU1 = auto()
    CPU2 = auto()
    CPU3 = auto()
    GPU  = auto()
    MEM = auto()
    NULL = auto()
    
class Type(Enum):
    Success = auto()
    Block = auto()