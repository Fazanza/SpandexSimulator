class MessageBuffer:
    def __init__(self, max_size, min_delay, max_delay):
        self.max_size = max_size
        self.buffer = []
        self.min_delay = min_delay
        self.max_delay = max_delay

    def enqueue(self, message):
        if len(self.buffer) < self.max_size:
            self.buffer.append(message)

    def dequeue(self):
        if self.buffer:
            return self.buffer.pop(0)

    def is_empty(self):
        return len(self.buffer) == 0
    
    ## return a list of elemenr which has timestamp + max_delay < current_time_stamp
    def find_latest_element(self, current_time):
        temp = []
        latest = None
        for item in self.buffer:
            if item.time_stamp + self.max_delay < current_time:
                temp.append(item)
        for item in temp:
            if latest == None:
                latest = item
            elif latest.time_stamp < item.time_stamp:
                latest = item
        return latest
    
    def find_qualify_element(self, current_time):
        temp = []
        for item in self.buffer:
            if item.time_stamp + self.min_delay < current_time:
                temp.append(item)
        return temp
    
    def get_content(self):
        return self.buffer

    def pick(self, current_time):
        selected_element = self.find_latest_element(current_time)
        if selected_element!= None:
            self.buffer.remove(selected_element)
            return selected_element
        qualify_list = self.find_qualify_element(current_time)
        if len(self.qualify_list) != 0:
            selected_element = random.choice(qualify_list)
            self.buffer.remove(selected_element)
            return selected_element
        return None
    
    def is_full(self):
        if len(self.buffer) < self.max_size:
            return True
        else:
            return False

    def peek(self):
        if not self.is_empty():
            return self.buffer[0]
        else:
            raise IndexError("peek from an empty queue")

    def clear(self):
        self.buffer.clear()

    def size(self):
        return len(self.buffer)