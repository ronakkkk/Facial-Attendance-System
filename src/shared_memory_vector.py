from multiprocessing import Lock, Value
from multiprocessing.managers import BaseProxy
from ctypes import c_bool

from .database import VectorCache

class SharedMemoryVector(VectorCache):

    def __init__(self, db_file=None):

        super().__init__(db_file=db_file)

        self.lock = Lock()
        self.is_locked = False
        self.counter = Value('i', 0)
    
    def match_faces(self, descriptors):

        while self.is_locked:
            pass

        with self.counter.get_lock():
            self.counter.value += 1

        ret_value = self._match_faces(descriptors)

        with self.counter.get_lock():
            self.counter.value -= 1

        return ret_value
    
    def set_up_db(self, db_file=None):

        self.lock.acquire()
        self.is_locked = True

        print('SharedMemoryVector',db_file)

        while self.counter.value > 0:
            pass

        self._set_up_db(db_file=db_file)

        self.lock.release()
        self.is_locked = False
    
    def debug(self):
        print(self.database)


class SharedMemoryVectorProxy(BaseProxy):
    
    _exposed_ = ('match_faces', 'set_up_db', 'debug', 'check_if_label_exists', '__getitem__')

    def match_faces(self, descriptors):
        return self._callmethod('match_faces', (descriptors,))
    
    def set_up_db(self, db_file=None):
        return self._callmethod('set_up_db', (db_file,))
    
    def debug(self):
        return self._callmethod('debug')

    def __getitem__(self, idx):
        return self._callmethod('__getitem__', (idx,))