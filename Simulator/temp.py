def CPU_RUN(self, CPU_Node):
    CPU = self.Device_Map.search(CPU_Node)
    CPU.runCPU()
    # do barrier
    CPU_barrier = CPU.get_barrier()
    if CPU_barrier != None:
        for GPU in self.GPU_List:
            self.Device_Map.search(GPU).update_barrier(CPU_barrier)
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