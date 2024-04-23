from globals import Trace
from globals import traces
from globals import CACHE_SIZE
from globals import BLOCK_SIZE

class Core:
    def __init__(self, _id: int):
        self.id = _id
        self.cache_capacity = CACHE_SIZE
        self.block_size = BLOCK_SIZE

    '''
    Returns whether data accessed by X will still be in the cache
    when access Y is executed (true only if number of unique bytes
    accessed between X and Y is less than 75% of cache capacity)
    '''

    @staticmethod
    def reuse_possible(t1: Trace, t2: Trace) -> bool:
        assert (t1.core == t2.core)
        if t1.index > t2.index:
            return Core.reuse_helper(t1, t2.index)
        return Core.reuse_helper(t2, t1.index)

    '''
    T2 is the larger trace index, goes from T2 to index and sees
    how many times it finds a address that doesn't match the other 
    address
    '''
    @staticmethod
    def reuse_helper(t2: Trace, index: int) -> bool:
        usedAddrs = {t2.addr}
        count = t2.index
        while count >= index + 1:
            count = count - 1
            if traces[count].core != t2.core:
                continue
            if traces[count].addr in usedAddrs:
                continue
            usedAddrs.add(traces[count].addr)
            if len(usedAddrs) > (CACHE_SIZE * 0.75):
                return False
        return True
