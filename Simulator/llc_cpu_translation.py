from enum import Enum, auto
import random
from collections import deque
from llc_utility import *
from global_utility import *
from llc import *
from llc_cpu_translation import *

class Translation:
    translation_map = {
        msg_type.FwdReqS       :   msg_type.FwdGetS     ,
        msg_type.FwdReqV       :   msg_type.FwdGetS     ,
        msg_type.FwdReqV_E     :   msg_type.FwdGetM     ,
        msg_type.FwdReqOdata   :   msg_type.FwdGetM     ,
        msg_type.FwdRvkO       :   msg_type.FwdGetM     ,
        msg_type.Inv           :   msg_type.Inv         ,
        msg_type.Data          :   msg_type.RepRvkO     ,
        msg_type.Data_V        :   msg_type.RepFwdV     ,
        msg_type.DataOwner     :   msg_type.RepRvkO     ,
        msg_type.DataOwner_V   :   msg_type.RepFwdV_E   ,
        msg_type.InvAck        :   msg_type.InvAck      ,
        msg_type.GetS          :   msg_type.ReqS        ,
        msg_type.GetM          :   msg_type.ReqOdata    ,
        msg_type.PutM          :   msg_type.ReqWB       ,
        msg_type.RepS          :   msg_type.DataDir     ,
        msg_type.RepOdata      :   msg_type.DataDir     ,
        msg_type.RepWB         :   msg_type.PutAck
    }
    
    def __init__(self, llc):
        self.llc = llc
    
    def State_preProcess(self, Msg_type, addr): # typically used for distinguish between reply RepFwdV
        if Msg_type == msg_type.Data:
            if self.llc.cache.getState_line(addr) == State.OS:
                return msg_type.Data_V
            else:
                return msg_type.Data
        elif Msg_type== msg_type.DataOwner:
            if self.llc.cache.getState_line(addr) == State.OV:
                return msg_type.DataOwner_V
            else:
                return msg_type.DataOwner
        
    def get_value(self, Msg_type, addr):
        real_msg_type = self.State_preProcess(Msg_type, addr)
        if real_msg_type in self.translation_map:
            return self.translation_map[real_msg_type]
        else:
            return " msg_type not found in translation map."