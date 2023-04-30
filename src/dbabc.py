from re import L
from dataclasses import dataclass, field
from typing import Type, Any, Tuple, Union
from enum import Enum
from datetime import datetime as datetimemodule, date as datemodule
from .utils import to_timestamp, from_stream, to_date
import numpy as np


class base_dataclass:

    @classmethod
    def coerce(cls, name: str, value: str):
        print(cls,name,value)
        raise NotImplementedError

    @classmethod
    def make(cls, data: Tuple[Any, ...], retrieval_order: Type[Enum], retrieval_name: Any) -> Any:

        data_dict = {}
        for a in retrieval_order:
            field_name = getattr(retrieval_name, a.name)
            data_dict[field_name] = cls.coerce(field_name, data[a.value])
        
        return cls(**data_dict)

@dataclass(frozen=True, unsafe_hash=True)
class Auth_Login_Data(base_dataclass):
    username: str 
    timestamp: datetimemodule
    addr: str
    browser: str
    remark: str

    @classmethod
    def coerce(cls, name: str, value: str) -> Union[datetimemodule, str]:
        if name in ['timestamp']:
            value = to_timestamp(value,noms = False)
        else:
            value = str(value)

        return value

@dataclass(frozen=True, unsafe_hash=True)
class Auth_User_Data(base_dataclass):
    username: str
    password: str
    role: str
    name: str

    @classmethod
    def coerce(cls, name: str, value: str) -> str:
        return str(value)

@dataclass(frozen=True, unsafe_hash=True)
class Face_Identity_Data(base_dataclass):
    empid: str
    entry: str

    @classmethod
    def coerce(cls, name: str, value: str) -> str:
        return str(value)

@dataclass(frozen=True, unsafe_hash=True)
class Face_Vector_Data(base_dataclass):
    f_id: int
    label: str
    empid: str
    vector: np.ndarray

    @classmethod
    def coerce(cls, name: str, value: str) -> Any:
        if name in ['vector']:
            value = from_stream(value)
        else:
            value = str(value)
        
        return value
    
@dataclass(frozen=True, unsafe_hash=True)
class Person_Alerts_Data(base_dataclass):
    alertid:str
    empid: str
    datetime: datetimemodule
    date: datemodule
    location: str

    @classmethod
    def coerce(cls, name: str, value: str) -> Union[datetimemodule, datemodule, str]:
        if name in ['datetime']:
            value = to_timestamp(value, noms=False)
        elif name in ['date']:
            value = to_date(value)
        else:
            value = str(value)
        
        return value

@dataclass(frozen=True, unsafe_hash=True)
class Person_Attendance_Log_Data(base_dataclass):
    empid: str
    intime: datetimemodule
    outtime: datetimemodule
    date: datemodule
    firstlocation: str
    lastseenlocation: str

    @classmethod
    def coerce(cls, name: str, value: str) -> Union[datetimemodule, datemodule, str]:
        if name in ['intime', 'outtime']:
            value = to_timestamp(value, noms=False)
        elif name in ['date']:
            value = to_date(value)
        else:
            value = str(value)
        
        return value
    
@dataclass(frozen=True, unsafe_hash=True)
class Person_Category_Data(base_dataclass):

    name : str
    cattype : str

    @classmethod
    def coerce(cls, name: str, value: str) -> str:
        return str(value)

@dataclass(frozen=True, unsafe_hash=True)
class Person_Department_Data(base_dataclass):
    deptid: str
    location: str
    deptname: str
    depthod: str
    timestamp: datetimemodule
    pushdata: str

    @classmethod
    def coerce(cls, name: str, value: str) -> Union[datetimemodule, str]:
        if name in ['timestamp']:
            value = to_timestamp(value, noms=False)
        else:
            value = str(value)
        
        return value

@dataclass(frozen=True, unsafe_hash=True)
class Person_Holiday_Data(base_dataclass):

    date: datemodule
    name: str
    htype: str
    # location: str
    deptid: str

    @classmethod
    def coerce(cls, name: str, value: str) -> Union[datemodule, str]:

        if name in ['date']:
            value = to_date(value)
        else:
            value = str(value)
        
        return value
    

@dataclass(frozen=True, unsafe_hash=True)
class Person_Location_Data(base_dataclass):

    location: str
    locationname: str

    @classmethod
    def coerce(cls, name: str, value: str) -> str:
        return str(value)

@dataclass(frozen=True, unsafe_hash=True)
class Person_Person_Details_Data(base_dataclass):

    empid: str
    name: str
    empstatus: str
    currdept: str
    currshift: str
    location: str
    shifttimestamp: datetimemodule
    depttimestamp: datetimemodule
    
    @classmethod
    def coerce(cls, name: str, value: str) -> Union[datetimemodule, str]:

        if name in ['depttimestamp','shifttimestamp']:
            value = to_timestamp(value, noms=False)
        else:
            value = str(value)
        
        return value
    
@dataclass(frozen=True, unsafe_hash=True)
class Person_Roster_Data(base_dataclass):

    rid: str
    name: str
    starttime: int
    endtime: int
    offday: str

    @classmethod
    def coerce(cls, name: str, value: str) -> Union[int, str]:

        if name in ['starttime', 'endtime']:
            value = int(value)
        else:
            value = str(value)
        
        return value

@dataclass(frozen=True, unsafe_hash=True)
class Warehouse_Olddeptchange_Data(base_dataclass):

    datetime: datetimemodule
    deptid: str
    deptname: str
    depthod: str
    fromdate: datemodule
    todate: datemodule
    location : str

    @classmethod
    def coerce(cls, name: str, value: str) -> Union[datetimemodule, datemodule, str]:

        if name in ['datetimemodule']:
            value = to_timestamp(value)
        elif name in ['fromdate', 'todate']:
            value = to_date(value)
        else:
            value = str(value)
        
        return value

@dataclass(frozen=True, unsafe_hash=True)
class Warehouse_Oldempdept_Data(base_dataclass):

    empid: str
    datetime: datetimemodule
    deptid: str
    deptname: str
    fromdate: datemodule
    todate: datemodule
    depthod : str
    location : str

    @classmethod
    def coerce(cls, name: str, value: str) -> Union[datetimemodule, datemodule, str]:
        
        if name in ['datetime']:
            value = to_timestamp(value)
        elif name in ['fromdate', 'todate']:
            value = to_date(value)
        else:
            value = str(value)
        
        return value

@dataclass(frozen=True, unsafe_hash=True)
class Warehouse_Oldempshifts_Data(base_dataclass):

    empid: str
    datetime: datetimemodule
    shift: str
    starttime: int
    endtime: int
    offday: str
    fromdate: datemodule
    todate: datemodule
    shiftname: str

    @classmethod
    def coerce(cls, name: str, value: str) -> Union[datetimemodule, datemodule, int, str]:

        if name in ['datetime']:
            value = to_timestamp(value)
        elif name in ['fromdate', 'todate']:
            value = to_date(value)
        elif name in ['starttime', 'endtime']:
            value = int(value)
        else:
            value = str(value)
        
        return value