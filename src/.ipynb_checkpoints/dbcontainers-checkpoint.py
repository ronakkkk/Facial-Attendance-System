from .global_vars import Auth_Login, Auth_Login_Fields,\
                         Auth_User, Auth_User_Fields,\
                         Face_Identity, Face_Identity_Fields,\
                         Face_Vector, Face_Vector_Fields,Person_Alerts,Person_Alerts_Fields,Person_Attendance_Log,Person_Attendance_Log_Fields,\
                         Person_Department, Person_Department_Fields,\
                         Person_Holiday, Person_Holiday_Fields,\
                         Person_Location, Person_Location_Fields,\
                         Person_Person_Details, Person_Person_Details_Fields,\
                         Person_Roster, Person_Roster_Fields,\
                         Warehouse_Olddeptchange, Warehouse_Olddeptchange_Fields,\
                         Warehouse_Oldempdept, Warehouse_Oldempdept_Fields,\
                         Warehouse_Oldempshifts, Warehouse_Oldempshifts_Fields, Person_Category,Person_Category_Fields

from .dbabc import Auth_Login_Data, Auth_User_Data, Face_Identity_Data, Face_Vector_Data,\
                   Person_Alerts_Data,Person_Attendance_Log_Data, Person_Department_Data, Person_Holiday_Data,\
                   Person_Location_Data, Person_Person_Details_Data, Person_Roster_Data,\
                   Warehouse_Olddeptchange_Data, Warehouse_Oldempdept_Data, Warehouse_Oldempshifts_Data, Person_Category_Data, base_dataclass 

from typing import Type, Any, Tuple
from enum import Enum

class DB_Container:

    def __init__(self, enum_class: Type[Enum], field_class: Any, data_class: Type[base_dataclass]):

        self.enum = enum_class
        self.field = field_class
        self.data = data_class
    
    def make(self, value: Tuple[Any, ...]) -> Type[base_dataclass]:
        return self.data.make(value, self.enum, self.field)

Auth_Login_Container = DB_Container(enum_class=Auth_Login, field_class=Auth_Login_Fields, data_class=Auth_Login_Data)
Auth_User_Container = DB_Container(enum_class=Auth_User, field_class=Auth_User_Fields, data_class=Auth_User_Data)
Face_Identity_Container = DB_Container(enum_class=Face_Identity, field_class=Face_Identity_Fields, data_class=Face_Identity_Data)
Face_Vector_Container = DB_Container(enum_class=Face_Vector, field_class=Face_Vector_Fields, data_class=Face_Vector_Data)
Person_Alerts_container = DB_Container(enum_class=Person_Alerts, field_class=Person_Alerts_Fields, data_class=Person_Alerts_Data)
Person_Attendance_Log_container = DB_Container(enum_class=Person_Attendance_Log, field_class=Person_Attendance_Log_Fields, data_class=Person_Attendance_Log_Data)
Person_Category_Container = DB_Container(enum_class = Person_Category, field_class = Person_Category_Fields, data_class = Person_Category_Data)
Person_Department_Container = DB_Container(enum_class=Person_Department, field_class=Person_Department_Fields, data_class=Person_Department_Data)
Person_Holiday_Container = DB_Container(enum_class=Person_Holiday, field_class=Person_Holiday_Fields, data_class=Person_Holiday_Data)
Person_Location_Container = DB_Container(enum_class=Person_Location, field_class=Person_Location_Fields, data_class=Person_Location_Data)
Person_Person_Details_Container = DB_Container(enum_class=Person_Person_Details, field_class=Person_Person_Details_Fields, data_class=Person_Person_Details_Data)
Person_Roster_Container = DB_Container(enum_class=Person_Roster, field_class=Person_Roster_Fields, data_class=Person_Roster_Data)
Warehouse_Olddeptchange_Container = DB_Container(enum_class=Warehouse_Olddeptchange, field_class=Warehouse_Olddeptchange_Fields, data_class=Warehouse_Olddeptchange_Data)
Warehouse_Oldempdept_Container = DB_Container(enum_class=Warehouse_Oldempdept, field_class=Warehouse_Oldempdept_Fields, data_class=Warehouse_Oldempdept_Data)
Warehouse_Oldempshifts_Container = DB_Container(enum_class=Warehouse_Oldempshifts, field_class=Warehouse_Oldempshifts_Fields, data_class=Warehouse_Oldempshifts_Data)

