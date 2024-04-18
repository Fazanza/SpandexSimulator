from enum import Enum, auto
from collections import deque
#from msi_coherence import MessageType, Message, VirtualChannel, Node
# from cpu_message import MessageType, Message
from global_utility import Msg as Message
from global_utility import msg_type as MessageType
import os

class Parser:



    # not used - handle in cache_ctrl
    def parse_device_type(device_str):
        device_mapping = {
            'cpu_0': Node.CPU0,
            'cpu_1': Node.CPU1,
            'cpu_2': Node.CPU2,
            'cpu_3': Node.CPU3,
            'gpu': Node.GPU,
            'mem': Node.MEM,
            'llc': Node.LLC,
            'null': Node.NULL
        }
        device_str = device_str.lower().replace(' ', '')
        if device_str in device_mapping:
            return device_mapping[device_str]
        else:
            raise ValueError(f"Unknown device type: {device_str}")

    # Read 1 Trace Line and 
    # Return Corresponding Messages
    def parse_trace_line(self, line):
        # print(line)
        parts = line.split()
        if not parts:
            raise ValueError("Empty line or formatting error.")
        operation = parts[0]
        print(operation)
        
        # LD/ST
        # if operation in ['ld' or 'st']:
        if operation == 'ld' or operation == 'st':  
            print(parts)  
            if len(parts) < 2:
                raise ValueError(f"Insufficient arguments for {operation.upper()}.")
            address = int(parts[1])
            # device_type = parse_device_type(parts[2])
            #cpu_id = parts[2]
            #return self.MemoryRequest(MessageType.LD if operation == 'ld' else MessageType.ST, address)
            return Message(mtype = MessageType.LD if operation == 'ld' else MessageType.ST, addr = address)
        # Barrier
        elif operation.startswith('Barrier'):
            if len(parts) < 3:
                raise ValueError("Insufficient arguments for BARRIER.")
            barrier_id = parts[1] # barrier ID
            barrier_count = int(parts[2]) # barrier count
            print(f"barrierid: {barrier_id}, barreir_count{barrier_count}")
            #return self.MemoryRequest(MessageType.Barrier, barrier_count, Node.NULL)
            return Message(mtype = MessageType.Barrier, barrierID = barrier_id, barrierCnt = barrier_count)

        else:
            raise ValueError(f"Unsupported operation: {operation}")


    # Read the memory trace file
    # and enqueue to the buffer
    def process_trace_file(self, buffer):
        
        filepath = self.get_file_path()
        
        with open(filepath, 'r') as file:
            lines = file.readlines()

        i = 0
        while i < len(lines):
        #  for _ in range(3): # process 3 operations every tick
            if i >= len(lines):
                break
            try:
                request = self.parse_trace_line(lines[i].strip()) # remove whitespace
                # currently assume buffer is unlimited for instrution queue
                # if not buffer.send_message(request): # If the buffer is full 
                #     break
                buffer.send_message(request) 
                i += 1
            except ValueError as e:
                print(f"Error parsing line: {e}")
                i += 1 

        print(i)
    
    def get_file_path(self):
        # need to file_name for device - given from cache controller Device Type
        file_name = 'memory_trace_toy.txt'

        # get file path
        src_directory = os.getcwd()
        parent_directory = os.path.dirname(src_directory)
        memory_traces_directory = os.path.join(parent_directory, 'memory_traces')
        file_path = os.path.join(memory_traces_directory, file_name)
        return file_path