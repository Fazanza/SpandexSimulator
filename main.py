# Assign CPU loads and non-release atomic RMW accesses a criticality weight of 6
# Assign GPU loads and non-release atomic RMW accesses a criticality weight of 2
# Assign all other accesses a criticality weight of 1

def isLoad(X):
    return (X.op == 'Load')

def isStore(X):
    return (X.op == 'Store')

def ownershipBeneficial(X):
    phase = 5
    xScore = 0
    Y = X
    Yprev = X
    prevList = [x]

    while Y == NextConflict(Y):
        if diffCores(YPrev, Y) or SyncSep(YPrev, Y):
            Phase = Phase - 1
            if Phase < 0 or (sa)

if __name__ == '__main__':
    print("hi")

