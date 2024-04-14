from enum import Enum, auto
import random
from collections import deque



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

# triggered by incoming messages
# msg_type
class msg_type(Enum):
#class Event(Enum)
    Load = auto()
    Store = auto()

    Inv = auto()
    
    Data = auto()
    EData = auto()
    
    Ack = auto()

class Event(Enum):
    Load = auto()
    Store = auto()

    Inv = auto()

    Data = auto()
    EData = auto()

    Ack = auto()

# Types of Request Messages
class requestType(Enum):
    # Requests from the cache for coherence
    GetS = auto()
    GetM = auto()
    PutS = auto()
    PutM = auto()
    
    # Requests from the directory to the caches on the fwd network
    Inv = auto()
    PutAck = auto() # The put request has been processed

class DeviceType(Enum):
    Directory = auto()
    Cache = auto()

# Types of Response Messages
class responseType(Enum):
    Data = auto()
    InvAck = auto() #from another cache

# Request Message Packet Struct
class requestMsg():
    def __init__(self, addr, request_type, src, dest, data_block):
        self.addr = addr
        self.requestType = request_type
        self.src = src # Node that initiated the request
        self.dest = dest # destination node
        self.dataBlock = data_block


# Cache->Dir Messages or Fwd Messages
class ResponseMsg():
    def __init__(self, addr, response_type, src, dest, data_block, ackCnt):
        self.addr = addr
        self.responseType = response_type
        self.src = src # Node that initiated the request
        self.dest = dest # destination node
        self.dataBlock = data_block
        self.ackCnt = ackCnt

# Virtual Channel
# Message Buffer
class VirtualChannel:
    def __init__(self):
        self.messages = deque()

    def is_ready(self):
        # return bool(self.queue)
        return bool(self.messages)


    def send_message(self, message):
        self.messages.append(message)

    def receive_message(self):
        return self.messages.popleft() if self.messages else None

    def is_empty(self):
        return len(self.messages) == 0

    def peek(self):
        return self.messages[0] if self.messages else None
        # return self.queue[0] if self.queue else None
    
    def print_all_messages(self):
        while not self.is_empty():
            print(self.receive_message())


# transient request buffer entry
class trb:
    def __init__(self):
        self.state = State.I #state of cache line
        self.data_block = None #data for cache line
        self.acks_outstanding = 0 #numer of acks left to receive

    def __repr__(self):
        return (f"tr : State={self.state}, DataBlock={self.data_block}, "
                f"AcksOutstanding={self.acks_outstanding}")

# transient request buffer
class trbTable:
    def __init__(self):
        self.entries = {}

    def lookup(self, addr):
        ## Return the trb entry for the given address if it exists
        return self.entries.get(addr, None)

    def allocate(self, addr):
        # Allocate a new trb entry for the given address. 
        if addr not in self.entries:
            self.entries[addr] = trb()
        return self.entries[addr]

    def deallocate(self, addr):
        # Remove the trb associated with the given address 
        if addr in self.entries:
            del self.entries[addr]

    def is_present(self, addr):
        # Check if there's a trb allocated for the given address
        return addr in self.entries

## below is configruable
## same as cache.py
class CacheEntry:
    def __init__(self, address, state='I', valid=False, dirty=False, data_block=None):
        self.address = address
        self.state = state  # 'I' for Invalid, 'M' for Modified, 'S' for Shared, 'E' for Exclusive
        self.valid = valid
        self.dirty = dirty
        self.data_block = data_block

    def __str__(self):
        return f"Addr: {self.address}, State: {self.state}, Valid: {self.valid}, Dirty: {self.dirty}"



class Cache:
    def __init__(self, size):
        # collection of cache entry
        self.entries = {i: CacheEntry(i) for i in range(size)}

    def get_entry(self, address):
        return self.entries.get(address)

    def set_entry(self, address, state, valid, dirty, data_block):
        if address in self.entries:
            entry = self.entries[address]
            entry.state = state
            entry.valid = valid
            entry.dirty = dirty
            entry.data_block = data_block
        else:
            self.entries[address] = CacheEntry(address, state, valid, dirty, data_block)

    def invalidate(self, address):
        if address in self.entries:
            self.entries[address].state = 'I'
            self.entries[address].valid = False
            print(f"Invalidated Cache Line: {self.entries[address]}")

    # checks if cache allocation is available for the given address
    # def is_cache_available(self, address):        

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

class MandatoryQueue:
    def __init__(self):
        self.queue = []

    def is_ready(self):
        return len(self.queue) > 0

    def enqueue(self, request):
        self.queue.append(request)

    def peek(self):
        return self.queue[0] if self.queue else None

    def dequeue(self):
        return self.queue.pop(0) if self.queue else None

## cache controller model 
## --> this is the part that takes care of state transition and event handling

class CacheController:
    def __init__(self, cache):
        self.cache = cache
        self.trbs = trbTable()
        self.channels = {
            'response_in': VirtualChannel(),
            'forward_in': VirtualChannel(),
            'mandatory_in': VirtualChannel()
        }
        self.data_block = None
        self.acks_outstanding = 0
        self.capacity = 10

    # trigger will cause state transition and will result in action
    # --> queue the output message
    # call do_trasition here
    def trigger(self, event, addr, cache_entry):
        # Event handling logic to be implemented
        print(f"Triggered {event.name} for address {addr}")
        if event == Event.DataDirNoAcks:
            print(f"DataDirNoAcks for address {addr}")
        elif event == Event.DataDirAcks:
            print(f"DataDirAcks for address {addr}")
        elif event == Event.DataOwner:
            print(f"DataOwner for address {addr}")
        elif event == Event.InvAck:
            print(f"InvAck for address {addr}")
        elif event == Event.LastInvAck:
            print(f"LastInvAck for address {addr}")

    # ACTIONS
    ## below are called during do_transition
    def allocateCacheBlock():
        self.cache.allocateBlock
    
    def sendGetS():
        msg_buffer.enqueue()
            # addr
            # msg_type
            # requestor
            # destination
    def sendGetM():
        msg_buffer.enqueue(msg)

################
    # def process_messages(self):
    #     for channel in self.channels:
    #         while not channel.is_empty():
    #             message = channel.receive_message()
    #             self.handle_message(message)

    # def handle_message(self, message):
    #     if message.address not in self.cache:
    #         self.cache[message.address] = CacheEntry(state=State.NP)

    #     entry = self.cache[message.address]
    #     print(f"Handling message for {message.address}: Current State={entry.state}, Type={message.mtype}")

    #     if message.mtype in [Event.Load, Event.Store, Event.Ifetch]:
    #         self.do_transition(entry, message.mtype)

    def handle_responses(self):
        channel = self.channels['response_in']
        while channel.is_ready():
            msg = channel.receive_message()
            entry = self.cache.get_entry[msg.addr]
            trb = self.trbs[msg.addr]
            # trb = self.trbs.lookup(msg.addr)
            # assert trb is not None, "trb must exist for this address"

            # if response sender is directory
            if msg.sender == DeviceType.Directory:
                if msg.type != responseType.Data:
                    raise ValueError("Directory should only reply with data")
                # if cache receives 'ack' from other caches before getting response from directory
                if msg.acks + trb.AckOutstanding == 0:
                    self.trigger(Event.DataDirNoAcks, msg.addr, entry)
                else:
                    self.trigger(Event.DataDirAcks, msg.addr, entry)
            
            # if sender is another cache
            else:
                if msg.type == responseType.Data:
                    self.trigger(Event.DataOwner, msg.addr, entry)
                elif msg.type == responseType.InvAck:
                    print(f"Got inv ack. {trb.AcksOutstanding} left")
                    if trb.AcksOutstanding == 1:
                        self.trigger(Event.LastInvAck, msg.addr, entry)
                    else:
                        self.trigger(Event.InvAck, msg.addr, entry)
            # if no messages to process, go to next message queue to process
            self.handle_forwards()

    def handle_forwards(self):
        channel = self.channels['forward_in']
        while channel.is_ready():
            msg = channel.receive()
            entry = self.cache.get_entry[msg.addr]
            trb = self.trbs[msg.addr]
            event_map = {
                requestType.GetS: Event.FwdGetS,
                requestType.GetM: Event.FwdGetM,
                requestType.Inv: Event.Inv,
                requestType.PutAck: Event.PutAck
            }
            event = event.get(msg.type, None)
            if event:
                self.trigger(event, msg.addr, entry)
            else:
                raise ValueError("Unexpected forward message type.")
            # if no messages to process, go to next message queue to process
            self.handle_mandatory()

    def handle_mandatory(self):
        channel = self.channels['mandatory_in']
        while channel.is_ready():
            msg = channel.receive()
            entry = self.cache.get_entry[msg.addr]
            trb = self.trbs[msg.addr]

            if not entry and not self.cache.is_cache_available(msg.addr):
                replacement_addr = self.probe_cache(msg.addr)
                replacement_entry = self.cache_entries[replacement_addr]
                self.trigger(Event.Replacement, replacement_addr, replacement_entry)
            else:
                event_map = {
                    'LD': Event.Load,
                    'ST': Event.Store,
                    'IFETCH': Event.Load  # Assuming IFETCH treated as a load for simplicity
                }
                event = event_map.get(msg.type, None)
                if event:
                    self.trigger(event, msg.addr, entry)
                else:
                    raise ValueError("Unexpected request type from processor")            

################      

    ##==========================================
    # STATE TRANSITION
    # process event
    def doTransition(self, event, message=None):
        print(f"Processing event: {event} in state: {self.cache_state}")
        ## state transition
        ## transition (cur_state, event, next_state) --> action
        if self.cache_state == State.I:
            if event == Event.Load:
                self.cache_state =  State.IS_D                
                # Actions to Define
                print("Transition to IS_D state: Load request received in Invalid state.")

        elif self.cache_state == State.IS_D :
            if event == Event.DataDirNoAcks:
                self.data_block = message.data_block
                self.cache_state = State.S
                print("Transition to Shared state: Data received with no ACKs required.")

        elif self.cache_state == State.IS_D :
            if event in [event.DataDirNoAcks, event.DataOwner]:
                self.cache_state = 'S'
                # Actions to define
            # elif event in [event.Load, event.Store, event.Replacement, event.Inv]:
                # stall

        elif self.cache_state == State.S:
            if event == Event.Store:
                self.cache_state = 'SM_AD'
                print("Transition to SM_AD state: Store request received in Shared state.")

        elif self.cache_state == State.SM_AD:
            if event == Event.InvAck:
                self.acks_outstanding -= 1
                print(f"Processed InvAck: {self.acks_outstanding} ACKs remaining.")

            if self.acks_outstanding == 0 and event == Event.LastInvAck:
                self.cache_state = State.M
                print("Transition to Modified state: Last InvAck received.")

        elif self.cache_state == State.M:
            if event == Event.Replacement:
                self.cache_state = State.I
                self.data_block = None
                print("Invalidated cache: Replacement occurred.")

    def receive_message(self, message):
        if message.msg_type == 'Data':
            self.process_event(Event.DataDirNoAcks, message)


    
    def is_available(self, addr):
        return len(self.entries) < self.capacity

    def probe(self, addr):
        # For simplicity, return a random address to be replaced
        return list(self.entries.keys())[0] if self.entries else None

    def get_cache_entry(self, addr):
        if addr in self.entries:
            return self.entries[addr]
        return None

    def allocate(self, addr, entry):
        if len(self.entries) >= self.capacity:
            self.deallocate(self.probe(addr))
        self.entries[addr] = entry

    def deallocate(self, addr):
        if addr in self.entries:
            del self.entries[addr]

# # Define how to handle incoming requests
# # not used
# def handle_incoming_requests(cache, queue):
#     if queue.is_ready():
#         request = queue.peek()
#         #request = queue.dequeue()
#         if request is None:
#             return
#         cache_entry = cache.get_cache_entry(request.line_address)
#         if cache_entry is None and not cache.is_available(request.line_address):
#             replacement_address = cache.probe(request.line_address)
#             cache.deallocate(replacement_address)
#             print(f"Evicted cache entry from {replacement_address} to make room")
#             cache_entry = CacheEntry()  # Create a new cache entry for simulation
#             cache.allocate(request.line_address, cache_entry)
#         else:
#             # Placeholder for event handling logic
#             print(f"Handling {request.request_type} for address {request.line_address}")
#             queue.dequeue()  # Remove the request from the queue after handling

# Cache Test
# Example of creating and using the Cache
cache_size = 10  # Define the size of the cache
cache = Cache(cache_size)
# Set some entries
cache.set_entry(1, 'Modified', True, True, [0x01, 0x02, 0x03, 0x04])
cache.set_entry(3, 'Shared', True, False, [0x05, 0x06, 0x07, 0x08])
# Print all cache contents
cache.print_contents()


# # test 1
# # Instantiate cache and queue
cache = Cache(10)
cache_ctrl = CacheController(cache)
# mandatory_queue = MandatoryQueue()
# # Simulate adding requests to the queue and handling them
# mandatory_queue.enqueue(MemRequest("0x1A", "Load"))
# mandatory_queue.enqueue(MemRequest("0x1A", "Store"))
# handle_incoming_requests(cache_ctrl, mandatory_queue)
# handle_incoming_requests(cache_ctrl, mandatory_queue)

# test2
sample_msg = ResponseMsg(
    addr="0x1A",
    response_type=responseType.Data,
    src="Node1",
    dest="Node2",
    data_block="100",
    ackCnt="2"
)

sample_msg2 = ResponseMsg(
    addr="0x1A",
    response_type=responseType.Data,
    src="Node1",
    dest="Node2",
    data_block="100",
    ackCnt="2"
)
cache_ctrl.channels['response_in'].send_message(sample_msg)
cache_ctrl.channels['response_in'].send_message(sample_msg2)
cache_ctrl.channels['response_in'].print_all_messages()


# # test 3

# cache_controller = CacheController()
# cache_controller.process_event(Event.Load)
# message = Message('Data', 'Directory', 'Cache', 'data_block_123')
# cache_controller.receive_message(message)
# cache_controller.process_event(Event.Store)
# cache_controller.process_event(Event.InvAck)
# cache_controller.process_event(Event.LastInvAck)