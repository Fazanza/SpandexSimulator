class inst(Enum):
    load = 1
    store = 2

c

class dataType:
    def __init__(self, inst, value, procType):
        self.inst = inst
        self.value = value
        self.procType = procType

    def getType(self):
        return self.type

    def getValue(self) -> object:
        return self.value