from eventlet import queue

__all__ = ['Empty', 'Full', 'LifoQueue', 'PriorityQueue', 'Queue']

__patched__ = ['LifoQueue', 'PriorityQueue', 'Queue']

# these classes exist to paper over the major operational difference between
# eventlet.queue.Queue and the stdlib equivalents


class Queue(queue.Queue):
    def __init__(self, maxsize=0):
        if maxsize == 0:
            maxsize = None
        super().__init__(maxsize)


class PriorityQueue(queue.PriorityQueue):
    def __init__(self, maxsize=0):
        if maxsize == 0:
            maxsize = None
        super().__init__(maxsize)


class LifoQueue(queue.LifoQueue):
    def __init__(self, maxsize=0):
        if maxsize == 0:
            maxsize = None
        super().__init__(maxsize)


Empty = queue.Empty
Full = queue.Full
