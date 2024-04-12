from enum import Enum, auto
import random
from collections import deque



# Define Cache States
class State(Enum):
    NP = auto()  # Not Present
    I = auto()  # Invalid
    S = auto()  # Shared
    E = auto()  # Exclusive
    M = auto()  # Modified
    IS = auto()  # Intermediate Shared
    IM = auto()  # Intermediate Modified
    SM = auto()  # Shared-to-Modified

# Define Events --> how is this different from messages?
# triggered by incoming messages
# msg_type
class msg_type(Enum):
#class Event(enum:)
    Load = auto()
    Store = auto()

    Inv = auto()
    
    Data = auto()
    Data_Exclusive = auto()
    
    Ack = auto()
class Event(Enum):
    Load = auto()
    Store = auto()
    Ifetch = auto()
    Inv = auto()
    Data = auto()
    Data_Exclusive = auto()
    Ack = auto()

# class Message:
#     def __init__(self, msg_type, sender, destination, data=None, acks=0):
#         self.msg_type = msg_type
#         self.sender = sender
#         self.destination = destination
#         self.data = data
#         self.acks = acks
#         # self.address = address

# Message class
class Message:
    def __init__(self, address, mtype):
        self.address = address
        self.mtype = mtype

# Cache Entry
class CacheEntry:
    def __init__(self, state=State.I):
        self.state = state
        self.dirty = False

## below is configruable
## same as cache.py
# class CacheEntry:
#     def __init__(self, address, state='I', valid=False, dirty=False, data_block=None):
#         self.address = address
#         self.state = state  # 'I' for Invalid, 'M' for Modified, 'S' for Shared, 'E' for Exclusive
#         self.valid = valid
#         self.dirty = dirty
#         self.data_block = data_block

#     def __str__(self):
#         return f"Addr: {self.address}, State: {self.state}, Valid: {self.valid}, Dirty: {self.dirty}"

# Virtual Channel
class VirtualChannel:
    def __init__(self):
        self.messages = deque()

    def send_message(self, message):
        self.messages.append(message)

    def receive_message(self):
        return self.messages.popleft() if self.messages else None

    def is_empty(self):
        return len(self.messages) == 0


class Cache:
    def __init__(self, size):
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


## cache controller model 
## --> this is the part that takes care of state transition and event handling

class CacheController:
    def __init__(self, cache):
        self.cache = cache
        #self.cache_state = CacheState.INVALID
        self.data_block = None
        self.acks_outstanding = 0
        self.channels = [VirtualChannel() for _ in range(3)]  # Example for 3 virtual channels
    ## below are called during transition ====
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
    def process_messages(self):
        for channel in self.channels:
            while not channel.is_empty():
                message = channel.receive_message()
                self.handle_message(message)

    def handle_message(self, message):
        if message.address not in self.cache:
            self.cache[message.address] = CacheEntry(state=State.NP)

        entry = self.cache[message.address]
        print(f"Handling message for {message.address}: Current State={entry.state}, Type={message.mtype}")

        if message.mtype in [Event.Load, Event.Store, Event.Ifetch]:
            self.do_transition(entry, message.mtype)

################
    def trigger(self, msg):
        if msg.msg_type == "Load":
            self.handle_load(msg.address)
        elif msg.msg_type == "Store":
            self.handle_store(msg.address)
        elif msg.msg_type == "Inv":
            self.cache.invalidate(msg.address)

    def access_cache(self, addr, event):
        if addr not in self.cache:
            self.cache[addr] = CacheEntry(state=State.NP)
        current_entry = self.cache[addr]
        print(f"Accessing {addr}: Current State={current_entry.state.name}, Event={event.name}")

        # Handle events based on current state
        if event == Event.Load or event == Event.Ifetch:
            if current_entry.state in [State.NP, State.I]:
                self.handle_miss(addr, current_entry)
            else:
                self.handle_hit(addr, current_entry)
        elif event == Event.Store:
            self.handle_store(addr, current_entry)

    def handle_miss(self, addr, entry):
        # Placeholder for miss handling logic
        print(f"Cache miss at {addr}")
        entry.state = random.choice([State.S, State.E])  # Randomized for example purposes

    def handle_hit(self, addr, entry):
        print(f"Cache hit at {addr}")

    def handle_load(self, address):
        entry = self.cache.get_entry(address)
        if entry and entry.valid:
            print(f"Load Hit: {entry}")
        else:
            print("Load Miss - Allocating and fetching data")
            # Simulate data fetch and update cache
            self.cache.set_entry(address, 'S', True, False, "data_fetched")
            print(f"Updated Cache Line: {self.cache.get_entry(address)}")

    def handle_store(self, address):
        entry = self.cache.get_entry(address)
        if entry and entry.state in ['M', 'E']:
            print(f"Store Hit: {entry}")
            entry.dirty = True
        else:
            print("Store Miss - Allocating and fetching data for modification")
            self.cache.set_entry(address, 'M', True, True, "data_modified")
            print(f"Updated Cache Line: {self.cache.get_entry(address)}")            

    ##==========================================
    def process_event(self, event, message=None):
        print(f"Processing event: {event} in state: {self.cache_state}")
        ## state transition
        ## transition (cur_state, event, next_state) --> action
        if self.cache_state == CacheState.INVALID:
            if event == CoherenceEvent.Load:
                # below are actions
                self.cache_state = 'IS_D'                
                allocateCacheBlock()
                allocateTBE()
                sendGetS()
                popMandatoryQueue()
                print("Transition to IS_D state: Load request received in Invalid state.")

        elif self.cache_state == 'IS_D':
            if event == CoherenceEvent.DataDirNoAcks:
                self.data_block = message.data_block
                self.cache_state = CacheState.SHARED
                print("Transition to Shared state: Data received with no ACKs required.")

        elif self.cache_state == 'IS_D':
            if event in [DataDirNoAcks, DataOwner]:
                self.cache_state = 'S'
                writeDataToCache
                deallocateTBE
                externalLoadHit
                popResponseQueue
            elif event in [Load, Store, Replacement, Inv]:
                stall

        elif self.cache_state == CacheState.SHARED:
            if event == CoherenceEvent.Store:
                self.cache_state = 'SM_AD'
                print("Transition to SM_AD state: Store request received in Shared state.")

        elif self.cache_state == 'SM_AD':
            if event == CoherenceEvent.InvAck:
                self.acks_outstanding -= 1
                print(f"Processed InvAck: {self.acks_outstanding} ACKs remaining.")

            if self.acks_outstanding == 0 and event == CoherenceEvent.LastInvAck:
                self.cache_state = CacheState.MODIFIED
                print("Transition to Modified state: Last InvAck received.")

        elif self.cache_state == CacheState.MODIFIED:
            if event == CoherenceEvent.Replacement:
                self.cache_state = CacheState.INVALID
                self.data_block = None
                print("Invalidated cache: Replacement occurred.")

    def receive_message(self, message):
        if message.msg_type == 'Data':
            self.process_event(CoherenceEvent.DataDirNoAcks, message)

    def do_transition(self, entry, event):
        # Define state transitions here
        if event == Event.Load:
            if entry.state in [State.NP, State.I]:
                entry.state = State.S
            elif entry.state == State.M:
                entry.state = State.M  # No transition needed for M state on Load
            print(f"Transitioned to {entry.state}")

        elif event == Event.Store:
            if entry.state in [State.S]:
                entry.state = State.M
            elif entry.state in [State.I, State.NP]:
                entry.state = State.M
            print(f"Transitioned to {entry.state}")


# test 1
cache = Cache(100)
controller = CacheController(cache)
controller.channels[0].send_message(Message("0x1A", Event.Load))
controller.channels[1].send_message(Message("0x1B", Event.Store))
controller.process_messages()

# # test 2

# cache_controller = CacheController()
# cache_controller.process_event(CoherenceEvent.Load)
# message = Message('Data', 'Directory', 'Cache', 'data_block_123')
# cache_controller.receive_message(message)
# cache_controller.process_event(CoherenceEvent.Store)
# cache_controller.process_event(CoherenceEvent.InvAck)
# cache_controller.process_event(CoherenceEvent.LastInvAck)





