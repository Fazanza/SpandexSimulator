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

        # Cache Test
        # Example of creating and using the Cache
        cache_size = 10  # Define the size of the cache
        cache = Cache(cache_size)
        # Set some entries
        #cache.set_entry(0x1, State.S, True, True, [0x01, 0x02, 0x03, 0x04])
        #cache.set_entry(0x300, State.S, True, False, [0x05, 0x06, 0x07, 0x08])
        # Print all cache contents
        cache.print_contents()

        #dut = proc_cache(cache_size=8, ways = 2, line_size = 2, memory = 16) 


        # test 1
        # Instantiate cache and queue

        cache_ctrl = CacheController(cache, clock)


        ld_msg = Message(MessageType.Load, 0x0, Node.CPU0, "Node2", [0x01, 0x02, 0x03, 0x04])
        st_msg = Message(MessageType.Store, 0x0, Node.CPU0, "Node2", [0x01, 0x02, 0x03, 0x04])

        for i in range(2):
            cache_ctrl.channels['instruction_in'].send_message(ld_msg)
            cache_ctrl.channels['instruction_in'].send_message(st_msg)
            #cache_ctrl.channels['response_in'].send_message(msg)

        # queue 1 message each to all queues
        inv_ack_message = Message(
            mtype=MessageType.InvAck,
            addr=0x1A2B3C4D,
            src=Node.CPU2,
            dest=Node.CPU1,
            ackCnt=1  # Acknowledgement count example
        )

        fwd_gets_message = Message(
            mtype=MessageType.GetS,
            addr=0x1A2B3C4D,
            src=Node.CPU1,
            dest=Node.CPU0,
            fwd_dest=Node.CPU0  # Forward to CPU0
        )

        load_message = Message(
            mtype=MessageType.LD,
            addr=0x1A2B3C4D,
            src=Node.NULL,
            dest=Node.CPU0,
            data_block=[0xDE, 0xAD, 0xBE, 0xEF]  # Example data block
        )
        #cache_ctrl.channels['response_in'].send_message(inv_ack_message)
        #cache_ctrl.channels['forward_in'].send_message(fwd_gets_message)
        #cache_ctrl.channels['instruction_in'].send_message(load_message)



        cache_ctrl.channels['instruction_in'].print_all_messages()
        # cache_ctrl.handle_instruction()
        # cache_ctrl.handle_instruction()
        # cache_ctrl.handle_instruction()
        # print(cache_ctrl.channels['instruction_in'])

        for _ in range(5):
            clock.clockEdge()
            cache_ctrl.runL1Controller()
            # for debugging
            cache_ctrl.channels['instruction_in'].print_all_messages()

        cache_ctrl.popInstructionQueue()
        for _ in range(5):
            clock.clockEdge()
            cache_ctrl.runL1Controller()
            # for debugging
            cache_ctrl.channels['instruction_in'].print_all_messages()

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
        src_directory = os.getcwd()
        parent_directory = os.path.dirname(src_directory)
        memory_traces_directory = os.path.join(parent_directory, 'memory_traces')
        file_path = os.path.join(memory_traces_directory, 'cpu_0.txt')
        


        message_buffer = VirtualChannel()
        parser = Parser()
        parser.process_trace_file(file_path, message_buffer)
   
# Run tests
if __name__ == '__main__':
    unittest.main()
