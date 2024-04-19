from gpu import *
from debug_utility import *

gpu_controller = GPU_Controller(256, 2,16, 1024, "gpu_0.txt")
gpu_debugger = gpu_debug(gpu_controller)
# gpu_debugger.print_barrier_map()
# gpu_controller.update_barrier(0)
# gpu_debugger.print_barrier_map()

# cycle 0
gpu_controller.GPU_run()
gpu_debugger.print_gpu_info()
gpu_debugger.print_GPU_cache_set(128)
gpu_controller.take_generated_msg()
gpu_controller.GPU_POST_RUN()
gpu_debugger.print_Inst_Buffer()
gpu_debugger.print_gpu_wait()

# cycle 1
gpu_controller.GPU_run()
gpu_debugger.print_gpu_info()
gpu_debugger.print_GPU_cache_set(128)
gpu_controller.take_generated_msg()
gpu_controller.GPU_POST_RUN()
gpu_debugger.print_Inst_Buffer()
gpu_debugger.print_gpu_wait()

# cycle 2
gpu_controller.GPU_run()
gpu_debugger.print_gpu_info()
gpu_debugger.print_GPU_cache_set(128)
gpu_debugger.print_GPU_cache_set(37)
gpu_controller.take_generated_msg()
gpu_controller.GPU_POST_RUN()
gpu_debugger.print_Inst_Buffer()
gpu_debugger.print_gpu_wait()

# cycle 3
msg = Msg(msg_type.RepV, 128, Node.LLC, Node.GPU)
gpu_controller.receieve_rep_msg(msg)
gpu_controller.GPU_run()
gpu_debugger.print_gpu_info()
gpu_debugger.print_GPU_cache_set(128)
# gpu_controller.take_generated_msg()
gpu_controller.GPU_POST_RUN()
gpu_debugger.print_Inst_Buffer()
gpu_debugger.print_gpu_wait()

# cycle 4
gpu_controller.update_barrier(0)
gpu_controller.GPU_run()
gpu_debugger.print_gpu_info()
gpu_debugger.print_GPU_cache_set(128)
gpu_controller.take_generated_msg()
gpu_controller.GPU_POST_RUN()
gpu_debugger.print_Inst_Buffer()
gpu_debugger.print_gpu_wait()

# cycle 5
msg = Msg(msg_type.RepWT, 128, Node.LLC, Node.GPU)
gpu_controller.receieve_rep_msg(msg)
gpu_controller.GPU_run()
gpu_debugger.print_gpu_info()
gpu_debugger.print_GPU_cache_set(128)
#gpu_controller.take_generated_msg()
gpu_controller.GPU_POST_RUN()
gpu_debugger.print_Inst_Buffer()
gpu_debugger.print_gpu_wait()

# cycle 6
gpu_controller.GPU_run()
gpu_debugger.print_gpu_info()
gpu_debugger.print_GPU_cache_set(128)
gpu_controller.take_generated_msg()
gpu_controller.GPU_POST_RUN()
gpu_debugger.print_Inst_Buffer()
gpu_debugger.print_barrier_map()
gpu_debugger.print_gpu_wait()

# cycle 7
gpu_controller.GPU_run()
gpu_debugger.print_gpu_info()
gpu_debugger.print_GPU_cache_set(128)
gpu_controller.take_generated_msg()
gpu_controller.GPU_POST_RUN()
gpu_debugger.print_Inst_Buffer()
gpu_debugger.print_barrier_map()
gpu_debugger.print_gpu_wait()

# cycle 8
# gpu_controller.update_barrier(0)
gpu_controller.GPU_run()
gpu_debugger.print_gpu_info()
gpu_debugger.print_GPU_cache_set(128)
gpu_controller.take_generated_msg()
gpu_controller.GPU_POST_RUN()
gpu_debugger.print_Inst_Buffer()
gpu_debugger.print_barrier_map()
gpu_debugger.print_gpu_wait()

# cycle 9
gpu_controller.GPU_run()
gpu_debugger.print_gpu_info()
gpu_debugger.print_GPU_cache_set(128)
gpu_controller.take_generated_msg()
gpu_controller.GPU_POST_RUN()
gpu_debugger.print_Inst_Buffer()
gpu_debugger.print_barrier_map()
gpu_debugger.print_gpu_wait()