from enum import Enum, auto
import random
from collections import deque
from utility.global_utility import *
from core.llc import *
from core.llc_cpu_translation import *

class Translation:
    translation_map = {
        msg_type.FwdReqS       :   msg_type.FwdGetS     ,
        msg_type.FwdReqV       :   msg_type.FwdGetS     ,
        msg_type.FwdReqV_E     :   msg_type.FwdGetM     , # for eviction of this addr in CPU
        msg_type.FwdReqOdata   :   msg_type.FwdGetM     , # for CPU getM when LLC in O
        msg_type.FwdRvkO       :   msg_type.FwdGetM     , # for GPU WT when LLC in O
        msg_type.Inv           :   msg_type.Inv         ,
        msg_type.Data          :   msg_type.RepRvkO     ,
        msg_type.Data_V        :   msg_type.RepFwdV     ,
        msg_type.InvAck        :   msg_type.InvAck      ,
        msg_type.GetS          :   msg_type.ReqS        ,
        msg_type.GetM          :   msg_type.ReqOdata    ,
        msg_type.PutM          :   msg_type.ReqWB       ,
        msg_type.RepS          :   msg_type.DataDir     ,
        msg_type.RepOdata      :   msg_type.DataDir     ,
        msg_type.RepWB         :   msg_type.PutAck
        # msg_type.DataOwner     :   msg_type.RepRvkO     ,
        # msg_type.DataOwner_V   :   msg_type.RepFwdV_E   ,
    }
    
    def __init__(self, llc):
        self.llc = llc
    
    def State_preProcess(self, Msg_type, addr): # typically used for distinguish between reply RepFwdV
        if Msg_type == msg_type.Data:
            if self.llc.cache.getState_line(addr) == State.OVS:
                return msg_type.Data_V
            else:
                assert self.llc.cache.getState_line(addr) == State.OS or self.llc.cache.getState_line(addr) == State.OO or self.llc.cache.getState_line(addr) == State.OV, f"Error! Data type translation fail, {self.llc.cache.getState_line(addr)}"
                return msg_type.Data
        else:
            return Msg_type
        # elif Msg_type== msg_type.DataOwner:
        #     if self.llc.cache.getState_line(addr) == State.OV:
        #         return msg_type.DataOwner_V
        #     else:
        #         return msg_type.DataOwner

        
    def translate_msg(self, input_msg):
        msg = Msg(input_msg.msg_type, input_msg.addr, input_msg.src, input_msg.dst, input_msg.ack_cnt, input_msg.fwd_dst, input_msg.target_addr)
        real_msg_type = self.State_preProcess(msg.msg_type, msg.addr)
        assert real_msg_type in self.translation_map, f"Error! msg_type {real_msg_type} not found in translation map."
        msg.msg_type = self.translation_map[real_msg_type]
        return msg