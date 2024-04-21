from enum import Enum, auto
from collections import deque
import random
import time
import math
import os
from itertools import islice


from utility.global_utility import Msg as Message
from utility.global_utility import msg_type as MessageType
from utility.cpu_utility import *

# from global_utility import Msg as Message
# from global_utility import msg_type as MessageType
# from global_utility import *
# from parser import Parser
class Parser:

    # assume 3 CPU limit
    def parse_device_type(self, deviceID):
        device_mapping = {
            Node.CPU0: 'cpu_0' ,
            Node.CPU1: 'cpu_1' ,
            Node.CPU2: 'cpu_2' ,
            Node.CPU3: 'cpu_3' 
        }
        if deviceID in device_mapping:
            return device_mapping[deviceID]


    # Read 1 Trace Line and 
    # Return Corresponding Messages
    def parse_trace_line(self, line, barriers):
        # print(line)
        parts = line.split()
        if not parts:
            raise ValueError("Empty line or formatting error.")
        operation = parts[0]        
        # LD/ST
        # if operation in ['ld' or 'st']:
        if operation == 'ld' or operation == 'st':  
            if len(parts) < 2:
                raise ValueError(f"Insufficient arguments for {operation.upper()}.")
            address = int(parts[1])
            # device_type = parse_device_type(parts[2])
            #cpu_id = parts[2]
            #return self.MemoryRequest(MessageType.LD if operation == 'ld' else MessageType.ST, address)
            return Message(msg_type = MessageType.Load if operation == 'ld' else MessageType.Store, addr = address)
        # Barrier
        elif operation.startswith('Barrier'):
            if len(parts) < 3:
                raise ValueError("Insufficient arguments for BARRIER.")
            barrier_id = int(parts[1]) # barrier ID
            barrier_count = int(parts[2]) # barrier count
            
            #enque barrier 
            barriers.append({barrier_id: barrier_count})
            return Message(msg_type = MessageType.Barrier)

        else:
            raise ValueError(f"Unsupported operation: {operation}")


    # Read the memory trace file
    # and enqueue to the buffer
    def process_trace_file(self, buffer, deviceID, barriers):
        
        filepath = self.get_file_path(deviceID)
        
        with open(filepath, 'r') as file:
            lines = file.readlines()

        i = 0
        while i < len(lines):
        #  for _ in range(3): # process 3 operations every tick
            if i >= len(lines):
                break
            try:
                request = self.parse_trace_line(lines[i].strip(), barriers) # remove whitespace
                # currently assume buffer is unlimited for instrution queue
                # if not buffer.send_message(request): # If the buffer is full 
                #     break
                buffer.send_message(request) 
                i += 1
            except ValueError as e:
                print(f"Error parsing line: {e}")
                i += 1 

        print(i)
    
    def get_file_path(self, deviceID):
        # need to file_name for device - given from cache controller Device Type
        device_name = self.parse_device_type(deviceID)
        file_name = device_name+'.txt'
        print(file_name)
        # file_name = 'memory_trace_toy.txt'

        # get file path
        src_directory = os.getcwd()
        parent_directory = os.path.dirname(src_directory)
        memory_traces_directory = os.path.join(parent_directory, 'memory_traces')
        file_path = os.path.join(memory_traces_directory, file_name)
        return file_path

# Virtual Channel
# Message Buffer
class VirtualChannel:
    def __init__(self):
        self.messages = deque()
        self.transaction_ongoing = False

    def __str__(self):
        return self.content

    def is_ready(self):
        # return bool(self.queue)
        return bool(self.messages)

    def send_message(self, message): #enque
        self.messages.append(message)

    #def receive_message(self):
    def dequeue(self):    
        return self.messages.popleft() if self.messages else None

    def is_empty(self):
        return len(self.messages) == 0

    def peek(self): #check the head point value of queue
        return self.messages[0] if self.messages else None
    
    # def print_all_messages(self):
    #     if self.is_empty():
    #         print("VC is empty")
    #     print("==========================")    
    #     for msg in self.messages:
    #         print("VC CONTENTS")
    #         Message.print_msg(msg)
    #     print(f"transaction_ongoing: {self.transaction_ongoing}")    
    #     print("==========================")

    # first 10 messages from the deque
    def print_all_messages(self):
        if self.is_empty():
            print("VC is empty")
        print("==========================")
        for msg in islice(self.messages, 10):
            print("VC CONTENTS")
            Message.print_msg(msg)  
        print(f"transaction_ongoing: {self.transaction_ongoing}")
        print("==========================")

# Define Cache States
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
    DataDir = auto()

    # Responses from other caches
    DataOwner = auto()


# transaction buffer entry
class tbe:
    def __init__(self, state):
        self.state = state #state of cache line
        #self.ackCnt
    def __repr__(self):
        return (f"tr : State={self.state}")

# transient request buffer
# transaction buffer
class tbeTable:
    def __init__(self):
        self.entries = {}

    #def isValid(self,tbe)

    def lookup(self, addr):
        if self.is_present(addr):
            print("TBE entry not found.")
        else:
            return self.entries.get(addr, None)

    def allocate(self, addr, cache_entry):
        # Allocate a new tbe entry for the given address. 
        if addr not in self.entries:
            self.entries[addr] = tbe(cache_entry.state)
        return self.entries[addr]

    def deallocate(self, addr):
        # Remove the tbe associated with the given address 
        if addr in self.entries:
            del self.entries[addr]

    def is_present(self, addr):
        # Check if there's a tbe allocated for the given address
        return addr in self.entries

## below is configruable
## same as cache.py
class CacheEntry:
    def __init__(self, address, state=State.I, isValid=False, isDirty=False, data_block=None):
        # cache line metadata
        self.address = address & ~0x3F  # base address for the cache line --> Mask out the lower 6 bits for 64-byte alignment. given as hex value ex) 0x211
        self.state = state  # Cache line state for coherency
        self.isValid = isValid
        self.isDirty = isDirty
        # data_block --> [byte1.. byte16] # list of 16byes (currently fixed to 64 bytes per line size but can be configurable)
        #data_block.extend([None] * (16 - len(data_block)))
        self.data_block = data_block if data_block else [None] * 16  
        self.LRU = -1  # will update later
        # self.accesslvl # read-only? write-only?

        # word granularity
        # flag

    def __str__(self):
        return f"Addr: {hex(self.address)}, State: {self.state}, isValid: {self.isValid}, data_block: {self.data_block}"

# Used for only modifying inside cache
class Cache: #currently assumes fully-associative
    def __init__(self, size):
        # collection of cache entry
        # dictionary with key: ADDR / value : CacheEntry
        self.size = size
        self.entries = {i * 0x40: CacheEntry(i * 0x40) for i in range(size)}  # Assume each address is aligned to 64 bytes (0x40)
        self.current_max_LRU = 0  # Track the highest LRU value

    def get_entry(self, address):
        base_address = address & ~0x3F
        return self.entries.get(base_address)

    def set_entry(self, cache_entry):
        base_address = cache_entry.address & ~0x3F  # Ensure the address is aligned
        if self.is_cache_available() and base_address not in self.entries:
            # Cache is full and the address is not in the cache, we need to evict an entry
            self.evict_cache_entry()
        self.entries[base_address] = cache_entry
        self.setMRU(cache_entry)
        print(f"Cache entry at {hex(base_address)} has been set or updated.")

    def invalidate(self, address):
        base_address = address & ~0x3F
        if base_address in self.entries:
            self.entries[base_address].state = 'I'
            self.entries[base_address].isValid = False
            print(f"Invalidated Cache Line: {self.entries[base_address]}")

    def is_cache_available(self):
        # Check if any cache entry is available (i.e., invalid or not in use)
        for entry in self.entries.values():
            if not entry.isValid:
                return True  # Found an available cache line
        return False  # No available cache line, all are valid and in use

    def evict_cache_entry(self):
        # Evict the least recently used cache entry
        lru_address = self.getReplacementAddr()
        if lru_address:
            evicted_entry = self.entries.pop(lru_address)
            print(f"Evicted Cache Line: {hex(evicted_entry.address)} with state {evicted_entry.state}")


    def setMRU(self, cache_entry):
            self.current_max_LRU += 1
            cache_entry.LRU = self.current_max_LRU  # Update the LRU to the highest current value, marking it most recently used

    def getReplacementAddr(self):
        # return replacement address
        # currently just randomly select and return an address from the cache
        if self.entries:
            return random.choice(list(self.entries.keys()))  
        else:
            return None  

    def print_contents(self):
        # Print each entry's details
        print("=========================")
        print("Printing each cache entry")
        for entry in self.entries.values():
            print(entry)
        print("=========================")

## Cache Controller Model 
## --> Handles Coherence Protocol
class CacheController:
    
    def __init__(self, size, deviceID=Node.CPU0): 
        self.cache = Cache(size)
        self.deviceID = deviceID 
        self.dirID = Node.LLC #device.getDirID()
        self.tbes = tbeTable()
        self.channels = {
            'response_in'   : VirtualChannel(),
            'request_in'    : VirtualChannel(),
            'instruction_in'  : VirtualChannel(),
            'response_out'  : VirtualChannel(),
            'request_out'   : VirtualChannel()
        }
        self.acks_outstanding = 0

        # Barrier Queue
        # key           value
        # barrier id : barrer count
        self.barriers = deque()
        self.encounter_barrier = None
        self.barrier_count = 0
        self.finish = False


## EXECUTE MEMORY 
    # config cache
    # parse memory trace
    def setCPU(self):
        parser = Parser()
        parser.process_trace_file(self.channels['instruction_in'], self.deviceID, self.barriers)
        
    def CPU_run(self):
        # Initialize a flag to check if all channels are busy
        all_busy = True

        # Insturction Queue should be filled
        # Parse the memory trace file
        # And fill up the instruction queue

        # List all channels in order of priority
        channels = ['response_in', 'request_in', 'instruction_in']
        for channel_key in channels:
            channel = self.channels[channel_key]
            if not channel.is_empty():
                # if channel.transaction_ongoing:
                #     print(f"Transaction is currently ongoing in {channel_key}. Skipping.")
                #     continue  # Skip to the next channel
                all_busy = False  # At least one channel is ready to be processed
                if channel_key == 'response_in':
                    if not self.channels[channel_key].transaction_ongoing:
                        self.handle_responses()
                    else:
                        print("Transaction ongoing in response_in channel.")
                elif channel_key == 'request_in'and not self.channels[channel_key].transaction_ongoing:
                    self.handle_forwards()
                elif channel_key == 'instruction_in':
                    if self.encounter_barrier is not None:
                        self.encounter_barrier = None #reset barrier flag
                        self.handle_instruction()
                    else:
                        self.handle_instruction()
            else:
                if channel_key == 'instruction_in':
                    print(f"{self.deviceID} run end")
                    self.finish = True 
                    #exit()
                    return None #At top level if None received, it indicates the program stopped running
                print(f"{channel_key} is empty. Moving to the next channel.")
        if all_busy:
            print("All channels are busy. Stalling for this cycle.")



## MESSAGE HANDLE
## need to enque based on messagetype
    # dequeue from message buffer (at every tick) and trigger events
    def handle_responses(self):
        channel = self.channels['response_in']
        # Check the head of the queue
        msg = channel.peek()  
        channel.transaction_ongoing = True # set flag to indicate transaction is ongoing
        entry = self.cache.get_entry(msg.addr)
        tbe = self.tbes.lookup(msg.addr) #tbe entry should already be allocated since this is response

        # if response sender is directory
        if msg.src is self.dirID:
            if msg.msg_type is MessageType.PutAck:
                self.trigger(Event.PutAck, msg.addr, entry, msg)   
            elif msg.msg_type is MessageType.DataDir:
                self.trigger(Event.DataDir, msg.addr, entry, msg)
            else:
                raise ValueError("Directory should only reply with data")
        # if sender is another cache
        else:
            if msg.msg_type is MessageType.DataOwner:
                self.trigger(Event.DataOwner, msg.addr, entry, msg)


    def handle_forwards(self):
        channel = self.channels['request_in']
        # Check the head of the queue
        msg = channel.peek()  
        channel.transaction_ongoing = True # set flag to indicate transaction is ongoing
        entry = self.cache.get_entry(msg.addr)
        #tbe = self.tbes.entries[msg.addr]
        tbe = self.tbes.lookup(msg.addr)
        
        if msg.msg_type is MessageType.FwdGetS:
            assert entry is not None, "FwdGetS must access valid entry"
            self.trigger(Event.FwdGetS, msg.addr, entry, msg)
        elif msg.msg_type is MessageType.FwdGetM:
            self.trigger(Event.FwdGetM, msg.addr, entry, msg)
        elif msg.msg_type is MessageType.Inv:
            self.trigger(Event.Inv, msg.addr, entry, msg)
        else:
            raise ValueError("Unexpected forward message type.")


    def handle_instruction(self):
        channel = self.channels['instruction_in']
        # Check the head of the queue
        msg = channel.peek()
        msg.print_msg()
        # channel.transaction_ongoing = True # set flag to indicate transaction is ongoing
        
        # first check for barrier
        # BARRIER
        # while being stuck, need to keep track of other processor's barrier encounter
        if msg.msg_type is MessageType.Barrier:
            # should be popped once barrier is cleared, until then, reference for count
            #barrier = self.barriers.popleft() 
            barrier = self.barriers[0]
            barrier_id = next(iter(barrier)) 
            barrier_count = barrier[barrier_id]
            print(f"running instruction : current barrier count= {barrier_count}, barrier count: {self.barrier_count}")

            if self.barrier_count==0: # first encounter barrier
                self.encounter_barrier = barrier_id # set flag to notify LLC
                self.barrier_count = barrier_count - 1 # exclude current running CPU
            elif barrier_count==0: #all CPU finish encountering barrier
                self.barriers.popleft() #pop head
                barrier_id = next(iter(barrier)) 
                self.barrier_count = barrier[barrier_id]  #reset flag count
                channel.dequeue() # dequeue instruction
                channel.transaction_ongoing = False # go to next inst
            # in next tick we can still process resp_in 
            # but will have to wait until barrier is cleared
        else :
            if channel.transaction_ongoing is True:
                print("transation in inst queue onging")
            else:
                entry = self.cache.get_entry(msg.addr) 
                #tbe = self.tbes.entries[msg.addr]

                # if miss and cache full --> first thing to check to handle to Replacement event
                #if not entry.isValid and not self.cache.is_cache_available(msg.addr):
                if not entry.isValid and not self.cache.is_cache_available():
                # if entry.state is State.I and not self.cache.is_cache_available(msg.addr):
                    # get replacement address from cache
                    replacement_addr = self.cache.getReplacementAddr()
                    replacement_entry = self.cache.get_entry(replacement_addr)
                    self.trigger(Event.Replacement, replacement_addr, replacement_entry, msg)

                else: # now we assume entry is valid
                    if msg.msg_type is MessageType.Load:
                        channel.transaction_ongoing = True 
                        self.trigger(Event.Load, msg.addr, entry, msg)
                    elif msg.msg_type is MessageType.Store:
                        channel.transaction_ongoing = True 
                        self.trigger(Event.Store, msg.addr, entry, msg)
                    else:
                        raise ValueError("Unexpected request type from processor")   

## EVENT TRIGGER    
    # trigger will cause state transition and will result in action
    # --> queue the output message
    # call do_trasition here
    def trigger(self, event, addr, cache_entry, message = None, tbe=None):
        # Event handling logic to be implemented

        print(f"Triggered {event.name} for address {addr}")
        self.doTransition(event, addr, cache_entry, message, tbe)
        
        

## ACTIONS
    ## below are called during do_transition
    
    # state information during trasaction
    def allocateTBE(self, addr, cache_entry):
        self.tbes.allocate(addr, cache_entry)
        print("TBE allocated for transition.")

    def deallocateTBE(self, addr):
        self.tbes.deallocate(addr)
        print("TBE deallocated.")

    # responses to CPU requests
    def loadHit(self, cache_entry):
        # assert(cache_entry.isValid)
        self.cache.setMRU(cache_entry)
        # send the data back to CPU
        print("Load hit processed.")

    def storeHit(self, cache_entry):
        self.cache.setMRU(cache_entry)
        # notify CPU? performance measure?
        print("Store hit processed.")
    
    def loadMiss(self):

        print("Load miss processed.")

    def storeMiss(self):

        print("Store miss processed.")

    # Send request to directory
    def sendGetS(self, addr):
        out_msg = Message(msg_type = MessageType.GetS, addr = addr, src = self.deviceID, dst = self.dirID) 
        self.channels["request_out"].send_message(out_msg)
        out_msg.print_msg()
        print("GetS message sent for read access.")

    def sendGetM(self, addr):
        out_msg = Message(msg_type = MessageType.GetM, addr = addr, src = self.deviceID, dst = self.dirID)
        self.channels["request_out"].send_message(out_msg)
        out_msg.print_msg()
        print("GetM message sent to fetch exclusive access.")

    def sendPutM(self, addr, cache_entry):
        out_msg = Message(msg_type = MessageType.PutM, addr = addr, src = self.deviceID, dst = self.dirID)
        self.channels["request_out"].send_message(out_msg)
        out_msg.print_msg()
        print("PutM message sent to evict block from modified state.")

    # Cache
    def allocateCacheBlock(self, entry):
        # assert isValid
        # asert cache is not full
        self.cache.set_entry(entry)  

    def deallocateCacheBlock(self, addr):
        self.cache.invalidate(addr)
        print("Cache block deallocated.")  

    def writeDataToCache(self, message, cache_entry):
        #cache_entry.data_block = message.data_block
        self.cache.set_entry(cache_entry)
        print("===========================================")
        print(f"Data written to cache block at {cache_entry.addr}")
        print("=================================================")

    def sendCacheDataToReq(self, message):
        out_msg = Message(msg_type = MessageType.DataOwner, addr = message.addr, src=self.deviceID, dst = message.fwd_dst) #destination node?
        self.channels["response_out"].send_message(out_msg)  
        print("=========Cache data sent to requestor=============")
        out_msg.print_msg()  
        print("=================================================")
    
    def sendCacheDataToDir(self, message):
        out_msg = Message(msg_type = MessageType.Data, addr = message.addr, src=self.deviceID, dst = self.dirID)
        self.channels["response_out"].send_message(out_msg)
        print("=========Cache data sent to directory.=============") 
        out_msg.print_msg()
        print("=================================================")

    def sendInvAcktoDir(self, addr):
        out_msg = Message(msg_type = MessageType.InvAck, addr = addr, src=self.deviceID, dst = self.dirID)
        self.channels["response_out"].send_message(out_msg)
        out_msg.print_msg()
        print("Invalidation Ack sent to requestor.")


    # Message Buffer Management
    def popInstructionQueue(self):
        self.channels["instruction_in"].dequeue()
        self.channels["instruction_in"].transaction_ongoing = False
        print("Instruction queue popped for processing.")
        return True

    def popResponseQueue(self):
        self.channels["response_in"].dequeue()
        self.channels["response_in"].transaction_ongoing = False
        print("Response queue popped for processing.")

    def popRequestQueue(self):
        self.channels["request_in"].dequeue()
        self.channels["request_in"].transaction_ongoing = False
        print("Request queue popped for processing.")
    
    def stall(self):
        print("Stalling: Unsupported event in current state.")
        return None

## STATE TRANSITION

    # def getState(self, tbe, cache_entry, addr):
    #     if is_valid(tbe):
    #         return tbe.


    # process event and do state transition
    def doTransition(self, event, addr, cache_entry, message=None, tbe=None):
        print(f"Processing event: {event} in state: {cache_entry.state}")

        #print(f"Type of cache_entry.state: {type(cache_entry.state)}, Type of event: {type(event)}")

        ## define state transition
        ## transition (cur_state, event, next_state) --> action
        if cache_entry.state is State.I:
            if event == Event.Load:
                cache_entry.state =  State.IS_D
                print(cache_entry)
                self.allocateCacheBlock(cache_entry) # allocating cache entry if miss returns
                self.allocateTBE(addr, cache_entry)
                self.sendGetS(addr)
                print("Transition from I to IS_D state: Load request received in Invalid state.")
            elif event is Event.Store:
                cache_entry.state =  State.IM_D 
                self.allocateCacheBlock(cache_entry) # allocating cache entry if miss returns
                #cache_entry.set_entry(cache_entry) wrong
                self.allocateTBE(addr, cache_entry)
                self.sendGetM(addr)
                print("Transition from I to IM_D state: Store request received in Invalid state.")
            elif event is Event.Inv:
                self.sendInvAcktoDir(addr)
                self.popRequestQueue()           
            else:
                raise ValueError(f"Unexpected Message in addr {addr}. Current state {cache_entry.state}")     

        elif cache_entry.state in [State.IS_D, State.IM_D] :
            if event in [Event.Load, Event.Store, Event.Replacement]:
                self.stall()
            elif event is Event.Inv:
                self.sendInvAcktoDir(addr)
                self.popRequestQueue()                

        elif cache_entry.state is State.IS_D :
            if event is Event.DataDir:
                cache_entry.state = State.S
                self.writeDataToCache(message, cache_entry) # don't need now
                self.deallocateTBE(addr)
                self.loadMiss()
                self.popInstructionQueue()  
                print("Transition to Shared state: Data received from LLC.")
            else:
                raise ValueError(f"Unexpected Message in addr {addr}. Current state {cache_entry.state}")

        elif cache_entry.state is State.IM_D:
            if event in [Event.DataDir, Event.DataOwner]:
                print("check IM_D")
                cache_entry.state = State.M
                self.deallocateTBE(addr)
                self.storeMiss()
                self.popInstructionQueue()
                self.popResponseQueue()    
                print("Transition to M state: Data received")
            else:
                raise ValueError(f"Unexpected Message in addr {addr}. Current state {cache_entry.state}")

        elif cache_entry.state is State.S:
            if event is Event.Load:
                self.loadHit(cache_entry)
                self.popInstructionQueue()            
            elif event is Event.Store:
                cache_entry.state = State.SM_D
                self.allocateTBE(addr, cache_entry)
                self.sendGetM(addr)
                print("Transition to SM_AD state: Store request received in Shared state.")
            # no explicit PutS message for replacement, instead need to respond to all Ack
            # we are doing a state transition for replacement address
            # original address with memory request transitions to 
            elif event is Event.Replacement:
                cache_entry.state = State.I               
            elif event is Event.Inv:
                cache_entry.state = State.IM_D
                self.sendInvAcktoDir(addr)
                self.popRequestQueue() #response queue
                print("Transition to I state: Invalidation request received in Shared state.")
            else:
                raise ValueError(f"Unexpected Message in addr {addr}. Current state {cache_entry.state}")
        
        elif cache_entry.state is State.SM_D:
            if event is Event.Load:
                self.loadHit(cache_entry)
                self.popInstructionQueue()    
                print("Processed Load event in SM_D state.")                           
            elif event in [Event.Store, Event.Replacement, Event.FwdGetS, Event.FwdGetM]:
                self.stall()           
            elif event is Event.Inv:
                cache_entry.state = State.IM_D
                self.sendInvAcktoDir(addr)
                self.popRequestQueue()     
            elif event is Event.DataDir:  
                cache_entry.state = State.M
                self.deallocateTBE(addr)
                self.storeMiss()
                self.popInstructionQueue()
                self.popResponseQueue()    
                print("Transition to M state: Ownership received")
            else:
                raise ValueError(f"Unexpected Message in addr {addr}. Current state {cache_entry.state}")

        elif cache_entry.state is State.M:
            if event is Event.Load:
                self.loadHit(cache_entry)
                self.popInstructionQueue()    
                print("Processed Load event in M state.")                
            elif event is Event.Store:
                self.storeHit(cache_entry)
                self.popInstructionQueue()
                print("Processed Store event in Modified state.")
            elif event is Event.Replacement:
                cache_entry.state = State.MI_A
                self.sendPutM(addr, cache_entry)
                print("Invalidated cache: Replacement occurred.")                
            elif event is Event.FwdGetS:
                cache_entry.state = State.S
                self.sendCacheDataToDir(message)
                self.popRequestQueue()
                print("Processing FwdGetS event in Modified state.")
            elif event is Event.FwdGetM:
                cache_entry.state = State.I
                print("Processing FwdGetM event in Modified state, transition to I")
                self.sendCacheDataToReq(message)
                self.popRequestQueue()
            elif event is Event.Inv:
                self.sendInvAcktoDir(addr)   
                self.popRequestQueue()      
                print("Processed Inv event in Modified state")  
            else:
                raise ValueError(f"Unexpected Message in addr {addr}. Current state {cache_entry.state}")                     

        elif cache_entry.state in [State.MI_A, State.SI_A, State.II_A]:
            if event in [Event.Load, Event.Store, Event.Replacement]:
                self.stall()
            elif event is Event.PutAck:
                cache_entry.state = State.I
                print("Transition to I state: PutAck received.")
                self.deallocateCacheBlock(addr)
                self.popRequestQueue()        
    
        elif cache_entry.state is State.MI_A:
            if event is Event.FwdGetS:
                cache_entry.state = State.SI_A
                print("Transition to SI_A state: Forwarding cache data.")
                self.sendCacheDataToDir(message)
                self.popRequestQueue()
            elif event is Event.FwdGetM:
                cache_entry.state = State.II_A
                print("Transition to II_A state: Forwarding cache data.")
                self.sendCacheDataToReq(message)
                self.popRequestQueue()
            elif event is Event.Inv:
                self.sendInvAcktoDir(addr)       
                self.popRequestQueue()    
            else:
                raise ValueError(f"Unexpected Message in addr {addr}. Current state {cache_entry.state}")                         

        elif cache_entry.state is State.SI_A:
            if event is Event.Inv:
                cache_entry.state = State.II_A
                print("Transition to II_A state: Invalidating cache block.")
                self.sendInvAcktoDir(addr)
                self.popRequestQueue()
            else:
                raise ValueError(f"Unexpected Message in addr {addr}. Current state {cache_entry.state}")

        elif cache_entry.state is State.II_A:
            if event is Event.Inv:
                self.sendInvAcktoDir(addr)   
                self.popRequestQueue() 
            else:
                raise ValueError(f"Unexpected Message in addr {addr}. Current state {cache_entry.state}")

## BARRIER HANDLING
    def print_barriers(self):
        # Prints all barriers and their counts
        if not self.barriers:
            print("No barriers to display.")
        else:
            print(f"=={self.deviceID} Current bBarriers and Their Counts==")
            for barrier in self.barriers:
                for barrier_id, count in barrier.items():
                    print(f"Barrier ID: {barrier_id}, Count: {count}")
    
    def get_barrier(self): # set flag for encountered barrier ID
        return self.encounter_barrier
    
    # CPU_barrier has to be 'string' type currently because barrier is parsed from a file
    def update_barrier(self, CPU_barrier): # input encountered barrier ID, this function should update barrier cnt 
        # currently assume id in order ex) 0 1 3 5

        # find a matching barrier, if none just pass
        for barrier_dict in self.barriers:
            if CPU_barrier in barrier_dict:
                barrier_dict[CPU_barrier] -= 1        
                    # if the count reaches zero
                    # end of barrier
                    # pop should be done in CPU side
                    # if barrier_dict[CPU_barrier] <= 0:
                    #     self.barriers.dequeue() #pop head
                
                break  # Exit the loop after updating the barrier
        else:
            print(f"No barrier found with ID {CPU_barrier}")


## OUTPUT INTERFACE

    def receive_rep_msg(self, message):
        self.channels['response_in'].send_message(message)
        print(f"Received and enqueued to response_in: {message}")

    def receive_req_msg(self, message):
        self.channels['request_in'].send_message(message)
        print(f"Received and enqueued to request_in: {message}")
    
    def get_generated_msg(self):
        if not self.channels['response_out'].is_empty():
            self.last_peeked_channel = 'response_out'
            return self.channels['response_out'].peek()
        elif not self.channels['request_out'].is_empty():
            self.last_peeked_channel = 'request_out'
            return self.channels['request_out'].peek()
        else:
            self.last_peeked_channel = None
            return None

    def take_generated_msg(self):
        if self.last_peeked_channel and not self.channels[self.last_peeked_channel].is_empty():
            return self.channels[self.last_peeked_channel].dequeue()
        return None
    
    def is_finish(self):
        return self.finish
    






