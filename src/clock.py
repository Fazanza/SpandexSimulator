class Clock:
    def __init__(self, frequency=100, start_time=0, callback= None):
        self.tick = start_time # global counter
        self.cycle = 0
        self.frequency = frequency  # Frequency in Hz
        self.clock_period = 1.0 / frequency  # Clock period calculated from frequency
        self.observers = []
        self.callback = callback

    def clockPeriod(self):
        return self.clock_period

    def currentTick(self):
        # Placeholder for a global tick function
        return self.tick

    def update(self):
        self.tick += self.clockPeriod()
        self.cycle += 1
        # self.notify_observers()
        if self.callback:
            self.callback(self.tick)

    def clockEdge(self, cycles=0):
        self.update()
        return self.tick + self.clockPeriod() * cycles
    
    def curCycle(self):
        return self.cycle

    def nextCycle(self):
        return self.clockEdge(1)
    
    ## for updating tick increase
    # def register_callback(self, callback):
    #     self.callback = callback  # Method to set the callback

    def register_observer(self, observer):
        self.observers.append(observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.update(self.tick)
            print(observer)


# clock = Clock()
# clock.clockEdge()
# print("Current tick:", clock.currentTick())  # Output the current global tick
# clock.clockEdge()
# print("Current tick:", clock.currentTick())  # Output the current global tick
# clock.clockEdge()
# clock.clockEdge()
# clock.clockEdge()
# clock.clockEdge()
# print("Current tick:", clock.currentTick())  # Output the current global tick

# for i in range(100):
#     clock.clockEdge()
#     print("Current tick:", clock.currentTick())  # Output the current global tick
