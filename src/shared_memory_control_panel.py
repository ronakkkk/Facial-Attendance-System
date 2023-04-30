#from multiprocessing import Value , Lock
from multiprocessing.managers import BaseProxy
from ctypes import c_bool



# Removing synchronized booelan-
# Got error : RuntimeError: Synchronized objects should only be shared between processes through inheritance
# Reasoning:
# [EXPIRATION, 
# LICENSE_MISSING, 
# INVALID_LICENSE] - will be written by one process, 
#
# [CLOSE_ALL, 
# UPDATE_CACHE, 
# MONITOR] - will be written by webapp, 
#            other process will read only
#
# [CAMERA_LIST->Display, 
# CAMERA_LIST->Recognition, 
# CAMERA_LIST->Monitor] - will also be written by webapp, 
#                         other process will read it.

class Value:
    def __init__(self, _, value):
        self.value = value

class SharedMemoryControlPanel:

    def __init__(self):

        self.EXPIRATION = Value(c_bool, False)
        self.LICENSE_MISSING = Value(c_bool, False)
        self.INVALID_LICENSE = Value(c_bool, False)
        self.CLOSE_ALL = Value(c_bool, True)
        self.UPDATE_CACHE = Value(c_bool, False)
        self.MONITOR = Value(c_bool, False)
        self.WEBAPP = Value(c_bool, False)
        self.CAMERA_LIST = dict()
        self.WELCOME_ANNOUNCEMENT = Value(c_bool, False)
        self.GUARD_ANNOUNCEMENT = Value(c_bool, False)
        self.ANNOUNCEMENT = Value(c_bool, False)

    def set_expiration(self):
        self.EXPIRATION.value = True
    
    def is_expired(self):
        return self.EXPIRATION.value
    
    def set_missing_license(self):
        self.LICENSE_MISSING.value = True
    
    def is_missing_license(self):
        return self.LICENSE_MISSING.value
    
    def set_invalid_license(self):
        self.INVALID_LICENSE.value = True
    
    def is_invalid_license(self):
        return self.INVALID_LICENSE.value
    
    def set_close_all(self):
        self.CLOSE_ALL.value = True
    
    def unset_close_all(self):
        self.CLOSE_ALL.value = False

    def is_close_all(self):
        return self.CLOSE_ALL.value
    
    def set_update_cache(self):
        self.UPDATE_CACHE.value = True
    
    def get_update_cache(self):
        return self.UPDATE_CACHE.value

    def reset_update_cache(self):
        self.UPDATE_CACHE.value = False

    def start_monitor(self):
        self.MONITOR.value = True
    
    def stop_monitor(self):
        self.MONITOR.value = False
    
    def should_display_monitor(self):
        return self.MONITOR.value
    
    def start_webapp(self):
        self.WEBAPP.value = True
    
    def stop_webapp(self):
        self.WEBAPP.value = False
    
    def should_run_webapp(self):
        return self.WEBAPP.value

    def should_stop(self):
        stop_flag = self.EXPIRATION.value | self.LICENSE_MISSING.value | self.INVALID_LICENSE.value
        return stop_flag
    
    def add_camera(self, camera_name, camera_address):

        self.CAMERA_LIST[len(self.CAMERA_LIST)] = { 'camera_name': camera_name,
                                                    'camera_address': camera_address,
                                                    'Display': False,
                                                    'Recognition': False}
        return len(self.CAMERA_LIST) - 1
    
    def get_camera_name(self, idx):
        return self.CAMERA_LIST[idx]['camera_name']
    
    def get_camera_address(self, idx):
        return self.CAMERA_LIST[idx]['camera_address']

    def stop_all_recognition(self):

        for idx in self.CAMERA_LIST:
            self.CAMERA_LIST[idx]['Recognition'] = False

    def stop_recognition(self, idx=None):

        if idx is None:
            self.stop_all_recognition()
        else:
            self.CAMERA_LIST[idx]['Recognition'] = False

    def start_all_recognition(self):

        for idx in self.CAMERA_LIST:
            self.CAMERA_LIST[idx]['Recognition'] = True

    def start_recognition(self, idx=None):
        
        if idx is None:
            self.start_all_recognition()
        else:
            self.CAMERA_LIST[idx]['Recognition'] = True

    def stop_all_display(self):

        for idx in self.CAMERA_LIST:
            self.CAMERA_LIST[idx]['Display'] = False

    def stop_display(self, idx=None):

        if idx is None:
            self.stop_all_display()
        else:
            self.CAMERA_LIST[idx]['Display'] = False
    
    def start_all_display(self):

        for idx in self.CAMERA_LIST:
            self.CAMERA_LIST[idx]['Display'] = True

    def start_display(self, idx=None):

        if idx is None:
            self.start_all_display()
        else:
            self.CAMERA_LIST[idx]['Display'] = True

    def should_display(self, idx):
        return self.CAMERA_LIST[idx]['Display']

    def should_recognize(self, idx):
        return self.CAMERA_LIST[idx]['Recognition']
    
    def set_welcome_announcement(self):
        self.WELCOME_ANNOUNCEMENT.value = True
    
    def reset_welcome_announcement(self):
        self.WELCOME_ANNOUNCEMENT.value = False
    
    def get_welcome_announcement(self):
        return self.WELCOME_ANNOUNCEMENT.value
    
    def set_guard_announcement(self):
        self.GUARD_ANNOUNCEMENT.value = True
    
    def reset_guard_announcement(self):
        self.GUARD_ANNOUNCEMENT.value = False
    
    def get_guard_announcement(self):
        return self.GUARD_ANNOUNCEMENT.value
    
    def set_announcement(self):
        self.ANNOUNCEMENT.value = True
    
    def reset_announcement(self):
        self.ANNOUNCEMENT.value = False
    
    def get_announcement(self):
        return self.ANNOUNCEMENT.value

    def debug(self):

        tuples = [  ('EXPIRATION', self.EXPIRATION),
                    ('LICENSE_MISSING', self.LICENSE_MISSING),
                    ('INVALID_LICENSE', self.INVALID_LICENSE),
                    ('CLOSE_ALL', self.CLOSE_ALL),
                    ('UPDATE_CACHE', self.UPDATE_CACHE),
                    ('MONITOR', self.MONITOR),
                    ('WEBAPP', self.WEBAPP),
                  ('WELCOME_ANNOUNCEMENT', self.WELCOME_ANNOUNCEMENT),
                    ('GUARD_ANNOUNCEMENT', self.GUARD_ANNOUNCEMENT),
                  ('ANNOUNCEMENT',self.ANNOUNCEMENT)
                ]

        for name, variable in tuples:
            print(f'{name} : {variable.value}')

        print(self.CAMERA_LIST)

class SharedMemoryControlPanelProxy(BaseProxy):
    
    _exposed_ = ('set_expiration', 'is_expired', 'set_missing_license',
                 'is_missing_license', 'set_invalid_license', 'is_invalid_license',
                 'set_close_all', 'is_close_all', 'unset_close_all', 'set_update_cache',
                 'get_update_cache', 'reset_update_cache', 'should_stop', 'start_monitor',
                 'stop_monitor', 'start_webapp', 'stop_webapp', 'should_run_webapp',
                 'should_display_monitor', 'add_camera', 'get_camera_name', 'get_camera_address', 
                 'stop_all_recognition', 'stop_recognition', 'start_all_recognition', 
                 'start_recognition', 'stop_all_display', 'stop_display', 'start_all_display', 
                 'start_display', 'should_display', 'should_recognize',
                 'set_welcome_announcement', 'reset_welcome_announcement', 'get_welcome_announcement',
                 'set_guard_announcement', 'reset_guard_announcement', 'get_guard_announcement','set_announcement', 'reset_announcement', 'get_announcement','debug')
                
    def set_expiration(self):
        return self._callmethod('set_expiration')
    
    def is_expired(self):
        return self._callmethod('is_expired')
    
    def set_missing_license(self):
        return self._callmethod('set_missing_license')
    
    def is_missing_license(self):
        return self._callmethod('is_missing_license')
    
    def set_invalid_license(self):
        return self._callmethod('set_invalid_license')
    
    def is_invalid_license(self):
        return self._callmethod('is_invalid_license')
    
    def set_close_all(self):
        return self._callmethod('set_close_all')
    
    def is_close_all(self):
        return self._callmethod('is_close_all')
    
    def unset_close_all(self):
        return self._callmethod('unset_close_all')

    def set_update_cache(self):
        return self._callmethod('set_update_cache')

    def get_update_cache(self):
        return self._callmethod('get_update_cache')

    def reset_update_cache(self):
        return self._callmethod('reset_update_cache')

    def should_stop(self):
        return self._callmethod('should_stop')

    def start_monitor(self):
        return self._callmethod('start_monitor')
    
    def stop_monitor(self):
        return self._callmethod('stop_monitor')
    
    def should_display_monitor(self):
        return self._callmethod('should_display_monitor')
    
    def start_webapp(self):
        return self._callmethod('start_webapp')
    
    def stop_webapp(self):
        return self._callmethod('stop_webapp')
    
    def should_run_webapp(self):
        return self._callmethod('should_run_webapp')

    def add_camera(self, camera_name, camera_address):
        return self._callmethod('add_camera', (camera_name, camera_address))
    
    def get_camera_name(self, idx):
        return self._callmethod('get_camera_name', (idx,))
    
    def get_camera_address(self, idx):
        return self._callmethod('get_camera_address', (idx,))
    
    def stop_all_recognition(self):
        return self._callmethod('stop_all_recognition')
    
    def stop_recognition(self, idx=None):
        return self._callmethod('stop_recognition', (idx,))

    def start_all_recognition(self):
        return self._callmethod('start_all_recognition')
    
    def start_recognition(self, idx=None):
        return self._callmethod('start_recognition', (idx,))
    
    def stop_all_display(self):
        return self._callmethod('stop_all_display')
    
    def stop_display(self, idx=None):
        return self._callmethod('stop_display', (idx,))
    
    def start_all_display(self):
        return self._callmethod('start_all_display')
    
    def start_display(self, idx=None):
        return self._callmethod('start_display', (idx,))
    
    def should_display(self, idx):
        return self._callmethod('should_display', (idx,))
    
    def should_recognize(self, idx):
        return self._callmethod('should_recognize', (idx,))
    
    def set_welcome_announcement(self):
        return self._callmethod('set_welcome_announcement')
    
    def reset_welcome_announcement(self):
        return self._callmethod('reset_welcome_announcement')
    
    def get_welcome_announcement(self):
        return self._callmethod('get_welcome_announcement')
    
    def set_guard_announcement(self):
        return self._callmethod('set_guard_announcement')
    
    def reset_guard_announcement(self):
        return self._callmethod('reset_guard_announcement')
    
    def get_guard_announcement(self):
        return self._callmethod('get_guard_announcement')
    
    def set_announcement(self):
        return self._callmethod('set_announcement')
    
    def reset_announcement(self):
        return self._callmethod('reset_announcement')
    
    def get_announcement(self):
        return self._callmethod('get_announcement')

    def debug(self):
        return self._callmethod('debug')    