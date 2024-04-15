from enum import Enum, auto
import random
from collections import deque
from clock import Clock
import time

from proc_cache import proc_cache

# Define Cache States
class State(Enum):
    I = auto()

    IS_D = auto()
    IM_AD = auto()
    IM_A = auto()

    S = auto()

    SM_AD = auto()
    SM_A = auto()
    
    M = auto()

    MI_A = auto()
    SI_A = auto()
    II_A = auto()


class Event(Enum):
    # From the processor (memory trace queue)
    Load = auto()
    Store = auto()

    # Internal event (only triggered from processor requests)
    Replacement = auto()

    # Forwarded request from other cache on the forward network
    FwdGetS = auto()
    FwdGetM = auto()
    Inv = auto()
    PutAck = auto()

    # Responses from directory
    DataDirNoAcks = auto()
    DataDirAcks = auto()

    # Responses from other caches
    DataOwner = auto()
    InvAck = auto()

    # Triggered after the last ack is received
    LastInvAck = auto()



class DeviceType(Enum):
    Directory = auto()
    Cache = auto()

# class Device(deviceType):
#     def __init__():
#         self.deviceID = 0
#         self.deviceType = deviceType #cache or directory
#     def getID():
#         if deviceType is DeviceType.Directory:
#             return 0
#         else:
#             self.deviceID += 1
#             return self.deviceID


class MessageType(Enum):
    GetS = auto()
    GetM = auto()
    PutS = auto()
    PutM = auto()
    Inv = auto()
    PutAck = auto()
    Data = auto()
    InvAck = auto() 
    LD = auto()
    ST = auto()



# # Memory Operation from Memory Trace
# class 

class Message():
    def __init__(self, mtype, addr, src, dest, data_block, ackCnt=0):
        self.mtype = mtype
        self.addr = addr
        self.src = src
        self.dest = dest
        self.dataBlock = data_block
        self.ackCnt = ackCnt
        
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
        print("==========================")

# transaction buffer entry
class tbe:
    def __init__(self, state, data_block, acks_outstanding):
        self.state = state #state of cache line
        self.data_block = data_block #data for cache line MIA
        self.acks_outstanding = acks_outstanding #numer of acks left to receive

    def __repr__(self):
        return (f"tr : State={self.state}, DataBlock={self.data_block}, "
                f"AcksOutstanding={self.acks_outstanding}")

# transient request buffer
# transaction buffer
class tbeTable:
    def __init__(self):
        self.entries = {}

    def lookup(self, addr):
        return self.entries.get(addr, None)

    def allocate(self, addr):
        # Allocate a new tbe entry for the given address. 
        if addr not in self.entries:
            self.entries[addr] = tbe()
        return self.entries[addr]

    def deallocate(self, addr):
        # Remove the tbe associated with the given address 
        if addr in self.entries:
            del self.entries[addr]

    def is_present(self, addr):
        # Check if there's a tbe allocated for the given address
        return addr in self.entries

class TBETable:
    def __init__(self, number_of_TBEs):
        self.m_number_of_TBEs = number_of_TBEs
        self.m_map = HashMap()

    def isPresent(self, address):
        assert address == self.line_address(address)
        assert len(self.m_map) <= self.m_number_of_TBEs
        return address in self.m_map

    def allocate(self, address):
        assert not self.isPresent(address)
        assert len(self.m_map) < self.m_number_of_TBEs
        self.m_map[address] = ENTRY()

    def deallocate(self, address):
        assert self.isPresent(address)
        assert len(self.m_map) > 0
        del self.m_map[address]

    def areNSlotsAvailable(self, n):
        return (self.m_number_of_TBEs - len(self.m_map)) >= n

    def lookup(self, address):
        if address in self.m_map:
            return self.m_map[address]
        return None

    def print(self, out):
        pass

## below is configruable
## same as cache.py
class CacheEntry:
    def __init__(self, address, state='I', isValid=False, isDirty=False, data_block=None):
        # cache line metadata
        self.address = address & ~0x3F  # base address for the cache line --> Mask out the lower 6 bits for 64-byte alignment. given as hex value ex) 0x211
        self.state = state  # Cache line state for coherency
        self.isValid = isValid
        #self.isDirty = isDirty
        self.data_block = data_block if data_block else [None] * 16  
        #data_block --> [byte1.. byte16] # list of 16byes (currently fixed to 64 bytes per line size but can be configurable)
        self.LRU = 0 # will update later
        # self.accesslvl # read-only? write-only?

        # word granularity
        # flag

    def __str__(self):
        return f"Addr: {hex(self.address)}, State: {self.state}, isValid: {self.isValid}, isDirty: {self.isDirty}"


class Cache: #currently assumes fully-associative
    def __init__(self, size):
        # collection of cache entry
        # dictionary with key: ADDR / value : CacheEntry
        self.entries = {i: CacheEntry(i) for i in range(size)} #preallocate
        #self.entries = {} # unlimited capacity
        self.current_max_LRU = 0  # Track the highest LRU value

    def get_entry(self, address):
        base_address = address & ~0x3F
        return self.entries.get(base_address)

    def set_entry(self, address, state, isValid, isDirty, data_block):
        base_address = address & ~0x3F
        if base_address in self.entries:
            entry = self.entries[base_address]
            entry.state = state
            entry.isValid = isValid
            entry.isDirty = isDirty
            entry.data_block = data_block
            self.setMRU(entry)
        else:
            self.entries[base_address] = CacheEntry(base_address, state, isValid, isDirty, data_block)

    def invalidate(self, address):
        base_address = address & ~0x3F
        if base_address in self.entries:
            self.entries[base_address].state = 'I'
            self.entries[base_address].isValid = False
            print(f"Invalidated Cache Line: {self.entries[base_address]}")

    # checks if cache allocation is available for the given address
    # def is_cache_available(self, address):

    def setMRU(self, cache_entry):
        self.current_max_LRU += 1
        cache_entry.LRU = self.current_max_LRU  # Update the LRU to the highest current value, marking it most recently used


    def print_contents(self):
        # Print each entry's details
        print("=========================")
        print("Printing each cache entry")
        for entry in self.entries.values():
            print(entry)
        print("=========================")

class MemRequest:
    def __init__(self, line_address, request_type):
        self.line_address = line_address
        self.request_type = request_type  # 'Load', 'Store' 


## Cache Controller Model 
## --> Handles Coherence Protocol
class CacheController:
    dirID = 0 #device.getDirID()
    def __init__(self, cache, clock, deviceID=1): 
        self.clock = clock
        self.cache = cache
        self.deviceID = deviceID 
        self.tbes = tbeTable()
        self.channels = {
            'response_in'   : VirtualChannel(),
            'forward_in'    : VirtualChannel(),
            'mandatory_in'  : VirtualChannel(),
            'response_out'  : VirtualChannel(),
            'request_out'   : VirtualChannel()
        }
        self.data_block = None
        self.acks_outstanding = 0
        self.capacity = 10
        
        
        self.last_checked_tick = self.clock.currentTick()
        self.clock.register_observer(self)
        # self.clock.register_callback(self.on_tick_update) 
        self.clock.callback = self.on_tick_update  # Setting the callback

        # self.handle_responses()
        # self.handle_forwards()
        # self.handle_mandatory()

    def on_tick_update(self, new_tick):
        # Handle the tick update here
        print(f"Tick changed detected in CacheController: {new_tick}")

    def update(self, tick):
        print(f"CacheController notified of tick update to: {tick}")    

    def monitor_tick(self):
        while True:
            current_tick = self.clock.currentTick()
            if current_tick != self.last_checked_tick:
                print(f"Tick has changed to: {current_tick}")
                self.last_checked_tick = current_tick
            time.sleep(0.1)  # sleep for a short time before checking again



## MESSAGE HANDLE
## need to enque based on messagetype
    # dequeue from message buffer (at every tick) and trigger events
    def handle_responses(self):
        channel = self.channels['response_in']
        #while channel.is_ready(clock()):
        msg = channel.peek()
        entry = self.cache.get_entry(msg.addr)
        tbe = self.tbes.entries[msg.addr]
        # tbe = self.tbes.lookup(msg.addr)
        # assert tbe is not None, "tbe must exist for this address"

        # if response sender is directory
        # if msg.src is DeviceType.Directory:
        if msg.src is self.DirID
            if msg.mtype is not MessageType.Data:
                raise ValueError("Directory should only reply with data")
            # if cache receives 'ack' from other caches before getting response from directory
            if msg.acks + tbe.AckOutstanding is 0:
                self.trigger(Event.DataDirNoAcks, msg.addr, entry)
            else:
                self.trigger(Event.DataDirAcks, msg.addr, entry)
        
        # if sender is another cache
        else:
            if msg.mtype is responseType.Data:
                self.trigger(Event.DataOwner, msg.addr, entry)
            elif msg.mtype is responseType.InvAck:
                print(f"Got inv ack. {tbe.acks_outstanding} left")
                if tbe.acks_outstanding is 1:
                    self.trigger(Event.LastInvAck, msg.addr, entry)
                else:
                    self.trigger(Event.InvAck, msg.addr, entry)
        # if no messages to process, go to next message queue to process
        self.handle_forwards()

    def handle_forwards(self):
        channel = self.channels['forward_in']
        #while channel.is_ready():
        msg = channel.peek()
        entry = self.cache.get_entry(msg.addr)
        tbe = self.tbes.entries[msg.addr]

        if msg.mtype is MessageType.GetS:
            self.trigger(Event.FwdGetS, msg.addr, entry)
        elif msg.mtype is MessageType.GetM:
            self.trigger(Event.FwdGetM, msg.addr, entry)
        elif msg.mtype is MessageType.Inv:
            self.trigger(Event.Inv, msg.addr, entry)
        elif msg.mtype is MessageType.PutAck:
            self.trigger(Event.PutAck, msg.addr, entry)            
        else:
            raise ValueError("Unexpected forward message type.")
        # if no messages to process, go to next message queue to process
        self.handle_mandatory()

    def handle_mandatory(self):
        channel = self.channels['mandatory_in']
        # while channel.is_ready(): # at each clockEdge(), check for a new message
        msg = channel.peek() # receive should account cache access latency
        entry = self.cache.get_entry(msg.addr)
        #tbe = self.tbes.entries[msg.addr]

        if not entry.isValid and not self.cache.is_cache_available(msg.addr):
        # if entry.state is State.I and not self.cache.is_cache_available(msg.addr):
            # get replacement address from cache
            # replacement_addr = self.probe_cache(msg.addr)
            replacement_entry = self.cache_entries[replacement_addr]
            self.trigger(Event.Replacement, replacement_addr, replacement_entry)
        else: # if entry is valid
            if msg.mtype is MessageType.LD:
                self.trigger(Event.Load, msg.addr, entry)
            elif msg.mtype is MessageType.ST:
                self.trigger(Event.Store, msg.addr, entry)
            else:
                raise ValueError("Unexpected request type from processor")   
    
## EVENT TRIGGER    
    # trigger will cause state transition and will result in action
    # --> queue the output message
    # call do_trasition here
    def trigger(self, event, addr, cache_entry):
        # Event handling logic to be implemented
        print(f"Triggered {event.name} for address {addr}")
        if event is Event.DataDirNoAcks:
            print(f"DataDirNoAcks for address {addr}")
            self.doTransition(event, cache_entry )
        elif event is Event.DataDirAcks:
            print(f"DataDirAcks for address {addr}")
        elif event is Event.DataOwner:
            print(f"DataOwner for address {addr}")
        elif event is Event.InvAck:
            print(f"InvAck for address {addr}")
        elif event is Event.LastInvAck:
            print(f"LastInvAck for address {addr}")
        elif event is Event.Load:
            print(f"Load for address {addr}")
            self.doTransition(event, cache_entry)
        elif event is Event.Store:    
            print(f"Store for address {addr}")
    
## ACTIONS
    ## below are called during do_transition

    def deallocateTBE(self, addr):
        self.tbes.deallocate(addr)
        print("TBE deallocated.")

    def allocateTBE(self, addr):
        self.tbes.allocate(addr)
        print("TBE allocated for transition.")

    # responses to CPU requests
    def loadHit(cache_entry):
        # assert(cache_entry.isValid)
        cache.setMRU(cache_entry)
        # send the data back to CPU
        print("Store hit processed.")

    def storeHit(self):
        cache.setMRU(cache_entry)
        # send the data back to CPU
        print("Store hit processed.")

    # Send request
    def sendGetS():
        out_msg = Message(mtype = MessageType.GetS, addr = addr, src = self.deviceID, dest = self.DirID)
        self.channels["request_out"].enqueue(out_msg)
        print("GetS message sent to fetch exclusive access.")
    def sendGetM():
        out_msg = Message(mtype = MessageType.GetM, addr = addr, src = self.deviceID, dest = self.DirID)
        self.channels["request_out"].enqueue(out_msg)
        print("GetM message sent to fetch exclusive access.")
    def sendPutS():
        out_msg = Message(mtype = MessageType.PutS, addr = addr, src = self.deviceID, dest = self.DirID)
        self.channels["request_out"].enqueue(out_msg)
        print("PutS message sent for downgrading the block state.")
    def sendPutM(self):
        out_msg = Message(mtype = MessageType.PutM, addr = addr, src = self.deviceID, dest = self.DirID)
        self.channels["request_out"].enqueue(out_msg)
        print("PutM message sent to evict block from modified state.")

    # Cache
    def allocateCacheBlock():
        self.cache.set_entry()     
    
    def writeDataToCache(self, message):
        self.data_block = message.data_block
        print("Data written to cache block.")

    def sendCacheDataToReq(self):
        out_msg = Message(mtype = MessageType.Data, addr = msg.addr, src=self.deviceID, dest = msg.src, data_block=cache_entry.data_block)
        self.channels["response_out"].enqueue(out_msg)        
        print("Cache data sent to requestor.")

    def sendCacheDataToDir(self, message):
        out_msg = Message(mtype = MessageType.Data, addr = message.addr, src=self.deviceID, dest = self.DirID, data_block=cache_entry.data_block)
        self.channels["response_out"].enqueue(out_msg)
        print("Cache data sent to directory.")

    def sendInvAcktoReq(self):
        out_msg = Message(mtype = MessageType.InvAck, addr = msg.addr, src=self.deviceID, dest = msg.src, data_block=cache_entry.data_block)
        self.channels["response_out"].enqueue(out_msg)
        print("Invalidation Ack sent to requestor.")

    def forwardEviction(self):
        print("Eviction forwarded to appropriate handler.")

    def deallocateCacheBlock(self):
        self.cache.invalidate(addr)
        print("Cache block deallocated.")

    def decrAcks(self,addr):
        # self.acks_outstanding -= 1
        self.tbes[addr].acks_outstanding -= 1
        print(f"Acks outstanding decremented, now {self.acks_outstanding}.")

    def storeAcks(self,message,addr):
        # assert self.tbes.is_valid(addr)
        self.tbes[addr].acks_outstanding += message.ackCnt
        print("Store acknowledgements processed.")

    def externalLoadHit(self):
        print("External load hit processed.")

    def popMandatoryQueue(self):
        self.channels["mandatory_in"].dequeue()
        print("Response queue popped for processing.")

    def popResponseQueue(self):
        self.channels["response_in"].dequeue()
        print("Response queue popped for processing.")

    def popForwardQueue(self):
        self.channels["forward_in"].dequeue()
        print("Forward queue popped for processing.")
           

## STATE TRANSITION
    # process event
    # 24 if expected
    def doTransition(self, event, cache_entry, message=None):
        print(f"Processing event: {event} in state: {cache_entry.state}")
        
        ## define state transition
        ## transition (cur_state, event, next_state) --> action
        if cache_entry.state is State.I:
            if event is Event.Load:
                cache_state =  State.IS_D
                self.allocateCacheBlock()
                self.allocate()
                print("Transition from I to IS_D state: Load request received in Invalid state.")

        elif cache_entry.state is State.I:
            if event is Event.Store:
                cache_state =  State.IM_D                
                # Actions to Define
                print("Transition from I to IM_D state: Store request received in Invalid state.")

        elif cache_entry.state is State.IS_D :
            if event in [event.Load, event.Store, event.Replacement]:
                self.data_block = message.data_block
                self.stall
            if event is event.Inv:
                self.sendInvAcktoReq()

            elif event in [event.DataDirNoAcks, event.DataOwner]:
                cache_entry.state = State.S
                print("Transition to Shared state: Data received with no ACKs required.")

        elif cache_entry.state in [State.IM_AD, State.IM_A] :
            if event in [event.Load, event.Store, event.FwdGetS, event.FwdGetM]:
                self.stall

        elif cache_entry.state is [State.IM_AD, State.SM_AD]:
            if event in [Event.DataDirNoAcks, Event.DataOwner]:
                cache_entry.state = State.M
                print("Transition to M state: Data received with no ACKs required.")
                self.writeDataToCache()
                self.storeAcks()
                self.popResponseQueue()    

        elif cache_entry.state is State.IM_AD:
            if event is Event.DataDirAcks:
                cache_entry.state = State.IM_A
                print("Transition to IM_A state: Data received with ACKs required.")
                self.writeDataToCache()
                self.storeAcks()
                self.popResponseQueue()
        
        elif cache_entry.state in [State.IM_AD, State.IM_A, State.SM_AD, State.SM_A] :
            if event is event.InvAck:
                self.decrAcks()
                popMandatoryQueue()        

        elif cache_entry.state is [State.IM_A, State.SM_A]:
            if event is event.LastInvAck:
                cache_entry.state = State.M
                print("Transition to M state: Data received with no ACKs required.")
                self.deallocateTBE()
                self.externalStoreHit()
                self.popResponseQueue()    

        elif cache_entry.state in [State.S, State.SM_AD, State.SM_A, State.M] :
            if event in event.Load:
                self.loadHit()
                self.popResponseQueue()

        elif cache_entry.state is State.S:
            if event is Event.Store:
                cache_entry.state = 'SM_AD'
                sendGetM()
                popMandatoryQueue()
                print("Transition to SM_AD state: Store request received in Shared state.")
        
        elif cache_entry.state in [State.SM_AD, State.SM_A]:
            if event in [Event.Store, Event.Replacement, Event.FwdGetS, Event.FwdGetM]:
                print("Stalling: Unsupported event in SM_AD, SM_A state.")
        
        elif cache_entry.state is State.SM_AD:
            if event is Event.InvAck:
                self.acks_outstanding -= 1
                print(f"Processed InvAck: {self.acks_outstanding} ACKs remaining.")

            if self.acks_outstanding is 0 and event is Event.LastInvAck:
                cache_entry.state = State.M
                print("Transition to Modified state: Last InvAck received.")

        elif cache_entry.state is State.M:
            if event is Event.Replacement:
                cache_entry.state = State.I
                self.data_block = None
                print("Invalidated cache: Replacement occurred.")

            elif event is Event.Store:
                print("Processing Store event in Modified state.")
                self.storeHit()
                self.forwardEviction()
                self.popMandatoryQueue()

            elif event is Event.FwdGetS:
                print("Processing FwdGetS event in Modified state.")
                self.sendCacheDataToReq()
                self.sendCacheDataToDir(message)
                self.popForwardQueue()

            elif event is Event.FwdGetM:
                print("Processing FwdGetM event in Modified state.")
                self.sendCacheDataToReq()
                self.deallocateCacheBlock()
                self.popForwardQueue()

        elif cache_entry.state in [State.MI_A, State.SI_A, State.II_A]:
            if event in [Event.Load, Event.Store, Event.Replacement]:
                self.stall
                print("Stalling: Unsupported event in MI_A, SI_A, or II_A state.")

            if event is Event.PutAck:
                cache_entry.state = State.I
                print("Transition to I state: PutAck received.")
                self.deallocateCacheBlock()
                self.popForwardQueue()        
    
        elif cache_entry.state is State.MI_A:
            if event is Event.FwdGetS:
                cache_entry.state = State.SI_A
                print("Transition to SI_A state: Forwarding cache data.")
                self.sendCacheDataToReq()
                self.sendCacheDataToDir()
                self.popForwardQueue()

            elif event is Event.FwdGetM:
                cache_entry.state = State.II_A
                print("Transition to II_A state: Forwarding cache data.")
                self.sendCacheDataToReq()
                self.popForwardQueue()

        elif cache_entry.state is State.SI_A:
            if event is Event.Inv:
                cache_entry.state = State.II_A
                print("Transition to II_A state: Invalidating cache block.")
                self.sendInvAcktoReq()
                self.popForwardQueue()

        elif cache_entry.state is State.II_A:
            if event is Event.PutAck:
                cache_entry.state = State.I
                print("Transition to I state: PutAck received.")
                self.deallocateCacheBlock()
                self.popForwardQueue()

clock = Clock()
for i in range(100):
    clock.clockEdge()

# Cache Test
# Example of creating and using the Cache
cache_size = 10  # Define the size of the cache
cache = Cache(cache_size)
# Set some entries
cache.set_entry(0x1, 'Modified', True, True, [0x01, 0x02, 0x03, 0x04])
cache.set_entry(0x300, 'Shared', True, False, [0x05, 0x06, 0x07, 0x08])
# Print all cache contents
cache.print_contents()

dut = proc_cache(cache_size=8, ways = 2, line_size = 2, memory = 16) 


# test 1
# Instantiate cache and queue

cache_ctrl = CacheController(cache, clock)
# cache_ctrl.monitor_tick()
# mandatory_queue = MandatoryQueue()
# # Simulate adding requests to the queue and handling them
# mandatory_queue.enqueue(MemRequest("0x1A", "Load"))
# mandatory_queue.enqueue(MemRequest("0x1A", "Store"))
# handle_incoming_requests(cache_ctrl, mandatory_queue)
# handle_incoming_requests(cache_ctrl, mandatory_queue)

msg = Message(MessageType.LD, 0x0, "Node1", "Node2", [0x01, 0x02, 0x03, 0x04])
cache_ctrl.channels['mandatory_in'].print_all_messages()
for i in range(5):
    #cache_ctrl.channels['mandatory_in'].send_message(msg)
    cache_ctrl.channels['response_in'].send_message(msg)
    
cache_ctrl.channels['mandatory_in'].print_all_messages()
cache_ctrl.handle_mandatory()
cache_ctrl.handle_mandatory()
cache_ctrl.handle_mandatory()
# print(cache_ctrl.channels['mandatory_in'])

for i in range(5):
    clock.clockEdge()
    if cache_ctrl.channels['response_in'].is_empty():
        if cache_ctrl.channels['forward_in'].is_empty():
            cache_ctrl.handle_mandatory()
        else:
            cache_ctrl.handle_forwards()
    else :
        cache_ctrl.handle_response()

# # test2
# sample_msg = Message(
#     addr="0x1A",
#     response_type=responseType.Data,
#     src="Node1",
#     dest="Node2",
#     data_block="100",
#     ackCnt="2"
# )

# sample_msg2 = Message(
#     addr="0x1A",
#     response_type=responseType.Data,
#     src="Node1",
#     dest="Node2",
#     data_block="100",
#     ackCnt="2"
# )
# cache_ctrl.channels['response_in'].send_message(sample_msg)
# cache_ctrl.channels['response_in'].send_message(sample_msg2)
# cache_ctrl.channels['response_in'].print_all_messages()


# # test 3

# cache_controller = CacheController()
# cache_controller.process_event(Event.Load)
# message = Message('Data', 'Directory', 'Cache', 'data_block_123')
# cache_controller.peek(message)
# cache_controller.process_event(Event.Store)
# cache_controller.process_event(Event.InvAck)
# cache_controller.process_event(Event.LastInvAck)





