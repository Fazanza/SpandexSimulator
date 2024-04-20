from utility.global_utility import *

class msg_classify:
    msg_map = {
        msg_type.ReqV       :       msg_class.Request   ,
        msg_type.ReqS       :       msg_class.Request   ,
        msg_type.ReqWT      :       msg_class.Request   ,
        msg_type.ReqOdata   :       msg_class.Request   ,
        msg_type.ReqWB      :       msg_class.Request   ,
        msg_type.InvAck     :       msg_class.Response  ,
        msg_type.RepRvkO    :       msg_class.Response  ,
        msg_type.RepFwdV    :       msg_class.Response  ,
        msg_type.RepFwdV_E  :       msg_class.Response  ,
        msg_type.RepS       :       msg_class.Response  ,
        msg_type.RepV       :       msg_class.Response  ,
        msg_type.RepWT      :       msg_class.Response  ,
        msg_type.RepWB      :       msg_class.Response  ,
        msg_type.RepOdata   :       msg_class.Response  ,
        msg_type.FwdReqS    :       msg_class.Request   ,
        msg_type.FwdReqV    :       msg_class.Request   ,
        msg_type.FwdReqV_E  :       msg_class.Request   ,
        msg_type.FwdReqOdata:       msg_class.Request   ,
        msg_type.FwdRvkO    :       msg_class.Request   ,
        msg_type.Inv        :       msg_class.Request   ,
        msg_type.FwdGetS    :       msg_class.Request   ,
        msg_type.FwdGetM    :       msg_class.Request   ,
        msg_type.DataDir    :       msg_class.Response  ,
        msg_type.DataOwner  :       msg_class.Response  ,
        msg_type.PutAck     :       msg_class.Response  
    }
    

    def get_value(self, Msg_type):
        if Msg_type in self.msg_map:
            return self.msg_map[Msg_type]
        else:
            print(f"msg_type {Msg_type} not found in msg map.")
            quit()
