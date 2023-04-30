from multiprocessing import Lock, Value, Array
from multiprocessing.managers import BaseManager, BaseProxy
from ctypes import c_bool

from .shared_memory_vector import SharedMemoryVector, SharedMemoryVectorProxy
from .shared_memory_identity import SharedMemoryIdentity, SharedMemoryIdentityProxy
from .shared_memory_control_panel import SharedMemoryControlPanel, SharedMemoryControlPanelProxy
from .shared_memory_display import SharedMemoryDisplay, SharedMemoryDisplayProxy
from .shared_memory_db import SharedMemoryDB, SharedMemoryDBProxy
from .shared_memory_progress_bar import SharedMemoryProgressBar, SharedMemoryProgressBarProxy

class SharedMemory(BaseManager):
    pass

SharedMemory.register('Vectors', SharedMemoryVector, proxytype=SharedMemoryVectorProxy)
SharedMemory.register('Identities', SharedMemoryIdentity, proxytype=SharedMemoryIdentityProxy)
SharedMemory.register('ControlPanel', SharedMemoryControlPanel, proxytype=SharedMemoryControlPanelProxy)
SharedMemory.register('Display', SharedMemoryDisplay, proxytype=SharedMemoryDisplayProxy)
SharedMemory.register('Database', SharedMemoryDB, proxytype=SharedMemoryDBProxy)
SharedMemory.register('ProgressBar', SharedMemoryProgressBar, proxytype=SharedMemoryProgressBarProxy)