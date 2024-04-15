# Assign CPU loads and non-release atomic RMW accesses a criticality weight of 6
# Assign GPU loads and non-release atomic RMW accesses a criticality weight of 2
# Assign all other accesses a criticality weight of 1

from globals import traces
from heuristic import owner_pred_benefit

if __name__ == '__main__':
    for trace in traces:
        print(owner_pred_benefit(trace))

