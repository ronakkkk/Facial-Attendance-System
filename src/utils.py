from datetime import datetime as datetimemodule, date as datemodule
from .global_vars import TIMESTAMP_FORMAT, TIMESTAMP_FORMAT_NOMS, DATE_FORMAT
import pickle as pkl
from typing import Any

def to_timestamp(value: str, noms=False) -> datetimemodule:
    
    if noms:
        value = datetimemodule.strptime(value, TIMESTAMP_FORMAT_NOMS)
    else:
        value = datetimemodule.strptime(value, TIMESTAMP_FORMAT)
    return value

def from_stream(value: bytes) -> Any:
    return pkl.loads(value)

def to_date(value: str) -> datemodule:
    value = datetimemodule.strptime(value, DATE_FORMAT).date()
    return value