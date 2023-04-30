# Make sure global_vars never import CONFIG
from enum import Enum

DEBUG_MODE = True
DEVELOPER_MODE = False

if DEBUG_MODE:
    DEVELOPER_MODE = True

INVALID_LICENSE = False


##### Auth tables
class Auth_Login(Enum):
    username = 0
    timestamp = 1
    addr = 2
    browser = 3
    remark = 4

class Auth_Login_Fields:
    tablename = 'login'
    username = 'username'
    timestamp = 'timestamp'
    addr = 'addr'
    browser = 'browser'
    remark = 'remark'

class Auth_User(Enum):
    username = 0
    password = 1
    role = 2
    name = 3

class Auth_User_Fields:
    tablename = 'user'
    username = 'username'
    password = 'password'
    role = 'role'
    name = 'name'


#### Face tables
class Face_Identity(Enum):
    empid = 0
    entry = 1

class Face_Identity_Fields:
    tablename = 'identity'
    empid = 'empid'
    entry = 'entry'

class Face_Vector(Enum):
    f_id = 0
    label = 1
    empid = 2
    vector = 3

class Face_Vector_Fields:
    tablename = 'vectors'
    f_id = 'f_id'
    label = 'label'
    empid = 'empid'
    vector = 'vector'

#### Person tables
class Person_Alerts(Enum):
    alertid=0
    empid=1
    datetime=2
    date=3
    location=4
    
class Person_Alerts_Fields:
    tablename='alerts'
    alertid='fid'
    empid='empid'
    datetime='datetime'
    date='date'
    location='location'

class Person_Attendance_Log(Enum):
    empid = 0
    intime = 1
    outtime = 2
    date = 3
    firstlocation = 4
    lastseenlocation = 5

class Person_Attendance_Log_Fields:
    tablename = 'attendance_log'
    empid = 'empid'
    intime = 'intime'
    outtime = 'outtime'
    date = 'date'
    firstlocation = 'firstlocation'
    lastseenlocation = 'lastseenlocation'
    
class Person_Category(Enum):
    name = 0
    cattype = 1

class Person_Category_Fields:
    tablename = 'category'
    name = 'name'
    cattype = 'cattype'

class Person_Department(Enum):
    deptid = 0
    location = 1
    deptname = 2
    depthod = 3
    timestamp = 4

class Person_Department_Fields:
    tablename = 'department'
    deptid = 'deptid'
    location = 'location'
    deptname = 'deptname'
    depthod = 'depthod'
    timestamp = 'timestamp'

class Person_Holiday(Enum):
    date = 0
    name = 1
    htype = 2
    # location = 3
    deptid = 3

class Person_Holiday_Fields:
    tablename = 'holiday'
    date = 'date'
    name = 'name'
    htype = 'htype'
    # location = 'location'
    deptid = 'deptid'

class Person_Location(Enum):
    location = 0
    locationname = 1

class Person_Location_Fields:
    tablename = 'locations'
    location = 'location'
    locationname = 'locationname'

class Person_Person_Details(Enum):
    empid = 0
    name = 1
    empstatus = 2
    currdept = 3
    currshift = 4
    location = 5
    depttimestamp = 6
    shifttimestamp=7

class Person_Person_Details_Fields:
    tablename = 'person_details'
    empid = 'empid'
    name = 'name'
    empstatus = 'empstatus'
    currdept = 'currdept'
    currshift = 'currshift'
    location = 'location'
    depttimestamp = 'depttimestamp'
    shifttimestamp='shifttimestamp'

class Person_Roster(Enum):
    rid = 0
    name = 1
    starttime = 2
    endtime = 3
    offday = 4

class Person_Roster_Fields:
    tablename = 'roster'
    rid = 'rid'
    name = 'name'
    starttime = 'starttime'
    endtime = 'endtime'
    offday = 'offday'

#### Warehouse tables
class Warehouse_Olddeptchange(Enum):
    datetime = 0
    deptid = 1
    deptname = 2
    depthod = 3
    fromdate = 4
    todate = 5
    location = 6

class Warehouse_Olddeptchange_Fields:
    tablename = 'olddeptchange'
    datetime = 'datetime'
    deptid = 'deptid'
    deptname = 'deptname'
    depthod = 'depthod'
    fromdate = 'fromdate'
    todate = 'todate'
    location = 'location'

class Warehouse_Oldempdept(Enum):
    empid = 0
    datetime = 1
    deptid = 2
    deptname = 3
    fromdate = 4
    todate = 5
    depthod=6
    location=7

class Warehouse_Oldempdept_Fields:
    tablename = 'oldempdept'
    empid = 'empid'
    datetime = 'datetime'
    deptid = 'deptid'
    deptname = 'deptname'
    fromdate = 'fromdate'
    todate = 'todate'
    depthod='depthod'
    location='location'

class Warehouse_Oldempshifts(Enum):
    empid = 0
    datetime = 1
    shift = 2
    starttime = 3
    endtime = 4
    offday = 5
    fromdate = 6
    todate = 7
    shiftname=8

class Warehouse_Oldempshifts_Fields:
    tablename = 'oldempshifts'
    empid = 'empid'
    datetime = 'datetime'
    shift = 'shift'
    starttime = 'starttime'
    endtime = 'endtime'
    offday = 'offday'
    fromdate = 'fromdate'
    todate = 'todate'
    shiftname='shiftname'

# Static variables
POLICY_KEY = b'n^b13itP0l1cyK3y'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_ANGLES = {0, 90, 180, 270}
TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
TIMESTAMP_FORMAT_NOMS = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'