from enum import Enum, auto
import random
from collections import deque
from clock import Clock
import time
import math
from proc_cache import proc_cache


class Node(Enum):
    LLC = auto()
    CPU0 = auto()
    CPU1 = auto()
    CPU2 = auto()
    CPU3 = auto()
    GPU = auto()
    MEM = auto()
    NULL = auto()


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
    DataDirNoAcks = auto()
    DataDirAcks = auto()

    # Responses from other caches
    DataOwner = auto()
    InvAck = auto()

    # Triggered after the last ack is received
    LastInvAck = auto()


class MessageType(Enum):
    GetS = auto()
    GetM = auto()
    PutS = auto()
    PutM = auto()

    FwdGetS = auto()
    FwdGetM = auto()
    Inv = auto()
    PutAck = auto()

    Data = auto()
    InvAck = auto()

    LD = auto()
    ST = auto()
    Replacement = auto()


# # Memory Operation from Memory Trace
# class 

class Message():
    def __init__(self, mtype, addr, src, dest, fwd_dest=Node.NULL, ackCnt=0, data_block=None):
        self.mtype = mtype
        self.addr = addr
        self.src = src
        self.dest = dest
        self.fwd_dest = fwd_dest
        self.ackCnt = ackCnt
        self.dataBlock = data_block

    def __str__(self):
        return (f"Message Type: {self.mtype}, "
                f"Address: {self.addr}, "
                f"Source: {self.src}, "
                f"Destination: {self.dest}, "
                f"Fwd_Dest: {self.fwd_dest}, "
                f"Ack Count: {self.ackCnt}, "
                f"Data Block: {self.dataBlock}")


# Virtual Channel
# Message Buffer
class VirtualChannel:
    def __init__(self):
        self.messages = deque()
        # Only one transaction can be outgoing in the queue
        # Sholdn't process next message until variable is false
        self.transaction_ongoing = False
        # self.clock = clock

    def __str__(self):
        return self.content

    def is_ready(self):
        return bool(self.messages)

    def enqueue(self, message):  # enque
        self.messages.append(message)

    # def receive_message(self):
    def dequeue(self):
        return self.messages.popleft() if self.messages else None

    def is_empty(self):
        return len(self.messages) == 0

    def peek(self):  # check the head point value of queue
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

## below is configruable
## same as cache.py
class CacheEntry:
    def __init__(self, address, state=State.I, isValid=False, isDirty=False, data_block=[]):
        # cache line metadata
        self.address = address & ~0x3F  # base address for the cache line --> Mask out the lower 6 bits for 64-byte alignment. given as hex value ex) 0x211
        self.state = state  # Cache line state for coherency
        self.isValid = isValid
        self.isDirty = isDirty
        # data_block --> [byte1.. byte16] # list of 16byes (currently fixed to 64 bytes per line size but can be configurable)
        data_block.extend([None] * (16 - len(data_block)))
        self.data_block = data_block
        self.LRU = -1  # will update later
        self.acksNeeded = -1
        self.acksReceived = 0
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
        if not self.is_cache_available(cache_entry.address) and base_address not in self.entries[set_num]:
            # Cache is full and the address is not in the cache, we need to evict an entry
            self.evict_cache_entry(set_num)
        if base_address in self.entries[set_num]:
            self.usage_order[set_num].remove(base_address)
        self.usage_order[set_num].append(base_address)
        self.entries[set_num][base_address] = cache_entry
        print(f"[CACHE] Cache entry in set {set_num} with tag {hex(cache_entry.address)} has been set or updated.")

    def invalidate(self, address):
        base_address = address & self.tag_mask
        set_num = (address >> 6) & self.set_mask
        if base_address in self.entries[set_num]:
            del self.entries[set_num][base_address]
            self.usage_order[set_num].remove(base_address)
            print(f"[CACHE] Invalidated Cache Line in set {set_num}: {self.entries[set_num][base_address]}")

    def is_cache_available(self, address):
        set_num = (address >> 6) & self.set_mask
        return len(self.entries[set_num]) < self.set_size

    def evict_cache_entry(self, set_num):
        # Evict the least recently used cache entry
        if self.entries:
            evicted_entry = self.entries[set_num].pop(self.usage_order[set].popleft())
            print(f"[CACHE] Evicted Cache Line in set {set_num}: {hex(evicted_entry.address)} with state {evicted_entry.state}")

    def setMRU(self, cache_entry):
        base_address = cache_entry.address & self.tag_mask
        set_num = (cache_entry.address >> 6) & self.set_mask
        self.usage_order[set_num].remove(base_address)
        self.usage_order[set_num].append(base_address)

    def getReplaceAddr(self, addr):
        set_num = (addr >> 6) & self.set_mask
        return self.usage_order[set_num][0].address

    def print_contents(self):
        # Print each entry's details
        print("=========================")
        print("[CACHE] Printing each cache entry")
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

    def __init__(self, cache, clock, deviceID=Node.CPU0):
        self.clock = clock
        self.cache = cache
        self.deviceID = deviceID
        self.dirID = Node.LLC  # device.getDirID()
        self.channels = {
            'response_in': VirtualChannel(),  # Data, InvAck
            'forward_in': VirtualChannel(),  # FwdGetS, FwdGetM, Inv, PutAck
            'instruction_in': VirtualChannel(),  # LD, ST
            'response_out': VirtualChannel(),  # GetS, GetM, PutS, PUtM
            'request_out': VirtualChannel()  # Data, InvAck
        }
        self.data_block = None
        self.capacity = 10

        self.last_checked_tick = self.clock.currentTick()
        self.clock.register_observer(self)
        # self.clock.register_callback(self.on_tick_update) 
        self.clock.callback = self.on_tick_update  # Setting the callback

    def runL1Controller(self):
        # List all channels in order of priority
        channels = ['response_in', 'forward_in', 'instruction_in']
        # These are output  channels 'request_out', 'response_out']
        for channel_key in channels:
            channel = self.channels[channel_key]
            if not channel.is_empty():
                if channel.transaction_ongoing:
                    print(f"[CHANNEL] Transaction is currently ongoing in {channel_key}. Skipping.")
                    continue  # Skip to the next channel
                self.doTransition(channel.peek())
            else:
                print(f"[CHANNEL] {channel_key} is empty. Moving to the next channel.")

    def on_tick_update(self, new_tick):
        # Handle the tick update here
        print(f"[CHANNEL] Tick changed detected in CacheController: {new_tick}")

    def update(self, tick):
        print(f"[CHANNEL] CacheController notified of tick update to: {tick}")

    ## MESSAGE HANDLE

    def handle_instruction(self):
        channel = self.channels['instruction_in']
        # Check the head of the queue
        msg = channel.peek()

        channel.transaction_ongoing = True  # set flag to indicate transaction is ongoing
        entry = self.cache.get_entry(msg.addr)  # what if the entry is not in cache?

        # if miss and cache full
        if not entry and not self.cache.is_cache_available(msg.addr):
            # if entry.state is State.I and not self.cache.is_cache_available(msg.addr):
            # get replacement address from cache
            replacement_addr = self.cache.getReplacementAddr(msg.addr)
            replacement_entry = self.cache.get_entry(replacement_addr)
            self.trigger(Event.Replacement, replacement_addr, replacement_entry)

    # Send request to directory
    def sendGetS(self, addr):
        out_msg = Message(mtype=MessageType.GetS, addr=addr, src=self.deviceID, dest=self.dirID)  # data_block size?
        self.channels["request_out"].enqueue(out_msg)
        print("GetS message sent for read access.")

    def sendGetM(self, addr):
        out_msg = Message(mtype=MessageType.GetM, addr=addr, src=self.deviceID, dest=self.dirID)
        self.channels["request_out"].enqueue(out_msg)
        print("GetM message sent to fetch exclusive access.")

    def sendPutS(self, message, cache_entry):  # need to remove this request
        out_msg = Message(mtype=MessageType.PutS, addr=message.addr, src=self.deviceID, dest=self.dirID,
                          data_block=cache_entry.data_block)
        self.channels["request_out"].enqueue(out_msg)
        print("PutS message sent for downgrading the block state.")

    def sendPutM(self, message, cache_entry):
        out_msg = Message(mtype=MessageType.PutM, addr=message.addr, src=self.deviceID, dest=message.src,
                          data_block=cache_entry.data_block)
        self.channels["request_out"].enqueue(out_msg)
        print("PutM message sent to evict block from modified state.")

    # Cache
    def allocateCacheBlock(self, entry):
        self.cache.set_entry(entry)

    def sendCacheDataToReq(self, message, cache_entry):
        out_msg = Message(mtype=MessageType.Data, addr=message.addr, src=self.deviceID, dest=message.fwd_dest,
                          data_block=cache_entry.data_block)
        self.channels["response_out"].enqueue(out_msg)
        print("Cache data sent to requestor.")

    def sendCacheDataToDir(self, message, cache_entry):
        out_msg = Message(mtype=MessageType.Data, addr=message.addr, src=self.deviceID, dest=self.dirID,
                          data_block=cache_entry.data_block)
        self.channels["response_out"].enqueue(out_msg)
        print("Cache data sent to directory.")

    def sendInvAcktoReq(self, message):
        out_msg = Message(mtype=MessageType.InvAck, addr=message.addr, src=self.deviceID, dest=message.src)
        self.channels["response_out"].enqueue(out_msg)
        print("Invalidation Ack sent to requestor.")

    def sendInvAcktoDir(self, message):
        out_msg = Message(mtype=MessageType.InvAck, addr=message.addr, src=self.deviceID, dest=self.dirID)
        self.channels["response_out"].enqueue(out_msg)
        print("Invalidation Ack sent to requestor.")

    def deallocateCacheBlock(self, addr):
        self.cache.invalidate(addr)
        print("Cache block deallocated.")

    # Message Buffer Management
    def stall(self):
        print("[Stalling]")

    ## STATE TRANSITION
    # process event and do state transition
    def doTransition(self, msg, channel):
        cache_entry = self.get_entry(msg.addr)
        channel.transaction_ongoing = True

        if cache_entry is None:  # Cache entry doesn't exist yet
            if msg.msg_type is MessageType.LD:
                self.cache.set_entry(CacheEntry(msg.addr, State.IS_D, True, False))
                self.sendGetS(msg.addr)
                channel.deque()  # start when state changes to S?
                print("[Transition] I to IS_D state: Load request received in Invalid state.")
            elif msg.msg_type is MessageType.ST:
                self.cache.set_entry(CacheEntry(msg.addr, State.IM_D, True, True))
                self.sendGetM(msg.addr)
                channel.deque()
                print("[Transition] I to IM_D state: Store request received in Invalid state.")
            elif msg.msg_type is MessageType.Inv:
                self.sendInvAcktoReq(msg)
            else:
                raise ValueError("[ERROR] Unexpected message type from processor")

        elif cache_entry.state is State.IS_D:
            if msg.msg_type in [MessageType.LD, MessageType.ST]:  # TODO: How to handle replacement
                self.stall()
            elif msg.msg_type is MessageType.Inv:
                self.sendInvAcktoReq(msg)
                channel.deque()
            elif msg.msg_type is MessageType.Data and msg.src is self.dirID:
                cache_entry.state = State.S
                cache_entry.data_block = msg.dataBlock
                self.cache.setMRU(cache_entry)
                channel.deque()
                print("[Transition] IS_D to S state")
            else:
                raise ValueError("[ERROR] Unexpected message type from processor")

        elif cache_entry.state in State.IM_D:
            if msg.msg_type in [MessageType.LD, MessageType.ST, MessageType.FwdGetS, MessageType.FwdGetM]:
                self.stall()
            elif msg.msg_type is MessageType.Inv:
                self.sendInvAcktoReq(msg)
                channel.deque()
            elif msg.msg_type is MessageType.Data:
                cache_entry.state = State.M
                cache_entry.data_block = msg.dataBlock
                self.cache.setMRU(cache_entry)
                channel.deque()
                print("[Transition] IM_D to M state")
            else:
                raise ValueError("[ERROR] Unexpected message type from processor")

        elif cache_entry.state is State.S:
            if msg.msg_type is MessageType.LD:
                self.cache.setMRU(cache_entry)
                channel.deque()
                print("[LOAD HIT] Cache entry hit in shared state")
            elif msg.msg_type is MessageType.ST:
                cache_entry.state = State.SM_D
                self.sendGetM(msg.addr)
                channel.deque()
                print("[Transition] S to SM_D state")
            elif msg.msg_type is MessageType.Inv:
                self.sendInvAcktoDir(msg)
                channel.deque()
            else:
                raise ValueError("[ERROR] Unexpected message type from processor")

        elif cache_entry.state is State.SM_D:
            if msg.msg_type is MessageType.LD:
                self.cache.setMRU(cache_entry)
                print("[LOAD HIT] Cache entry hit in shared state")
            elif msg.msg_type is [MessageType.ST, MessageType.FwdGetS, MessageType.FwdGetM]:
                self.stall()
            elif msg.msg_type is MessageType.Inv:
                cache_entry.state = State.IM_D
                self.sendInvAcktoReq(msg)
                channel.deque()
                print("[Transition] SM_D to IM_A state")
            elif msg.msg_type is MessageType.Data and msg.src is self.dirID:
                cache_entry.state = State.M
                cache_entry.data_block = msg.dataBlock
                self.cache.setMRU(cache_entry)
                channel.deque()
                print("[Transition] SM_D to M state")
            else:
                raise ValueError("[ERROR] Unexpected message type from processor")

        elif cache_entry.state is State.M:
            if msg.msg_type is MessageType.LD:
                self.cache.setMRU(cache_entry)
                channel.deque()
                print("[LOAD HIT] Cache entry LD hit in M")
            elif msg.msg_type is MessageType.ST:
                self.cache.setMRU(cache_entry)
                cache_entry.data_block = msg.dataBlock
                channel.deque()
                print("[STORE HIT] Cache entry ST hit in M")
            elif msg.msg_type is MessageType.FwdGetS:
                cache_entry.state = State.S
                self.sendPutS(msg, cache_entry)
                channel.deque()
                print("[Transtion] M to S, Sending PutS to Dir")
            elif msg.msg_type is MessageType.FwdGetM:
                cache_entry.state = State.I
                self.sendPutM(msg, cache_entry)
                channel.deque()
                print("[Transition] M to M, Sending PutM to Dir")
            elif msg.msg_type is MessageType.Inv:
                self.sendInvAcktoReq(msg)
                channel.deque()
            else:
                raise ValueError("[ERROR] Unexpected message type from processor")

        elif cache_entry.state in State.MI_A:
            if msg.msg_type in [MessageType.LD, MessageType.ST]:
                self.stall()
            elif msg.msg_type is MessageType.FwdGetS:
                cache_entry.state = State.SI_A
                self.sendPutS(msg, cache_entry)
                channel.deque()
                print("[Transition] MI_A to SI_A state")
            elif msg.msg_type is MessageType.FwdGetM:
                cache_entry.state = State.II_A
                self.sendPutM(msg, cache_entry)
                channel.deque()
                print("[Transition] MI_A to II_A state")
            elif msg.msg_type is MessageType.Inv:
                self.sendInvAcktoReq(msg)
                channel.deque()
            elif msg.msg_type is MessageType.PutAck:
                cache_entry.state = State.I
                channel.deque()
                print("[Transition] MI_A to I state")
            else:
                raise ValueError("[ERROR] Unexpected message type from processor")

        elif cache_entry.state in State.SI_A:
            if msg.msg_type in [MessageType.LD, MessageType.ST]:
                self.stall()
            elif msg.msg_type is MessageType.Inv:
                cache_entry.state = State.II_A
                self.sendInvAcktoReq(msg)
                channel.deque()
                print("[Transition] SI_A to II_A state")
            elif msg.msg_type is MessageType.PutAck:
                cache_entry.state = State.I
                channel.deque()
                print("[Transition] SI_A to I state")
            else:
                raise ValueError("[ERROR] Unexpected message type from processor")

        elif cache_entry.state in State.II_A:
            if msg.msg_type in [MessageType.LD, MessageType.ST]:
                self.stall()
            elif msg.msg_type is MessageType.Inv:
                self.sendInvAcktoReq(msg)
                channel.deque()
            elif msg.msg_type is MessageType.PutAck:
                cache_entry.state = State.I
                channel.deque()
                print("[Transition] II_A to I state")
            else:
                raise ValueError("[ERROR] Unexpected message type from processor")

        else:
            raise ValueError("[ERROR] Unexpected state")
