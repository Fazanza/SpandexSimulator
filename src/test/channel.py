#not used just for testing
class Channel:
    def __init__(self):
        self.queue = []

    def is_empty(self):
        return len(self.queue) == 0

    def peek(self):
        if not self.is_empty():
            return self.queue[0]
        return None

    def dequeue(self):
        if not self.is_empty():
            return self.queue.pop(0)
        return None

class CommunicationSystem:
    def __init__(self):
        self.channels = {
            'request_out': Channel(),
            'response_out': Channel()
        }
        self.last_peeked_channel = None  # To remember which channel was last peeked

    def get_generated_msg(self):
        if not self.channels['response_out'].is_empty():
            self.last_peeked_channel = 'response_out'
            return self.channels['response_out'].peek()
        elif not self.channels['request_out'].is_empty():
            self.last_peeked_channel = 'request_out'
            return self.channels['request_out'].peek()
        else:
            self.last_peeked_channel = None
            return None

    def take_generated_msg(self):
        if self.last_peeked_channel and not self.channels[self.last_peeked_channel].is_empty():
            return self.channels[self.last_peeked_channel].dequeue()
        return None


