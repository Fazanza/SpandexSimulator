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
