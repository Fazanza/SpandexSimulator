from enum import Enum, auto


class Node(Enum):
    LLC = auto()
    CPU0 = auto()
    CPU1 = auto()
    CPU2 = auto()
    CPU3 = auto()
    GPU = auto()
    MEM = auto()
    NULL = auto()


class msg_type(Enum):
    # Snoop Req from another node ()
    ReqV = auto()
    ReqS = auto()
    ReqWT = auto()
    ReqOdata = auto()
    ReqWB = auto()
    ## ReqWTdata = auto()

    # Snoop response from another node
    InvAck = auto()
    RepRvkO = auto()
    RepFwdV = auto()
    RepFwdV_E = auto()
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
    FwdReqV_E = auto() # ReqV exclusive, The O state in CPU will directly downgrade to 
    FwdReqOdata = auto()
    FwdRvkO = auto()
    Inv = auto()

    # Req generated from Node Instruction
    Load = auto()
    Store = auto()
    Barrier = auto()

    # CPU message type
    GetS = auto()
    GetM = auto()
    PutM = auto()
    FwdGetS = auto()
    FwdGetM = auto()
    DataDir = auto() # data from LLC
    DataOwner = auto() # data from Owner
    PutAck = auto()
    Data = auto() # data from cpu to LLC

# class msg_classify:
#     msg_map = {
#         msg_type.ReqV       :       msg_class.Request   ,
#         msg_type.ReqS       :       msg_class.Request   ,
#         msg_type.ReqWT      :       msg_class.Request   ,
#         msg_type.ReqOdata   :       msg_class.Request   ,
#         msg_type.ReqWB      :       msg_class.Request   ,
#         msg_type.InvAck     :       msg_class.Response  ,
#         msg_type.RepRvkO    :       msg_class.Response  ,
#         msg_type.RepFwdV    :       msg_class.Response  ,
#         msg_type.RepFwdV_E  :       msg_class.Response  ,
#         msg_type.RepS       :       msg_class.Response  ,
#         msg_type.RepV       :       msg_class.Response  ,
#         msg_type.RepWT      :       msg_class.Response  ,
#         msg_type.RepWB      :       msg_class.Response  ,
#         msg_type.RepOdata   :       msg_class.Response  ,
#         msg_type.FwdReqS    :       msg_class.Request   ,
#         msg_type.FwdReqV    :       msg_class.Request   ,
#         msg_type.FwdReqV_E  :       msg_class.Request   ,
#         msg_type.FwdReqOdata:       msg_class.Request   ,
#         msg_type.FwdRvkO    :       msg_class.Request   ,
#         msg_type.Inv        :       msg_class.Request   ,
#         msg_type.FwdGetS    :       msg_class.Request   ,
#         msg_type.FwdGetM    :       msg_class.Request   ,
#         msg_type.DataDir    :       msg_class.Response  ,
#         msg_type.DataOwner  :       msg_class.Response  ,
#         msg_type.PutAck     :       msg_class.Response  
#     }

class type(Enum):
    Success = auto()
    Block = auto()
    Error = auto()


class Msg:
    def __init__(self, msg_type, addr=None, src=None, dst=None, ack_cnt=0, fwd_dst=None, target_addr = None):
        self.msg_type = msg_type
        self.addr = addr
        self.src = src
        self.dst = dst
        self.fwd_dst = fwd_dst
        self.ack_cnt = ack_cnt
        self.target_addr = target_addr ## when request of target addr evict lru, may need to send invalidation to LRU, need to add the request of target addr to Inv 
    
    def print_msg(self):
        if self == None:
                print(None)
        else:
            print(f"msg_type: {self.msg_type}, addr: {self.addr}, src: {self.src}, dst: {self.dst}, fwd_dst: {self.fwd_dst}, ack_cnt: {self.ack_cnt}, target_addr: {self.target_addr}")


class Queue:
    def __init__(self):
        self.items = []

    def is_empty(self):
        """Check if the queue is empty."""
        return len(self.items) == 0

    def enqueue(self, item):
        """Add an item to the end of the queue."""
        self.items.append(item)

    def dequeue(self):
        """Remove the item from the front of the queue and return it."""
        if not self.is_empty():
            return self.items.pop(0)
        else:
            raise IndexError("dequeue from an empty queue")

    def peek(self):
        """Look at the first item of the queue without removing it."""
        if not self.is_empty():
            return self.items[0]
        else:
            raise IndexError("peek from an empty queue")

    def size(self):
        """Return the number of items in the queue."""
        return len(self.items)

    def clear(self):
        """Remove all items from the queue."""
        self.items = []
    
    def print_all(self):
        print("#################### Queue ####################")
        for item in self.items:
            item.print_msg()


class Map:
    def __init__(self):
        self.map = {}

    def insert(self, key, value):
        if key in self.map:
            print(f"Error: Key '{key}' already exists.")
            return False
        self.map[key] = value
        return True

    def search(self, key):
        if key in self.map:
            return self.map[key]
        else:
            print(f"Key: {key} not found.")
            return None

    def change(self, key, value):
        if key in self.map:
            self.map[key] = value
            print(f"Changed Key: {key} to new Value: {value}")
        else:
            print(f"Error: Key '{key}' not found. No value changed.")