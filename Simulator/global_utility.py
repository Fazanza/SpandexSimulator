from enum import Enum, auto

class Node(Enum):
    LLC = auto()
    CPU0 = auto()
    CPU1 = auto()
    CPU2 = auto()
    CPU3 = auto()
    GPU  = auto()
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

class msg:
    def __init__(self, msg_type, addr, src, dst, ack_cnt, fwd_dst):
        self.msg_type   = msg_type
        self.addr       = addr
        self.src        = src
        self.dst        = dst
        self.fwd_dst    = fwd_dst
        self.ack_cnt    = ack_cnt

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