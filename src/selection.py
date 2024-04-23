from enum import Enum
from helper import Trace
from heuristic import owner_benefit
from heuristic import shared_state_benefit
from heuristic import owner_pred_benefit


class Type(Enum):
    ReqO_Data = 0
    ReqS = 1
    ReqVo = 2
    ReqV = 3
    ReqO = 4
    ReqWTo = 5
    ReqWTfwd = 6
    ReqWTo_Data = 7
    ReqWTfwd_Data = 8


'''
Load request type selection
'''


def load_request_type(t1: Trace) -> Type:
    if owner_benefit(t1):
        return Type.ReqO_Data
    elif shared_state_benefit(t1):
        return Type.ReqS
    elif owner_pred_benefit(t1):
        return Type.ReqVo
    else:
        return Type.ReqV


'''
Store request type selection
'''


def store_request_type(t1: Trace) -> Type:
    if owner_benefit(t1):
        return Type.ReqO
    elif owner_pred_benefit(t1):
        return Type.ReqWTo
    else:
        return Type.ReqWTfwd


'''
RMW request type selection
'''


def RMW_request_type(t1: Trace) -> Type:
    if owner_benefit(t1):
        return Type.ReqO_Data
    elif owner_pred_benefit(t1):
        return Type.ReqWTo_Data
    else:
        return Type.ReqWTfwd_Data
