class MessageBuffer:
    def __init__(self, max_size):
        self.max_size = max_size
        self.buffer = []

    def __str__(self):
        return "Buffer Contents: " + ", ".join(map(str, self.buffer))

    def enqueue(self, message):
        if len(self.buffer) < self.max_size:
            self.buffer.append(message)
        else:
            print("Buffer is full. Unable to enqueue message:", message)

    def dequeue(self):
        if self.buffer:
            return self.buffer.pop(0)
        else:
            print("Buffer is empty. Unable to dequeue.")

    def is_empty(self):
        return len(self.buffer) == 0

    def clear(self):
        self.buffer.clear()

    def size(self):
        return len(self.buffer)
    

# testing
buffer = MessageBuffer(10)
buffer.enqueue("msg1")
buffer.enqueue("msg2")
buffer.dequeue()
buffer.enqueue("msg3")
buffer.enqueue("msg4")
print(buffer)
# buffer.dequeue()
# buffer.dequeue()
# buffer.dequeue()
# buffer.dequeue()
