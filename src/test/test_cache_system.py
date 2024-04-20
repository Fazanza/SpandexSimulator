################
# To run all tests in test cases
# python3 -m unittest test.test_cache_system.TestCacheSystem
#
# To run a specific test method within a test case:
# python3 -m unittest test.test_cache_system.TestCacheSystem.test_message_sending
#################
import unittest
from clock import Clock
from msi_coherence import *
from parser import *
import os
from test.channel import *


class TestCacheSystem(unittest.TestCase):


    def test_setUp(self):
        # global counter - tick
        self.clock = Clock()
        for i in range(100):
            self.clock.clockEdge() # increment clock
            print("Current tick:", self.clock.currentTick())  # Output the current global tick

        self.cache = Cache(10)
        self.cache_ctrl = CacheController(self.cache, self.clock)
        
        self.msg = Message(MessageType.LD, "0x1A", "Node1", "Node2", "100")
        self.cache_ctrl.channels['mandatory_in'].print_all_messages()
        for i in range(5):
            self.cache_ctrl.channels['mandatory_in'].send_message(self.msg)
        self.cache_ctrl.channels['mandatory_in'].print_all_messages()

    def test_cache(self):
        # Example to create a cache and check availability
        cache = Cache(size=4)

        print("initial cache")
        cache.print_contents()  # Print initial state

        c1 = CacheEntry(0x1, State.S, True, False, [0x01, 0x02, 0x03, 0x04])
        c2 = CacheEntry(0x50, State.M, True, True, [0x05, 0x06, 0x07, 0x08])
        c3 = CacheEntry(0x300, State.M, True, True, [0x11, 0x12, 0x13, 0x14])
        c4 = CacheEntry(0x200, State.S, True, False, [0x0D, 0x0E, 0x0F, 0x10])
        # Writing to same address
        c5 = CacheEntry(0x300, State.M, True, True, [0x11, 0x12, 0x13, 0x14])
        # Testing eviction policy
        c6 = CacheEntry(0x400, State.M, True, True, [0x11, 0x12, 0x13, 0x14])
        c7 = CacheEntry(0x600, State.M, True, True, [0x11, 0x12, 0x13, 0x14])
        c8 = CacheEntry(0x800, State.M, True, True, [0x11, 0x12, 0x13, 0x14])
        c9 = CacheEntry(0x400, State.M, True, True, [0x11, 0x12, 0x13, 0x14])
        c10 = CacheEntry(0x900, State.M, True, True, [0x11, 0x12, 0x13, 0x14])
        c11 = CacheEntry(0xc00, State.M, True, True, [0x11, 0x12, 0x13, 0x14])
        # Test set eviction
        c12 = CacheEntry(0x430, State.M, True, True, [0x11, 0x12, 0x13, 0x14])
        c13 = CacheEntry(0x950, State.M, True, True, [0x11, 0x12, 0x13, 0x14])
        c13 = CacheEntry(0x960, State.M, True, True, [0x11, 0x12, 0x13, 0x14])
        c14 = CacheEntry(0xc20, State.M, True, True, [0x11, 0x12, 0x13, 0x14])

        Cache.set_entry(cache, c1)
        Cache.set_entry(cache, c2)
        Cache.set_entry(cache, c3)
        Cache.set_entry(cache, c4)
        Cache.set_entry(cache, c5)
        Cache.set_entry(cache, c6)
        Cache.set_entry(cache, c7)
        Cache.set_entry(cache, c8)
        Cache.set_entry(cache, c9)
        Cache.set_entry(cache, c10)
        Cache.set_entry(cache, c11)
        Cache.set_entry(cache, c12)
        Cache.set_entry(cache, c13)
        Cache.set_entry(cache, c14)

        cache.print_contents()  # Print initial state

        #cache.set_entry(0x1, State.S, True, True, [0x01, 0x02, 0x03, 0x04])
        #cache.set_entry(0x300, State.S, True, False, [0x05, 0x06, 0x07, 0x08])

    # def enqueue_memory_trace():
    #     self.setup = setUp()
    #     msg = Message(MessageType.LD, "0x1A", "Node1", "Node2", "100")
    #     setup.cache_ctrl.channels['mandatory_in'].print_all_messages()
    #     for i in range(5):
    #         setup.cache_ctrl.channels['mandatory_in'].send_messages(msg)
    #     setup.cache_ctrl.channels['mandatory_in'].print_all_messages()

    def test_message_handling_priority(self):
        clock = Clock()
        for i in range(100):
            clock.clockEdge()

        # Instantiate CPU [L1]
        cache_ctrl = CacheController(20)

        # setup cache
        cache = cache_ctrl.cache
        c1 = CacheEntry(0x1, State.SM_D, True, False, [0x01, 0x02, 0x03, 0x04])
        c2 = CacheEntry(0x45, State.M, True, False, [0x05, 0x06, 0x07, 0x08])
        c3 = CacheEntry(0x85, State.I, True, False, [0x11, 0x12, 0x13, 0x14])
        c4 = CacheEntry(0x123, State.S, True, False, [0x0D, 0x0E, 0x0F, 0x10])
        Cache.set_entry(cache, c1)
        Cache.set_entry(cache, c2)
        Cache.set_entry(cache, c3)
        Cache.set_entry(cache, c4)
        cache_ctrl.cache.print_contents()

        cache_ctrl.setCPU() #parse mem traces
        cache_ctrl.channels['instruction_in'].print_all_messages()

        print("============SIMULATION START==================")
        for _ in range(100):
            clock.clockEdge()
            print(f"===============CYCLE{clock.tick}===================")
            cache_ctrl.runCPU()
            #cache_ctrl.popInstructionQueue()
            print(f"===================================================")


        # # MESSAGE TEMPLATE
        # # inv_ack_message = Message(
        # #     mtype=MessageType.InvAck,
        # #     addr=0x1A2B3C4D,
        # #     src=Node.CPU2,
        # #     dest=Node.CPU1,
        # #     ackCnt=1  # Acknowledgement count example
        # # )

        # fwd_gets_message = Message(
        #     msg_type=MessageType.FwdGetS,
        #     addr=0x1,
        #     src=Node.LLC,
        #     dst=Node.CPU0,
        #     fwd_dst=Node.CPU1  # Forward to CPU0
        # )

        # load_message = Message(
        #     msg_type=MessageType.FwdGetM,
        #     addr=0x50,
        #     src=Node.LLC,
        #     dst=Node.CPU0,
        #     fwd_dst=Node.CPU2  # Forward to CPU0
        #     #data_block=[0xDE, 0xAD, 0xBE, 0xEF]  # Example data block
        # )

        # # cache_ctrl.channels['response_in'].send_message(inv_ack_message)
        # cache_ctrl.channels['request_in'].send_message(fwd_gets_message)
        # cache_ctrl.channels['request_in'].send_message(load_message)
        # # cache_ctrl.channels['instruction_in'].send_message(load_message)

        # cache_ctrl.setCPU()
        # cache_ctrl.channels['request_in'].print_all_messages()
        # cache_ctrl.channels['instruction_in'].print_all_messages()
        # cache_ctrl.print_barriers()
        # # cache_ctrl.handle_instruction()
        # # cache_ctrl.handle_instruction()
        # # cache_ctrl.handle_instruction()
        # # print(cache_ctrl.channels['instruction_in'])

        # print("============SIMULATION START==================")
        # for _ in range(5):
        #     clock.clockEdge()
        #     cache_ctrl.runCPU()
        # #     # for debugging
        # #     cache_ctrl.channels['instruction_in'].print_all_messages()

        # cache_ctrl.popRequestQueue()
        # print("============POP REQUEST QUEUE=====================")
        # for _ in range(5):
        #     clock.clockEdge()
        #     cache_ctrl.runCPU()        
        # # for _ in range(5):
        # #     clock.clockEdge()
        # #     cache_ctrl.runL1Controller()
        # #     # for debugging
        # #     cache_ctrl.channels['instruction_in'].print_all_messages()

    def test_tbe(self):
        # Instantiate tbeTable and add some test cases
        tbe_table = tbeTable()

        # Test 1: Allocation and Initial State Check
        address = 0x200
        tbe_entry = tbe(State.I, [0x19, 0x20, 0x21], 0)
        allocated_tbe = tbe_table.allocate(address, tbe_entry)
        print(f"allocated TBE: {allocated_tbe}")  # Expected: TBE with state 'I', empty data block, and 0 acks

        # Test 2: Lookup Functionality
        print(f"lookUp(): {tbe_table.lookup(address)}")  # Expected: Same as allocated_tbe
        print(tbe_table.lookup(0x404))  # Expected: None

        # Test 3: Deallocate and Check Absence
        tbe_table.deallocate(address)
        print(tbe_table.is_present(address))  # Expected: False

        # Test 4: Multiple TBE Management
        addresses = [0x100, 0x180, 0x240]
        for addr in addresses:
            tbe_entry = tbe(State.M, [0x19, 0x20, 0x21], 3)
            tbe_table.allocate(addr, tbe_entry)
        print(all(tbe_table.is_present(addr) for addr in addresses))  # Expected: True

    def test_message_sending(self):
        # Simulate sending a message
        msg = Message(addr="0x1A", response_type="Data", src="Node1", dest="Node2", data_block="100", ackCnt="2")
        self.cache_ctrl.channels['response_in'].send_message(msg)
        self.assertFalse(self.cache_ctrl.channels['response_in'].is_empty())
        received_message = self.cache_ctrl.channels['response_in'].receive_message()
        self.assertEqual(msg, received_message)

    def test_handling_requests(self):
        # Assuming functionality to handle requests is implemented
        self.cache_ctrl.channels['mandatory_in'].send_message("Load 0x1A")
        self.cache_ctrl.channels['mandatory_in'].send_message("Store 0x1A")
        # Assuming a method to handle messages
        self.cache_ctrl.handle_incoming_requests()
        # Checks go here to validate state changes
    
    def test_mem_trace_parsing(self):

        # get file path

        message_buffer = VirtualChannel()
        parser = Parser()
        parser.process_trace_file(file_path, message_buffer)
    
    def test_barrier(self):
        # Instantiate CPU [L1]
        cache_ctrl = CacheController(20)
        cache_ctrl.cache.print_contents()  # Print initial state
        cache_ctrl.setCPU() #parse mem traces
        cache_ctrl.channels['instruction_in'].print_all_messages()
        cache_ctrl.print_barriers()

        # dequeue inst 
        clock = Clock()
        for _ in range(3):
            clock.clockEdge()
            print(f"CLOCK TICK : {clock.tick}")
            cache_ctrl.runCPU()
            #cache_ctrl.popInstructionQueue()
            #cache_ctrl.channels['instruction_in'].transaction_ongoing = False
            print(f"Barrier Flag (ID) : {cache_ctrl.encounter_barrier}")
            # for debugging
            #cache_ctrl.channels['instruction_in'].print_all_messages()

        #cache_ctrl.popInstructionQueue()
        #for _ in range(1):
        clock.clockEdge()
        cache_ctrl.update_barrier("0") 
        cache_ctrl.update_barrier("0")
        cache_ctrl.runCPU()

        # for debugging
        cache_ctrl.channels['instruction_in'].print_all_messages()
        print(cache_ctrl.encounter_barrier)
        cache_ctrl.print_barriers()
        
        #for _ in range(1)
        clock.clockEdge()
        cache_ctrl.update_barrier("0")        
        cache_ctrl.runCPU()
        cache_ctrl.print_barriers()

        #for _ in range(1)
        clock.clockEdge()
        cache_ctrl.update_barrier("0")
        cache_ctrl.runCPU()
        cache_ctrl.print_barriers()
        

        #for _ in range(1)
        clock.clockEdge()
        cache_ctrl.runCPU()
        cache_ctrl.print_barriers()
        print(cache_ctrl.encounter_barrier)

        #for _ in range(1)
        clock.clockEdge()
        cache_ctrl.runCPU()
        cache_ctrl.print_barriers()
        print(f"encounter flag: {cache_ctrl.encounter_barrier}")
        
    def test_msi(self):
        # Instantiate CPU [L1]
        cache_ctrl = CacheController(20)
        cache_ctrl.cache.print_contents()  # Print initial state
        cache_ctrl.setCPU() #parse mem traces
        cache_ctrl.channels['instruction_in'].print_all_messages()


        # setup cache
        cache = cache_ctrl.cache
        c1 = CacheEntry(0x1, State.S, True, False, [0x01, 0x02, 0x03, 0x04])
        c2 = CacheEntry(0x45, State.M, True, False, [0x05, 0x06, 0x07, 0x08])
        c3 = CacheEntry(0x85, State.I, True, False, [0x11, 0x12, 0x13, 0x14])
        c4 = CacheEntry(0x123, State.S, True, False, [0x0D, 0x0E, 0x0F, 0x10])
        Cache.set_entry(cache, c1)
        Cache.set_entry(cache, c2)
        Cache.set_entry(cache, c3)
        Cache.set_entry(cache, c4)
        cache_ctrl.cache.print_contents()

        # enque some request and response




 
    def test_comm(self):
        # Example usage
        comm_system = CommunicationSystem()
        # Assuming channels are filled with some data
        comm_system.channels['request_out'].queue.append('Request1')
        comm_system.channels['response_out'].queue.append('Response1')
        comm_system.channels['response_out'].queue.append('Response2')


        print(comm_system.get_generated_msg())  # Should print 'Response1' (Response priority)
        print(comm_system.get_generated_msg())
        print(comm_system.get_generated_msg())
        print(comm_system.take_generated_msg()) # Should remove and print 'Response1'
        print(comm_system.get_generated_msg())
        print(comm_system.take_generated_msg())
        print(comm_system.get_generated_msg())
        print(comm_system.take_generated_msg())
        print(comm_system.take_generated_msg())
        print(comm_system.get_generated_msg())
        

    def test_instruction_queue(self):
        clock = Clock()
        for i in range(100):
            clock.clockEdge()

        # Instantiate CPU [L1]
        cache_ctrl = CacheController(20)

        # setup cache
        cache = cache_ctrl.cache
        c1 = CacheEntry(0x1, State.SM_D, True, False, [0x01, 0x02, 0x03, 0x04])
        c2 = CacheEntry(0x45, State.M, True, False, [0x05, 0x06, 0x07, 0x08])
        c3 = CacheEntry(0x85, State.I, True, False, [0x11, 0x12, 0x13, 0x14])
        c4 = CacheEntry(0x123, State.S, True, False, [0x0D, 0x0E, 0x0F, 0x10])
        Cache.set_entry(cache, c1)
        Cache.set_entry(cache, c2)
        Cache.set_entry(cache, c3)
        Cache.set_entry(cache, c4)
        cache_ctrl.cache.print_contents()

        cache_ctrl.setCPU() #parse mem traces
        cache_ctrl.channels['instruction_in'].print_all_messages()

        print("============SIMULATION START==================")
        for _ in range(100):
            clock.clockEdge()
            print(f"===============CYCLE{clock.tick}===================")
            cache_ctrl.runCPU()
            #cache_ctrl.popInstructionQueue()
            print(f"===================================================")

    def test_response_queue(self):
        clock = Clock()
        
        # Instantiate CPU [L1]
        cache_ctrl = CacheController(20)

        # setup cache
        cache = cache_ctrl.cache
        c1 = CacheEntry(0x1, State.IM_D, True, False, [0x01, 0x02, 0x03, 0x04])
        c2 = CacheEntry(0x45, State.IM_D, True, False, [0x05, 0x06, 0x07, 0x08])
        c3 = CacheEntry(0x85, State.IM_D, True, False, [0x11, 0x12, 0x13, 0x14])
        c4 = CacheEntry(0x123, State.SM_D, True, False, [0x0D, 0x0E, 0x0F, 0x10])
        c5 = CacheEntry(0xc0, State.SM_D, True, False, [0x0D, 0x0E, 0x0F, 0x10])
        Cache.set_entry(cache, c1)
        Cache.set_entry(cache, c2)
        Cache.set_entry(cache, c3)
        Cache.set_entry(cache, c4)
        Cache.set_entry(cache, c5)
        cache_ctrl.cache.print_contents()

        # cache_ctrl.setCPU() #parse mem traces
        # cache_ctrl.channels['instruction_in'].print_all_messages()

        # Possible message types for the test
        allowed_message_types = [MessageType.PutAck, MessageType.DataDir, MessageType.DataOwner]

        # Randomly select a message type from the allowed types
        msg_type = random.choice(allowed_message_types)

        for _ in range(20):
            addr = random.randint(0x0, 0x100)  # Random address
            # Possible message types for the test
            allowed_message_types = [MessageType.PutAck, MessageType.DataDir, MessageType.DataOwner]
            # Randomly select a message type from the allowed types
            msg_type = random.choice(allowed_message_types)
            if msg_type in (MessageType.PutAck, MessageType.DataDir):
                src = Node.LLC  # Directory source for PutAck and DataDir
            else:
                src = random.choice([Node.CPU1, Node.CPU2, Node.CPU3])  # Random CPU source for DataOwner
            msg = Msg(msg_type, addr, src, dst = Node.CPU0)
            cache_ctrl.channels['response_in'].send_message(msg)

        cache_ctrl.channels['response_in'].print_all_messages()

        print("============SIMULATION START==================")
        for _ in range(100):
            clock.clockEdge()
            print(f"===============CYCLE{clock.tick}===================")
            cache_ctrl.runCPU()
            #cache_ctrl.popInstructionQueue()
            print(f"===================================================")
   
# Run tests
if __name__ == '__main__':
    unittest.main()
