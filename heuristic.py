from trace import Trace
from trace import ProcType
from trace import Helper
from core import Core

'''
Returns true if ownership for t1 is likely to improve overall performance
Basically checks whether t1 obtaining ownership will help or hurt performance for t2
'''


def owner_benefit(t1: Trace) -> bool:
    phase: int = 5
    x_score: int = 0
    t2: Trace = Helper.next_conflict(t1)
    t2_prev: Trace = t1
    prevList: Trace = t1
    while t2:
        if Helper.diff_core(t2_prev, t2) or Helper.sync_possible(t2_prev, t2):
            phase = phase - 1

            if phase < 0 or (Helper.same_core(t1, t2) and not Core.reuse_possible(t1, t2)):
                break

            y_val = 0
            if Helper.same_core(t2, prevList):
                y_val = 2 * Helper.criticality(t2)
            else:
                y_val = 0.5 * Helper.criticality(t2)

            if Helper.same_core(t1, t2):
                x_score = x_score + y_val
            else:
                x_score = x_score - y_val
                prevList = t2

        t2_prev = t2
        t2 = Helper.next_conflict(t2)

    if x_score > 0:
        return True
    return False


'''
Returns true if obtaining shared state for t1 would improve performance
based on expected reuse effects. Assume that obtaining shared state is
beneficial if the issuing core is a CPU and it can lead to at least one
future cache hit
'''


def shared_state_benefit(t1: Trace) -> bool:
    if t1.proctype == ProcType.GPU:
        return False
    t2: Trace = Helper.next_block_conflict(t1)
    t2_prev: Trace = t1
    while t2:
        if Helper.diff_core(t2_prev, t2) or Helper.sync_possible(t2_prev, t2):
            if Helper.is_load(t2) and Helper.same_core(t1, t2):
                return True
            if Helper.is_store(t2) and Helper.diff_core(t1, t2):
                return False
        t2_prev = t2
        t2 = Helper.next_block_conflict(t2)
    return False


'''
Return true if using owner prediction is likely to be successful for the
given prediction mechanism based on execution history
'''


def owner_pred_benefit(t1: Trace) -> bool:
    x_score: int = 0
    phase: int = 4
    t1_prev: Trace = Helper.prev_conflict(t1)
    t2: Trace = Helper.prev_acc(t1)
    while t2:
        t2_prev: Trace = Helper.prev_conflict(t2)
        if Helper.same_core(t1, t2) and Helper.same_inst(t1, t2):
            phase = phase - 1

            if phase < 0:
                break

            if Helper.same_core(t2_prev, t1_prev):
                x_score = x_score + 1
            else:
                x_score = x_score - 1
        t2 = Helper.prev_acc(t2)

    if x_score > 0:
        return True
    return False
