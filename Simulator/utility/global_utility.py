from enum import Enum, auto
from collections import deque


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
    GetS = auto() # request from CPU
    GetM = auto() # request from CPU
    PutM = auto() # request from CPU
    FwdGetS = auto() # request send to LLC
    FwdGetM = auto() # request send to LLC
    DataDir = auto() # response from LLC (data)
    DataOwner = auto() # response from Owner / response send to other Node
    PutAck = auto() # response from LLC
    Data = auto() # data from cpu to LLC
    
    ## temp state used in translation map, not any actual state in protocol
    Data_V = auto() # represent LLC should receieve RepFwdV instead of RepRvkO
    DataOwner_V = auto() # represent LLC should receieve RepFwdV_E instead of RepRvkO

class msg_class(Enum):
    Request = auto()
    Response = auto()

class type(Enum):
    Success = auto()
    Block = auto()
    Error = auto()

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


class Msg:
    def __init__(self, msg_type, addr, src, dst, ack_cnt = 0, fwd_dst = Node.NULL, target_addr = None):
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
        self.items = deque()

    def is_empty(self):
        """Check if the queue is empty."""
        return len(self.items) == 0

    def enqueue(self, item):
        """Add an item to the end of the queue."""
        self.items.append(item)
    
    def enqueue_front(self, item):
        """Add an item to the end of the queue."""
        self.items.appendleft(item)

    def dequeue(self):
        """Remove the item from the front of the queue and return it."""
        if not self.is_empty():
            return self.items.popleft()
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
        self.items.clear()
    
    def is_member(self, element):
        """Check if the element is in the queue."""
        return element in self.items
    
    def print_all(self):
        print("#################### Queue ####################")
        print(f"Queue Size: {len(self.items)}")
        for item in self.items:
            if item != None:
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
    
    def print_Map(self, key = None):
        if key != None:
            print(f"{key} : {self.map[key]}")
        else:
            for key in self.map:
                print(f"{key} : {self.map[key]}")
