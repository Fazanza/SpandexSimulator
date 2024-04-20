from core.cpu import *
from header.cpu_header import *
from utility.cpu_debug_utility import *

cpu_controller = CPU_Controller(256, 2,16, 1024, "cpu_0.txt", Node.CPU0)
cpu_debugger = cpu_debug(cpu_controller)
cpu_controller.cache.addNewLine(384)
cpu_controller.cache.updateState_line(384, State.M)
cpu_controller.cache.renewAccess(384)

# cycle 0
cpu_controller.CPU_run()
cpu_debugger.print_cpu_info()
cpu_debugger.print_cpu_cache_set(128)
while cpu_controller.get_generated_msg() != None:
    cpu_controller.take_generated_msg()
cpu_controller.CPU_POST_RUN()
cpu_debugger.print_Inst_Buffer()
cpu_debugger.print_cpu_wait()

# cycle 1
cpu_controller.CPU_run()
cpu_debugger.print_cpu_info()
cpu_debugger.print_cpu_cache_set(128)
while cpu_controller.get_generated_msg() != None:
    cpu_controller.take_generated_msg()
cpu_controller.CPU_POST_RUN()
cpu_debugger.print_Inst_Buffer()
cpu_debugger.print_cpu_wait()

# cycle 2
cpu_controller.CPU_run()
cpu_debugger.print_cpu_info()
cpu_debugger.print_cpu_cache_set(128)
while cpu_controller.get_generated_msg() != None:
    cpu_controller.take_generated_msg()
cpu_debugger.print_cpu_cache_set(37)
cpu_controller.CPU_POST_RUN()
cpu_debugger.print_Inst_Buffer()
cpu_debugger.print_cpu_wait()

# cycle 3
msg = Msg(msg_type.DataDir, 128, Node.LLC, Node.CPU0)
cpu_controller.receieve_rep_msg(msg)
cpu_controller.CPU_run()
cpu_debugger.print_cpu_info()
cpu_debugger.print_cpu_cache_set(128)
while cpu_controller.get_generated_msg() != None:
    cpu_controller.take_generated_msg()
# cpu_controller.take_generated_msg()
cpu_controller.CPU_POST_RUN()
cpu_debugger.print_Inst_Buffer()
cpu_debugger.print_cpu_wait()

# cycle 4
cpu_controller.update_barrier(0)
cpu_controller.CPU_run()
cpu_debugger.print_cpu_info()
cpu_debugger.print_cpu_cache_set(128)
while cpu_controller.get_generated_msg() != None:
    cpu_controller.take_generated_msg()
cpu_controller.CPU_POST_RUN()
cpu_debugger.print_Inst_Buffer()
cpu_debugger.print_cpu_wait()

# cycle 5
# msg = Msg(msg_type.RepWT, 128, Node.LLC, Node.cpu)
#cpu_controller.receieve_rep_msg(msg)
cpu_controller.CPU_run()
cpu_debugger.print_cpu_info()
cpu_debugger.print_cpu_cache_set(128)
while cpu_controller.get_generated_msg() != None:
    cpu_controller.take_generated_msg()
cpu_controller.CPU_POST_RUN()
cpu_debugger.print_Inst_Buffer()
cpu_debugger.print_cpu_wait()

# cycle 6
cpu_controller.CPU_run()
cpu_debugger.print_cpu_info()
cpu_debugger.print_cpu_cache_set(128)
cpu_debugger.print_cpu_cache_set(24)
cpu_controller.CPU_POST_RUN()
cpu_debugger.print_Inst_Buffer()
cpu_debugger.print_barrier_map()
cpu_debugger.print_cpu_wait()

# cycle 7
cpu_controller.CPU_run()
cpu_debugger.print_cpu_info()
cpu_debugger.print_cpu_cache_set(128)
cpu_debugger.print_cpu_cache_set(24)
cpu_controller.CPU_POST_RUN()
cpu_debugger.print_Inst_Buffer()
cpu_debugger.print_barrier_map()
cpu_debugger.print_cpu_wait()

# cycle 8
#cpu_controller.update_barrier(0)
rep_msg = Msg(msg_type.DataDir, 128, Node.LLC, Node.CPU0)
req_msg = Msg(msg_type.FwdGetM, 384, Node.LLC, Node.CPU0, 0, Node.CPU1)
cpu_controller.receieve_rep_msg(rep_msg)
cpu_controller.receieve_req_msg(req_msg)
cpu_controller.CPU_run()
cpu_debugger.print_cpu_info()
cpu_debugger.print_cpu_cache_set(128)
cpu_controller.CPU_POST_RUN()
cpu_debugger.print_Inst_Buffer()
cpu_debugger.print_barrier_map()
cpu_debugger.print_cpu_wait()

# # cycle 9
# cpu_controller.CPU_run()
# cpu_debugger.print_cpu_info()
# cpu_debugger.print_cpu_cache_set(128)
# cpu_controller.take_generated_msg()
# cpu_controller.CPU_POST_RUN()
# cpu_debugger.print_Inst_Buffer()
# cpu_debugger.print_barrier_map()
# cpu_debugger.print_cpu_wait()