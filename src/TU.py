################
# Translation Unit for Local Controller
# Translates local request to global request 
# takes global response and coalesce them based on the device granularity
################

import msi_coherence import *


class TranslationUnit:
    def __init__(self, cache_controller):
        self.cache_controller = cache_controller

    def process_local_request(self, msg):
        # Check the type of request and translate to global coherence protocol request
        if msg.mtype == MessageType.LD:
            # Local load request, possibly translate to a global GetS request
            self.send_global_request(msg.addr, MessageType.GetS)
        elif msg.mtype == MessageType.ST:
            # Local store request, possibly translate to a global GetM request
            self.send_global_request(msg.addr, MessageType.GetM)
        else:
            raise ValueError("Unsupported local request type")

    def send_global_request(self, addr, request_type):
        # Create a global request message based on local request
        global_msg = Message(mtype=request_type, addr=addr, src=self.cache_controller.deviceID, dest=self.cache_controller.dirID)
        self.cache_controller.channels['request_out'].enqueue(global_msg)
        print(f"Global {request_type.name} request sent for address {addr}")

    def handle_global_response(self, global_msg):
        # Determine the local event or response based on the global response
        if global_msg.mtype in [MessageType.Data, MessageType.DataAck]:
            # Data or DataAck received from directory or other cache
            entry = self.cache_controller.cache.get_entry(global_msg.addr)
            if global_msg.src == self.cache_controller.dirID:
                self.cache_controller.trigger(Event.DataDirNoAcks, global_msg.addr, entry, global_msg)
            else:
                self.cache_controller.trigger(Event.DataOwner, global_msg.addr, entry, global_msg)
        elif global_msg.mtype == MessageType.InvAck:
            # Invalidate Acknowledgement received
            entry = self.cache_controller.cache.get_entry(global_msg.addr)
            self.cache_controller.trigger(Event.InvAck, global_msg.addr, entry, global_msg)
        else:
            raise ValueError("Unexpected global response type")

    def coalesce_responses(self, global_msg):
        # Coalescing logic if needed
        entry = self.cache_controller.cache.get_entry(global_msg.addr)
        if global_msg.mtype == MessageType.Data:
            if global_msg.ackCnt > 0:
                self.cache_controller.trigger(Event.DataDirAcks, global_msg.addr, entry, global_msg)
            else:
                self.cache_controller.trigger(Event.DataDirNoAcks, global_msg.addr, entry, global_msg)

# Integration with CacheController
class CacheController:
    def __init__(self, cache, clock, deviceID=Node.CPU0):
        # existing initialization code
        self.translation_unit = TranslationUnit(self)

    def handle_instruction(self):
        # modified to use translation unit
        msg = self.channels['instruction_in'].peek()
        self.translation_unit.process_local_request(msg)

# Usage example in CacheController:
# controller.handle_instruction() processes local requests to global and vice versa




