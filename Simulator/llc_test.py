from llc import *
from debug_utility import*

llc_controller = LLC_Controller(256, 2,16, 1024, 10, 1, 3, 3)
llc_debugger = llc_debug(llc_controller)

msg1 = Msg(msg_type.ReqV, 128, Node.GPU, Node.LLC, 0, Node.NULL)
msg2 = Msg(msg_type.ReqV, 128, Node.GPU, Node.LLC, 0, Node.NULL)
msg3 = Msg(msg_type.ReqOdata, 37, Node.CPU1, Node.LLC, 0, Node.NULL)
msg4 = Msg(msg_type.ReqOdata, 256, Node.CPU2, Node.LLC, 0, Node.NULL)
msg5 = Msg(msg_type.ReqOdata, 384, Node.CPU3, Node.LLC, 0, Node.NULL)
msg6 = Msg(msg_type.ReqOdata, 512, Node.GPU, Node.LLC, 0, Node.NULL)
msg7 = Msg(msg_type.ReqS, 640, Node.CPU0, Node.LLC, 0, Node.NULL)

# llc_controller.receieve_req_msg(msg_type.ReqV, 128, Node.GPU, Node.LLC, 0, Node.NULL)
# llc_controller.receieve_req_msg(msg_type.ReqS, 128, Node.CPU0, Node.LLC, 0, Node.NULL)
llc_controller.receieve_req_msg(msg3)
llc_controller.receieve_req_msg(msg4)
llc_controller.receieve_req_msg(msg5)
llc_controller.receieve_req_msg(msg6)
llc_controller.receieve_req_msg(msg7)
llc_controller.req_msg_box.print_all()

# clk 0
print()
llc_controller.LLC_run()
llc_debugger.print_current_msg()

# clk 1
print()
llc_controller.LLC_run()
llc_debugger.print_current_msg()

# clk 2
print()
llc_controller.LLC_run()
llc_debugger.print_current_msg()
llc_debugger.print_LLC_cache_set(128)
llc_debugger.print_LLC_cache_set(37)
llc_debugger.print_LLC_generated_msg_queue()
# llc_debugger.print_LLC_mem_queue()

# clk 3
print()
llc_controller.LLC_run()
llc_debugger.print_current_msg()
llc_debugger.print_LLC_cache_set(128)
llc_debugger.print_LLC_cache_set(37)
llc_debugger.print_LLC_generated_msg_queue()

# clk 4
print()
llc_debugger.print_LLC_request_box()
llc_controller.LLC_run()
llc_debugger.print_current_msg()
llc_debugger.print_LLC_cache_set(128)
llc_debugger.print_LLC_cache_set(37)
llc_debugger.print_LLC_generated_msg_queue()

# clk 5
print()
llc_debugger.print_LLC_request_box()
llc_controller.LLC_run()
llc_debugger.print_current_msg()
llc_debugger.print_LLC_cache_set(128)
llc_debugger.print_LLC_cache_set(37)
llc_debugger.print_LLC_generated_msg_queue()


# clk 6
print()
llc_debugger.print_LLC_request_box()
llc_controller.LLC_run()
llc_debugger.print_current_msg()
print()
llc_debugger.print_LLC_cache_set(128)
llc_debugger.print_LLC_cache_set(37)
llc_debugger.print_LLC_generated_msg_queue()

# clk 7
print()
#llc_controller.receieve_rep_msg(msg_type.RepFwdV, 384, Node.CPU0, Node.LLC, 0, Node.NULL)
llc_debugger.print_LLC_request_box()
llc_controller.LLC_run()
llc_debugger.print_current_msg()
print()
llc_debugger.print_LLC_cache_set(128)
llc_debugger.print_LLC_cache_set(37)
llc_debugger.print_LLC_generated_msg_queue()

# clk 7
print()
llc_debugger.print_LLC_request_box()
llc_controller.LLC_run()

llc_debugger.print_current_msg()
llc_debugger.print_LLC_cache_set(128)
llc_debugger.print_LLC_cache_set(37)
llc_debugger.print_LLC_generated_msg_queue()

# clk 8
print()
llc_controller.LLC_run()
llc_debugger.print_current_msg()
llc_debugger.print_LLC_cache_set(128)
llc_debugger.print_LLC_cache_set(37)
llc_debugger.print_LLC_generated_msg_queue()

