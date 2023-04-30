from multiprocessing import Lock, Value, Queue
from multiprocessing.managers import BaseProxy
from ctypes import c_bool

class SharedMemoryDB:
    
    def __init__(self):
        self.query_container = Queue()

    def add_query(self, query_tuple):
        self.query_container.put(query_tuple)
    
    def get_query(self):
        
        prop = None

        try:
            prop = self.query_container.get(block=False)
        except Exception as e:
            pass

        return prop

class SharedMemoryDBProxy(BaseProxy):
    
    _exposed_ = ('add_query', 'get_query')

    def add_query(self, query_tuple):
        try:
            return self._callmethod('add_query', (query_tuple,))
        except:
            pass
        
    def get_query(self):
        return self._callmethod('get_query')