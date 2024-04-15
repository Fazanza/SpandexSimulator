################
# To run all tests in test cases
# python -m unittest test_cache_system.TestCacheSystem
#
# To run a specific test method within a test case:
# python -m unittest test_cache_system.TestCacheSystem.test_message_sending
#################
import unittest
from clock import Clock
from msi_coherence import (
State, Event, DeviceType, MessageType, Message, VirtualChannel, trb, trbTable, CacheEntry,
Cache, CacheController
)
class TestCacheSystem(unittest.TestCase):


    def setUp(self):
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

    # def enqueue_memory_trace():
    #     self.setup = setUp()
    #     msg = Message(MessageType.LD, "0x1A", "Node1", "Node2", "100")
    #     setup.cache_ctrl.channels['mandatory_in'].print_all_messages()
    #     for i in range(5):
    #         setup.cache_ctrl.channels['mandatory_in'].send_messages(msg)
    #     setup.cache_ctrl.channels['mandatory_in'].print_all_messages()

    def message_handling_priority(self):
        clock = Clock()
        for i in range(100):
            clock.clockEdge()

        # Cache Test
        # Example of creating and using the Cache
        cache_size = 10  # Define the size of the cache
        cache = Cache(cache_size)
        # Set some entries
        cache.set_entry(0x1, State.S, True, True, [0x01, 0x02, 0x03, 0x04])
        cache.set_entry(0x300, State.S, True, False, [0x05, 0x06, 0x07, 0x08])
        # Print all cache contents
        cache.print_contents()

        #dut = proc_cache(cache_size=8, ways = 2, line_size = 2, memory = 16) 


        # test 1
        # Instantiate cache and queue

        cache_ctrl = CacheController(cache, clock)


        ld_msg = Message(MessageType.LD, 0x0, Node.CPU0, "Node2", [0x01, 0x02, 0x03, 0x04])
        st_msg = Message(MessageType.ST, 0x0, Node.CPU0, "Node2", [0x01, 0x02, 0x03, 0x04])

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
        cache_ctrl.channels['forward_in'].send_message(fwd_gets_message)
        cache_ctrl.channels['instruction_in'].send_message(load_message)



        cache_ctrl.channels['instruction_in'].print_all_messages()
        # cache_ctrl.handle_instruction()
        # cache_ctrl.handle_instruction()
        # cache_ctrl.handle_instruction()
        # print(cache_ctrl.channels['instruction_in'])

        for i in range(5):
            clock.clockEdge()
            cache_ctrl.runL1Controller()
            # for debugging
            cache_ctrl.channels['instruction_in'].print_all_messages()

        cache_ctrl.popInstructionQueue()
        for i in range(5):
            clock.clockEdge()
            cache_ctrl.runL1Controller()
            # for debugging
            cache_ctrl.channels['instruction_in'].print_all_messages()



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

# Run tests
if __name__ == '__main__':
    unittest.main()
