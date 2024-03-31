from trace import Trace
from trace import Helper

class Core:
    def __init__(self, _id: int):
        self.id = _id

    '''
    Returns whether data accessed by X will still be in the cache
    when access Y is executed (true only if number of unique bytes
    accessed between X and Y is less than 75% of cache capacity)
    '''
    def reuse_possible(self, t1: Trace, t2: Trace) -> bool:
        return Helper.same_core(t1, t2)
