from enum import Enum, auto
from collections import deque
import random
import time
import math

from global_utility import Msg as Message
from global_utility import msg_type as MessageType
from global_utility import *
from parser import Parser


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
    
    def print_all_messages(self):
        if self.is_empty():
            print("VC is empty")
        print("==========================")    
        for msg in self.messages:
            print("VC CONTENTS")
            #print(msg)  # This will invoke __str__ method of Message object
            Message.print_msg(msg)
        print(f"transaction_ongoing: {self.transaction_ongoing}")    
        print("==========================")

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

# transaction buffer entry
class tbe:
    def __init__(self, state, data_block, acks_outstanding):
        self.state = state #state of cache line
        self.data_block = data_block #data for cache line 
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
        if self.is_present(addr):
            print("TBE entry not found.")
        else:
            return self.entries.get(addr, None)

    def allocate(self, addr, tbe):
        # Allocate a new tbe entry for the given address. 
        if addr not in self.entries:
            self.entries[addr] = tbe
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
    def __init__(self, address, state='I', isValid=False, isDirty=False, data_block=[]):
        # cache line metadata
        self.address = address & ~0x3F  # base address for the cache line --> Mask out the lower 6 bits for 64-byte alignment. given as hex value ex) 0x211
        self.state = state  # Cache line state for coherency
        self.isValid = isValid
        self.isDirty = isDirty
        # data_block --> [byte1.. byte16] # list of 16byes (currently fixed to 64 bytes per line size but can be configurable)
        data_block.extend([None] * (16 - len(data_block)))
        self.data_block = data_block
        self.LRU = -1  # will update later
        # self.accesslvl # read-only? write-only?

        # word granularity
        # flag

    def __str__(self):
        return f"Addr: {hex(self.address)}, State: {self.state}, isValid: {self.isValid}, data_block: {self.data_block}"


class Cache:
    def __init__(self, size):
        # collection of cache entry
        # dictionary with key: ADDR / value : CacheEntry
        self.size = size
        self.set_size = 2  # set size, change if wanted
        self.set_entries = int(self.size / self.set_size)
        self.entries = [{} for _ in range(self.set_entries)]  # Assume each address is aligned to 64 bytes (0x40)
        self.usage_order = [deque() for _ in range(self.set_entries)]
        self.set_mask = (1 << int(math.log(self.set_size, 2))) - 1
        self.tag_mask = ~(self.set_mask | 0x3F)

    def get_entry(self, address):
        base_address = address & self.tag_mask
        set_num = (address >> 6) & self.set_mask
        return self.entries[set_num].get(base_address)

    def set_entry(self, cache_entry):
        base_address = cache_entry.address & self.tag_mask  # Ensure the address is aligned
        set_num = (cache_entry.address >> 6) & self.set_mask  # Ensure the address is aligned
        if not self.is_cache_available(set_num) and base_address not in self.entries[set_num]:
            # Cache is full and the address is not in the cache, we need to evict an entry
            self.evict_cache_entry(set_num)
        if base_address in self.entries[set_num]:
            self.usage_order[set_num].remove(base_address)
        self.usage_order[set_num].append(base_address)
        self.entries[set_num][base_address] = cache_entry
        print(f"Cache entry in set {set_num} with tag {hex(cache_entry.address)} has been set or updated.")

    def invalidate(self, address):
        base_address = address & self.tag_mask
        set_num = (address >> 6) & self.set_mask
        if base_address in self.entries[set_num]:
            del self.entries[set_num][base_address]
            self.usage_order[set_num].remove(base_address)
            print(f"Invalidated Cache Line in set {set_num}: {self.entries[set_num][base_address]}")

    def is_cache_available(self, set):
        return len(self.entries[set]) < self.set_size

    def evict_cache_entry(self, set):
        # Evict the least recently used cache entry
        if self.entries:
            evicted_entry = self.entries[set].pop(self.usage_order[set].popleft())
            print(f"Evicted Cache Line in set {set}: {hex(evicted_entry.address)} with state {evicted_entry.state}")

    def print_contents(self):
        # Print each entry's details
        print("=========================")
        print("Printing each cache entry")
        for i in range(self.set_entries):
            for entry in self.entries[i].values():
                print(entry)
        print("=========================")

class MemRequest:
    def __init__(self, line_address, request_type):
        self.line_address = line_address
        self.request_type = request_type  # 'Load', 'Store' 


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
            'forward_in'    : VirtualChannel(),
            'instruction_in'  : VirtualChannel(),
            'response_out'  : VirtualChannel(),
            'request_out'   : VirtualChannel()
        }
        self.acks_outstanding = 0

        # Barrier Data
        # key           value
        # barrier id : barrer count
        self.barriers = {}


## EXEUTE MEMORY 
    # config cache
    # parse memory trace
    def setCPU(self):
        parser = Parser()
        parser.process_trace_file(self.channels['instruction_in'], self.deviceID, self.barriers)
        
    def runCPU(self):
        # Initialize a flag to check if all channels are busy
        all_busy = True

        # Insturction Queue should be filled
        # Parse the memory trace file
        # And fill up the instruction queue

        # List all channels in order of priority
        channels = ['response_in', 'forward_in', 'instruction_in']
        for channel_key in channels:
            channel = self.channels[channel_key]
            if not channel.is_empty():
                if channel.transaction_ongoing:
                    print(f"Transaction is currently ongoing in {channel_key}. Skipping.")
                    continue  # Skip to the next channel
                all_busy = False  # At least one channel is ready to be processed
                if channel_key == 'response_in':
                    self.handle_responses()
                elif channel_key == 'forward_in':
                    self.handle_forwards()
                elif channel_key == 'instruction_in':
                    self.handle_instruction()
            else:
                if channel_key == 'instruction_in':
                    print(f"{self.deviceID} run end")
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
            if msg.mtype is not MessageType.Data:
                raise ValueError("Directory should only reply with data")
            # if cache receives 'ack' from other caches before getting response from directory
            if msg.AckCnt + tbe.acks_outstanding == 0:
                self.trigger(Event.DataDirNoAcks, msg.addr, entry, msg)
            else: # wait for more acks
                self.trigger(Event.DataDirAcks, msg.addr, entry, msg)
        
        # if sender is another cache
        else:
            if msg.mtype is MessageType.Data:
                self.trigger(Event.DataOwner, msg.addr, entry, msg)
            elif msg.mtype is MessageType.InvAck:
                print(f"Got inv ack. {tbe.acks_outstanding} left")
                if tbe.acks_outstanding is 1:
                    self.trigger(Event.LastInvAck, msg.addr, entry, msg)
                else:
                    self.trigger(Event.InvAck, msg.addr, entry, msg)
        # if no messages to process, go to next message queue to process
        # self.handle_forwards()

    def handle_forwards(self):
        channel = self.channels['forward_in']
        # Check the head of the queue
        msg = channel.peek()  
        channel.transaction_ongoing = True # set flag to indicate transaction is ongoing
        entry = self.cache.get_entry(msg.addr)
        #tbe = self.tbes.entries[msg.addr]

        if msg.mtype is MessageType.FwdGetS:
            self.trigger(Event.FwdGetS, msg.addr, entry, msg)
        elif msg.mtype is MessageType.FwdGetM:
            self.trigger(Event.FwdGetM, msg.addr, entry, msg)
        elif msg.mtype is MessageType.Inv:
            self.trigger(Event.Inv, msg.addr, entry, msg)
        elif msg.mtype is MessageType.PutAck:
            self.trigger(Event.PutAck, msg.addr, entry, msg)            
        else:
            raise ValueError("Unexpected forward message type.")
        # if no messages to process, go to next message queue to process
        # self.handle_instruction()

    def handle_instruction(self):
        channel = self.channels['instruction_in']
        # Check the head of the queue
        msg = channel.peek()
        channel.transaction_ongoing = True # set flag to indicate transaction is ongoing
        entry = self.cache.get_entry(msg.addr) # what if the entry is not in cache?
        #tbe = self.tbes.entries[msg.addr]

        # if miss and cache full
        #if not entry.isValid and not self.cache.is_cache_available(msg.addr):
        if not entry.isValid and not self.cache.is_cache_available():
        # if entry.state is State.I and not self.cache.is_cache_available(msg.addr):
            # get replacement address from cache
            replacement_addr = self.cache.getReplacementAddr()
            replacement_entry = self.cache.get_entry(replacement_addr)
            self.trigger(Event.Replacement, replacement_addr, replacement_entry, msg)
        else: # if entry is valid
            if msg.mtype is MessageType.Load:
                self.trigger(Event.Load, msg.addr, entry, msg)
            elif msg.mtype is MessageType.Store:
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
        if event is Event.DataDirNoAcks:
            print(f"DataDirNoAcks for address {addr}")
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
        elif event is Event.Store:    
            print(f"Store for address {addr}")

## ACTIONS
    ## below are called during do_transition
    
    def allocateTBE(self, addr):
        self.tbes.allocate(addr)
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

        print("Hit miss processed.")

    # Send request to directory
    def sendGetS(self, addr):
        out_msg = Message(mtype = MessageType.GetS, addr = addr, src = self.deviceID, dest = self.dirID) #data_block size?
        self.channels["request_out"].enqueue(out_msg)
        print("GetS message sent for read access.")

    def sendGetM(self, addr):
        out_msg = Message(mtype = MessageType.GetM, addr = addr, src = self.deviceID, dest = self.dirID)
        self.channels["request_out"].enqueue(out_msg)
        print("GetM message sent to fetch exclusive access.")

    def sendPutS(self, addr): # need to remove this request
        out_msg = Message(mtype = MessageType.PutS, addr = addr, src = self.deviceID, dest = self.dirID)
        self.channels["request_out"].enqueue(out_msg)
        print("PutS message sent for downgrading the block state.")

    def sendPutM(self, addr, cache_entry):
        out_msg = Message(mtype = MessageType.PutM, addr = addr, src = self.deviceID, dest = self.dirID, data_block=cache_entry.data_block)
        self.channels["request_out"].enqueue(out_msg)
        print("PutM message sent to evict block from modified state.")

    # Cache
    def allocateCacheBlock(self, entry):
        # assert isValid
        # asert cache is not full
        self.cache.set_entry(entry)     
    
    def writeDataToCache(self, message, cache_entry):
        #cache_entry.data_block = message.data_block
        self.cache.set_entry(cache_entry)
        print("Data written to cache block.")

    def sendCacheDataToReq(self, message, cache_entry):
        out_msg = Message(mtype = MessageType.Data, addr = message.addr, src=self.deviceID, dest = message.fwd_dest, data_block=cache_entry.data_block)
        self.channels["response_out"].enqueue(out_msg)        
        print("Cache data sent to requestor.")

    def sendCacheDataToDir(self, message, cache_entry):
        out_msg = Message(mtype = MessageType.Data, addr = message.addr, src=self.deviceID, dest = self.dirID, data_block=cache_entry.data_block)
        self.channels["response_out"].enqueue(out_msg)
        print("Cache data sent to directory.")

    def sendInvAcktoReq(self, message):
        out_msg = Message(mtype = MessageType.InvAck, addr = message.addr, src=self.deviceID, dest = message.fwd_dest)
        self.channels["response_out"].enqueue(out_msg)
        print("Invalidation Ack sent to requestor.")

    def deallocateCacheBlock(self, addr):
        self.cache.invalidate(addr)
        print("Cache block deallocated.")

    def decrAcks(self,addr):
        # self.acks_outstanding -= 1
        self.tbes[addr].acks_outstanding -= 1
        print(f"Acks outstanding decremented, now {self.acks_outstanding}.")

    def storeAcks(self,addr,message):
        # assert self.tbes.is_valid(addr)
        self.tbes[addr].acks_outstanding += message.ackCnt
        print("Store acknowledgements processed.")

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

    def popForwardQueue(self):
        self.channels["forward_in"].dequeue()
        self.channels["forward_in"].transaction_ongoing = False
        print("Forward queue popped for processing.")
    
    def stall():
        print("Stalling: Unsupported event in current state.")

## STATE TRANSITION
    # process event and do state transition
    def doTransition(self, event, addr, cache_entry, message=None, tbe=None):
        print(f"Processing event: {event} in state: {cache_entry.state}")
        
        ## define state transition
        ## transition (cur_state, event, next_state) --> action
        if cache_entry.state is State.I:
            if event is Event.Load:
                cache_entry.state =  State.IS_D
                # self.allocateCacheBlock()
                cache_entry.set_entry(cache_entry)
                self.allocateTBE(addr)
                self.sendGetS(addr)
                self.popInstructionQueue() # start when state changes to S?
                print("Transition from I to IS_D state: Load request received in Invalid state.")
            elif event is Event.Store:
                cache_entry.state =  State.IM_AD 
                # self.allocateCacheBlock(cache_entry)
                cache_entry.set_entry(cache_entry)
                self.allocateTBE(addr)
                self.sendGetM(addr)
                self.popInstructionQueue() # start when state changes to M?              
                print("Transition from I to IM_D state: Store request received in Invalid state.")

        elif cache_entry.state is State.IS_D :
            if event in [Event.Load, Event.Store, Event.Replacement]:
                self.stall
            ## Invalidation mesage always ack --> just change at trigger?
            elif event is Event.Inv:
                self.sendInvAcktoReq(message)
            elif event in [Event.DataDirNoAcks, Event.DataOwner]:
                cache_entry.state = State.S
                self.writeDataToCache(message, cache_entry)
                self.deallocateTBE(addr)
                self.loadMiss()
                print("Transition to Shared state: Data received with no ACKs required.")

        elif cache_entry.state in [State.IM_AD, State.IM_A] :
            if event in [Event.Load, Event.Store, Event.FwdGetS, Event.FwdGetM]:
                self.stall

        elif cache_entry.state is [State.IM_AD, State.SM_AD]:
            if event in [Event.DataDirNoAcks, Event.DataOwner]:
                cache_entry.state = State.M
                print("Transition to M state: Data received with no ACKs required.")
                self.writeDataToCache(message, cache_entry)
                self.deallocateTBE(addr)
                self.storeMiss()
                self.popResponseQueue()    

        elif cache_entry.state is State.IM_AD:
            if event is Event.DataDirAcks:
                cache_entry.state = State.IM_A
                print("Transition to IM_A state: Data received with ACKs required.")
                self.writeDataToCache(message, cache_entry)
                self.storeAcks(addr, message)
                self.popResponseQueue()
        
        elif cache_entry.state in [State.IM_AD, State.IM_A, State.SM_AD, State.SM_A] :
            if event is Event.InvAck:
                self.decrAcks(addr)
                self.popResponseQueue()        

        elif cache_entry.state is [State.IM_A, State.SM_A]:
            if event is Event.LastInvAck:
                cache_entry.state = State.M
                print("Transition to M state: Data received with no ACKs required.")
                self.deallocateTBE(addr)
                self.storeMiss()
                self.popResponseQueue()    

        elif cache_entry.state in [State.S, State.SM_AD, State.SM_A, State.M] :
            if event is Event.Load:
                self.loadHit(cache_entry)
                self.popInstructionQueue()

        elif cache_entry.state is State.S:
            if event is Event.Store:
                cache_entry.state = 'SM_AD'
                self.sendGetM(addr)
                self.popInstructionQueue()
                print("Transition to SM_AD state: Store request received in Shared state.")
            elif event is Event.Inv:
                cache_entry.state = 'I'
                self.sendInvAcktoReq(message)
                self.popForwardQueue()
                print("Transition to I state: Invalidation request received in Shared state.")
            # no explicit PutS message for replacement, instead need to respond to all Ack
            elif event is Event.Replacement:
              cache_entry.state = State.SI_A

        elif cache_entry.state in [State.SM_AD, State.SM_A]:
            if event in [Event.Store, Event.Replacement, Event.FwdGetS, Event.FwdGetM]:
                self.stall
        
        elif cache_entry.state is State.SM_AD:
            if event is Event.Inv:
                cache_entry.state = State.IM_AD
                self.sendInvAcktoReq(message)
                # self.acks_outstanding -= 1
                # print(f"Processed InvAck: {self.acks_outstanding} ACKs remaining.")
            elif event is Event.DataDirAcks:
                cache_entry.state = State.SM_A
                self.writeDataToCache(message, cache_entry)
                self.storeAcks(addr, message)
                self.popResponseQueue()    

            # if self.acks_outstanding is 0 and event is Event.LastInvAck:
            #     cache_entry.state = State.M
            #     print("Transition to Modified state: Last InvAck received.")

        elif cache_entry.state is State.M:
            if event is Event.Replacement:
                cache_entry.state = State.I
                self.data_block = None
                print("Invalidated cache: Replacement occurred.")
            elif event is Event.Store:
                print("Processing Store event in Modified state.")
                self.storeHit(cache_entry)
                self.popInstructionQueue()
            elif event is Event.FwdGetS:
                print("Processing FwdGetS event in Modified state.")
                self.sendCacheDataToReq(message, cache_entry)
                self.sendCacheDataToDir(message, cache_entry)
                self.popForwardQueue()
            elif event is Event.FwdGetM:
                print("Processing FwdGetM event in Modified state.")
                self.sendCacheDataToReq(message, cache_entry)
                self.deallocateCacheBlock(addr)
                self.popForwardQueue()

        elif cache_entry.state in [State.MI_A, State.SI_A, State.II_A]:
            if event in [Event.Load, Event.Store, Event.Replacement]:
                self.stall
            elif event is Event.PutAck:
                cache_entry.state = State.I
                print("Transition to I state: PutAck received.")
                self.deallocateCacheBlock(addr)
                self.popForwardQueue()        
    
        elif cache_entry.state is State.MI_A:
            if event is Event.FwdGetS:
                cache_entry.state = State.SI_A
                print("Transition to SI_A state: Forwarding cache data.")
                self.sendCacheDataToReq(message, cache_entry)
                self.sendCacheDataToDir(message, cache_entry)
                self.popForwardQueue()
            elif event is Event.FwdGetM:
                cache_entry.state = State.II_A
                print("Transition to II_A state: Forwarding cache data.")
                self.sendCacheDataToReq(message, cache_entry)
                self.popForwardQueue()

        elif cache_entry.state is State.SI_A:
            if event is Event.Inv:
                cache_entry.state = State.II_A
                print("Transition to II_A state: Invalidating cache block.")
                self.sendInvAcktoReq(message)
                self.popForwardQueue()

        elif cache_entry.state is State.II_A:
            if event is Event.PutAck:
                cache_entry.state = State.I
                print("Transition to I state: PutAck received.")
                self.deallocateCacheBlock(addr)
                self.popForwardQueue()

## BARRIER HANDLING
    def print_barriers(self):
        # Prints all barriers and their counts
        if not self.barriers:
            print("No barriers to display.")
            return
        print(f"=={self.deviceID} Current bBarriers and Their Counts==")
        for barrier_id, count in self.barriers.items():
            print(f"Barrier ID: {barrier_id}, Count: {count}")



## OUTPUT INTERFACE
    # returns response message and dequeues it from reponse queue

    def receive_resp_msg(self) : 
        response_channel = self.channels['response_out']
        if response_channel.is_empty():
            return None
        else:
            # we assume stalling is handled in the top level
            # if rep_queue.is_full():
            #     return None
            # else: 
            message = response_channel.dequeue()
            # we assume LLC response input queue enqueing is handled seperately
            # rep_queue.enqueue(channels['response_out'][0])
            return message
        

    def get_generated_msg(self) : #peek req_queue
        request_channel = self.channels['request_out']
        if request_channel.is_empty():
            return None
        else:
            return request_channel.peek()

    def take_generated_msg(self) : #pop req_queue
        request_channel = self.channels['request_out']
        if request_channel.is_empty():
            return None
        else:
            else: 
                message = request_channel.dequeue()
                return message





