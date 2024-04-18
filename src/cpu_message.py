from enum import Enum, auto
from collections import deque

class Node(Enum):
    LLC = auto()
    CPU0 = auto()
    CPU1 = auto()
    CPU2 = auto()
    CPU3 = auto()
    GPU  = auto()
    MEM = auto()
    NULL = auto()


class MessageType(Enum):
    # Request Messages
    GetS = auto()
    GetM = auto()
    PutS = auto()
    PutM = auto()

    # Fwd In Messages
    FwdGetS = auto()
    FwdGetM = auto()
    Inv = auto()
    PutAck = auto()

    # Response Messages
    Data = auto()
    InvAck = auto() 

    # Instruction Message
    LD = auto()
    ST = auto()

    # just for parsing
    Barrier = auto()

# # Memory Operation from Memory Trace
# class 

class Message():
    def __init__(self, mtype, addr=None, src=Node.NULL, dest=Node.NULL, fwd_dest = Node.NULL, ackCnt=0, data_block=None, barrierID = None, barrierCnt=0):
        self.mtype = mtype
        self.addr = addr
        self.src = src
        self.dest = dest
        self.fwd_dest = fwd_dest 
        self.ackCnt = ackCnt
        self.dataBlock = data_block # not used since we don't care about correctness
        self.barrierID = barrierID
        self.barrierCnt = barrierCnt

        
    def __str__(self):
        return (f"Message Type: {self.mtype}, "
                f"Address: {self.addr}, "
                f"Source: {self.src}, "
                f"Destination: {self.dest}, "
                f"Data Block: {self.dataBlock}, "
                f"Ack Count: {self.ackCnt}")

# Virtual Channel
# Message Buffer
class VirtualChannel:
    def __init__(self):
        self.messages = deque()
        self.transaction_ongoing = False
        #self.clock = clock

    def __str__(self):
        return self.content

    def is_ready(self):
        # return bool(self.queue)
        return bool(self.messages)
        # return self.clock.currentTick() >= self.clock.clockEdge()


    def send_message(self, message): #enque
        self.messages.append(message)

    #def receive_message(self):
    def dequeue(self):    
        return self.messages.popleft() if self.messages else None

    def is_empty(self):
        return len(self.messages) == 0

    def peek(self): #check the head point value of queue
        return self.messages[0] if self.messages else None
    
    def print_all_messages(self):
        if self.is_empty():
            print("VC is empty")
        print("==========================")    
        for msg in self.messages:
            print("VC CONTENTS")
            print(msg)  # This will invoke __str__ method of Message object
        print(f"transaction_ongoing: {self.transaction_ongoing}")    
        print("==========================")