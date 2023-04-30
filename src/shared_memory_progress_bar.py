from multiprocessing import Value
from multiprocessing.managers import BaseProxy
from collections import defaultdict

class SharedMemoryProgressBar:
    
    def __init__(self):
        self.counter = defaultdict(int)
        self.frame_counts = defaultdict(int)

    def set_frame_count(self, idx, frame_count):
        self.frame_counts[idx] = frame_count

    def increment(self, idx):
        self.counter[idx] += 1

    def get_frame_count(self, idx):
        val = 0
        if idx in self.frame_counts:
            val = self.frame_counts[idx]
        return val

    def get_count(self, idx):
        val = 0
        if idx in self.counter:
            val = self.counter[idx]
        return val
    
    def drop(self, idx):
        self.counter.pop(idx)
        self.frame_counts.pop(idx)
    
    def debug(self):
        print('counter:', self.counter)
        print('frame_counts:', self.frame_counts)

class SharedMemoryProgressBarProxy(BaseProxy):

    _exposed_ = ('set_frame_count', 'increment', 'get_frame_count', 'get_count', 'drop', 'debug')

    def set_frame_count(self, idx, frame_count):
        return self._callmethod('set_frame_count', (idx, frame_count))

    def increment(self, idx):
        return self._callmethod('increment', (idx,))
    
    def get_frame_count(self, idx):
        return self._callmethod('get_frame_count', (idx,))

    def get_count(self, idx):
        return self._callmethod('get_count', (idx,))
    
    def drop(self, idx):
        return self._callmethod('drop', (idx,))
    
    def debug(self):
        return self._callmethod('debug')