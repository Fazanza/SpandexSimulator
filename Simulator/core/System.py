from utility.global_utility import *
from core.msg_classify import *

class System:
    def __init__(self, Device_Map, Device_List, Core_List, CPU_List, GPU_List, TPU):
        self.Device_Map = Device_Map
        self.Device_List = Device_List
        self.Core_List = Core_List
        self.CPU_List = CPU_List
        self.GPU_List = GPU_List
        self.TPU = TPU # used to translate request between CPU and LLC
        self.MsgClassify = msg_classify()
        self.system_clk = 0
        self.is_finish = False
    
    def get_clk(self):
        return self.system_clk
    
    def round_robin(queue):
        temp = queue[0]
        for i in range(1, len(queue)):
            queue[i-1] = queue[i]
        queue[len(queue)-1] = temp
        return queue

    def is_member(self, element, list):
        return element in list
    
    ### Every Node do not require any msg, it just send msg to the other Node
    ### when Every Node run, it just read it's own req and rep queue
    def LLC_RUN(self, LLC_Node):
        LLC = self.Device_Map.search(LLC_Node)
        LLC.LLC_run()
        while LLC.get_generated_msg() != None:
            generated_msg = LLC.get_generated_msg()
            msg_class = self.MsgClassify.get_value(generated_msg.msg_type)
            #
            if msg_class == msg_class.Request: # send request to other Node
                assert(generated_msg.dst != Node.GPU), "Error! LLC is sending request to GPU"
                self.Device_Map.search(generated_msg.dst).receieve_req_msg(self.TPU.translate_msg(generated_msg))
                LLC.take_generated_msg() # pop from LLC generated_msg_queue
            #
            elif msg_class == msg_class.Response: # send response to other Node
                if self.is_member(generated_msg.dst, self.GPU_List):
                    self.Device_Map.search(generated_msg.dst).receieve_rep_msg(generated_msg)
                elif self.is_member(generated_msg.dst, self.CPU_List):
                    self.Device_Map.search(generated_msg.dst).receieve_rep_msg(self.TPU.translate_msg(generated_msg))
                LLC.take_generated_msg() # pop from LLC generated_msg_queue
    
    def GPU_RUN(self, GPU_Node):
        GPU = self.Device_Map.search(GPU_Node)
        GPU.GPU_run()
        # do barrier
        GPU_barrier = GPU.get_barrier()
        if GPU_barrier != None:
            for CPU in self.CPU_List:
                self.Device_Map.search(CPU).update_barrier(GPU_barrier)
        # do generate msg
        if GPU.get_generated_msg() != None:
            generated_msg = GPU.get_generated_msg()
            msg_class = self.MsgClassify.get_value(generated_msg.msg_type)
            assert msg_class == msg_class.Request, "Error! GPU is generated Response type of msg"
            assert generated_msg.dst == Node.LLC, "Error! GPU is sending Request to Node other than LLC"
            req_msg_taken = self.Device_Map.search(Node.LLC).receieve_req_msg # check if LLC req_msg_box has enough space to enqueue
            if req_msg_taken == True:
                GPU.take_generated_msg()
        GPU.GPU_POST_RUN()
    
    def CPU_RUN(self, CPU_Node):
        CPU = self.Device_Map.search(CPU_Node)
        CPU.CPU_run()
        # do barrier
        CPU_barrier = CPU.get_barrier()
        if CPU_barrier != None:
            for GPUs in self.GPU_List:
                self.Device_Map.search(GPUs).update_barrier(CPU_barrier)
            for CPUs in self.CPU_List:
                if self.Device_Map.search(CPUs) != CPU:
                    self.Device_Map.search(CPUs).update_barrier(CPU_barrier)

        # do generate msg
        while CPU.get_generated_msg() != None:
            generated_msg = CPU.get_generated_msg()
            msg_class = self.MsgClassify.get_value(generated_msg.msg_type)
            
            if msg_class == msg_class.Request: # send request to other Node
                assert(generated_msg.dst == Node.LLC), "Error! CPU is sending request to Node other than LLC"
                if self.Device_Map.search(Node.LLC).receieve_req_msg(self.TPU.translate_msg(generated_msg)) == True:
                    CPU.take_generated_msg() # pop from LLC generated_msg_queue
            #
            elif msg_class == msg_class.Response: # send response to other Node
                if self.is_member(generated_msg.dst, self.CPU_List):
                    self.Device_Map.search(generated_msg.dst).receieve_rep_msg(generated_msg)
                else:
                    self.Device_Map.search(generated_msg.dst).receieve_rep_msg(self.TPU.translate_msg(generated_msg))
                CPU.take_generated_msg() # pop from LLC generated_msg_queue
        CPU.CPU_POST_RUN()

    def SYSTEM_RUN(self):
        # Run 
        while True:
            self.is_finish = True
            for core in self.Core_List:
                self.is_finish = self.is_finish and self.Device_Map.search(core).is_finish()
            if self.is_finish == True:
                print("All Program Finish ! ! !")
                return 0

            for core in self.Core_List:
                if self.is_member(core, self.CPU_List):
                    self.CPU_RUN(core)
                elif self.is_member(core, self.GPU_List):
                    self.GPU_RUN(core)
            self.LLC_RUN(Node.LLC)

            self.Core_List = self.round_robin(self.Core_List)
            self.system_clk = self.system_clk + 1

# ### Every Node do not require any msg, it just send msg to the other Node
# ### when Every Node run, it just read it's own req and rep queue
# def LLC_RUN(LLC_Node, Device_map, TPU, Msg_Classify, GPU_List, CPU_List):
#     LLC = Device_map.search(LLC_Node)
#     LLC.LLC_run()
#     while LLC.get_generated_msg() != None:
#         generated_msg = LLC.get_generated_msg()
#         msg_class = Msg_Classify.get_value(generated_msg.msg_type)
#         #
#         if msg_class == msg_class.Request: # send request to other Node
#             assert(generated_msg.dst != Node.GPU), "Error! LLC is sending request to GPU"
#             Device_map.search(generated_msg.dst).receieve_req_msg(TPU.translate_msg(generated_msg))
#             LLC.take_generated_msg() # pop from LLC generated_msg_queue
#         #
#         elif msg_class == msg_class.Response: # send response to other Node
#             if is_member(generated_msg.dst, GPU_List):
#                 Device_map.search(generated_msg.dst).receieve_rep_msg(generated_msg)
#             elif is_member(generated_msg.dst, CPU_List):
#                 Device_map.search(generated_msg.dst).receieve_rep_msg(TPU.translate_msg(generated_msg))
#             LLC.take_generated_msg() # pop from LLC generated_msg_queue

# def GPU_RUN(GPU_Node, Device_map, Msg_Classify, CPU_List):
#     GPU = Device_map.search(GPU_Node)
#     GPU.GPU_run()
#     # do barrier
#     GPU_barrier = GPU.get_barrier()
#     if GPU_barrier != None:
#         for CPU in CPU_List:
#             Device_map.search(CPU).update_barrier(GPU_barrier)
#     # do generate msg
#     if GPU.get_generated_msg() != None:
#         generated_msg = GPU.get_generated_msg()
#         msg_class = Msg_Classify.get_value(generated_msg.msg_type)
#         assert msg_class == msg_class.request, "Error! GPU is generated Response type of msg"
#         assert generated_msg.dst == Node.LLC, "Error! GPU is sending Request to Node other than LLC"
#         req_msg_taken = Device_map.search(Node.LLC).receieve_req_msg # check if LLC req_msg_box has enough space to enqueue
#         if req_msg_taken == True:
#             GPU.take_generated_msg()
#         GPU.GPU_POST_RUN()

# def CPU_RUN(CPU_Node, Device_map, TPU, Msg_Classify, GPU_List, CPU_List):
#     CPU = Device_map.search(CPU_Node)
#     CPU.runCPU()
#     # do barrier
#     CPU_barrier = CPU.get_barrier()
#     if CPU_barrier != None:
#         for GPU in GPU_List:
#             Device_map.search(GPU).update_barrier(CPU_barrier)
#         for CPUs in CPU_List:
#             if Device_map.search(CPUs) != CPU:
#                 Device_map.search(CPUs).update_barrier(CPU_barrier)

#     # do generate msg
#     while CPU.get_generated_msg() != None:
#         generated_msg = CPU.get_generated_msg()
#         msg_class = Msg_Classify.get_value(generated_msg.msg_type)
        
#         if msg_class == msg_class.Request: # send request to other Node
#             assert(generated_msg.dst == Node.LLC), "Error! CPU is sending request to Node other than LLC"
#             if Device_map.search(Node.LLC).receieve_req_msg(TPU.translate_msg(generated_msg)) == True:
#                 CPU.take_generated_msg() # pop from LLC generated_msg_queue
#         #
#         elif msg_class == msg_class.Response: # send response to other Node
#             if is_member(generated_msg.dst, CPU_List):
#                 Device_map.search(generated_msg.dst).receieve_rep_msg(generated_msg)
#             else:
#                 Device_map.search(generated_msg.dst).receieve_rep_msg(TPU.translate_msg(generated_msg))
#             CPU.take_generated_msg() # pop from LLC generated_msg_queue