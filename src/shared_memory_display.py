from multiprocessing import Lock, Value, Queue
from multiprocessing.managers import BaseProxy
from ctypes import c_bool
from collections import defaultdict

class SharedMemoryDisplay:

    def __init__(self):

        self.camera_container = defaultdict(lambda: None)
        self.counter = Value('i', 0)
    
    def add_frame(self, camera_id, frame, frame_properties):
    
        self.camera_container[camera_id] = (camera_id, frame, frame_properties)

    def get_frame(self):

        # Can be converted into an yield output

        if len(self.camera_container) <= 0:
            return None

        with self.counter.get_lock():
            next_index = self.counter.value % len(self.camera_container)
            self.counter.value = self.counter.value + 1
        key = list(self.camera_container.keys())[next_index]
        prop = self.camera_container[key]

        return prop

    def debug(self, process_name):
        
        print(self)
        print(process_name)
        print(self.camera_container)

    def __len__(self):
        return len(self.camera_container)

class SharedMemoryDisplayProxy(BaseProxy):

    _exposed_ = ('add_frame', 'get_frame', 'debug', '__len__')

    def add_frame(self, camera_id, frame, frame_properties):
        try:
            return self._callmethod('add_frame', (camera_id, frame, frame_properties))
        except Exception as e:
            pass

    def get_frame(self):
        return self._callmethod('get_frame')
    
    def debug(self, process_name):
        return self._callmethod('debug', (process_name,))

    def __len__(self):
        return self._callmethod('__len__')