from multiprocessing import Lock, Value
from multiprocessing.managers import BaseProxy
from ctypes import c_bool

from .database import IdentityCache

class SharedMemoryIdentity(IdentityCache):

    def __init__(self, db_file=None):
        super().__init__(db_file=db_file)
        self.lock = Lock()
        self.is_locked = False
        self.counter = Value('i', 0)

    def find_identity(self, label):

        while self.is_locked:
            pass

        with self.counter.get_lock():
            self.counter.value += 1

        ret_value = self._find_identity(label=label)

        with self.counter.get_lock():
            self.counter.value -= 1

        return ret_value

    def load_people_list(self, db_file=None):

        self.lock.acquire()
        self.is_locked = True

        while self.counter.value > 0:
            pass

        # print('shared memory identity.py', self.database, db_file)
        self._set_up_db(db_file=db_file)

        self.is_locked = False  # It is placed before release,
                                # Because, there will be in-consistancy 
                                # in two consecutive load_people_list call.
        self.lock.release()
    
    def debug(self):
        print(self.database)


class SharedMemoryIdentityProxy(BaseProxy):
    
    _exposed_ = ('find_identity', 'load_people_list', 'debug')

    def find_identity(self, label):
        return self._callmethod('find_identity', (label, ))
    
    def load_people_list(self, db_file=None):
        return self._callmethod('load_people_list', (db_file, ))
    
    def debug(self):
        return self._callmethod('debug')