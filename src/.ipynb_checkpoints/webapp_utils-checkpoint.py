from flask_login import UserMixin
from hashlib import md5
from .queries import check_username_for_login, retrieve_user_info, register_person,\
                     search_by_id, search_by_name, update_person_status, delete_user,\
                     fetch_alerts, get_cameras_from_db, get_roster_from_db,\
                     insert_operator_info, search_operator_by_name,\
                     search_operator_by_username, update_operator, delete_operator,\
                     update_operator_password, is_face_exists, search_all, get_shift_timing_from_db,\
                     update_employee_shift_details, add_roster_to_db, get_department_from_db, update_employee_department_details, add_department_to_db, add_holiday_to_db, add_location_to_db, add_category_to_db, get_category_from_db, update_department_details, select_from_locations, get_hod_list_from_db, select_from_person_details, select_from_person_department, select_from_face_identity

#create_report_in_range, get_videos_from_db, 
from .dbutils import create_connection, encrypt
from .report import write_report, write_alerts
from .load_config import CONFIG
from .global_vars import ALLOWED_EXTENSIONS
# from .offline_recognition import run_offline_recognition
import pickle
from shutil import copyfile
import glob, os, random, string, time
import numpy as np, pandas as pd
from multiprocessing import Process
from datetime import datetime as datetimemodule, date as datemodule
from collections import defaultdict

from .action_tesa_report_new import generate_action_tesa_report,generate_action_tesa_monthly_report
from .excel_report_format import write_report_all_logs, write_report_working_hours, write_report_daily, write_report_monthly

# Memory container for shared memories
class MemoryContainer:
    
    def __init__(self):
        
        self.memory = dict()

    def add_memory(self, memory_type, memory):
        self.memory[memory_type] = memory
    
    def __getitem__(self, memory_type):
        return self.memory[memory_type]

memory_container = MemoryContainer()

#User class for login
class User(UserMixin):
    
    def __init__(self):
        super().__init__()
        self.authenticated = False
        self.admin = False
        self.worker = dict()

    def set_authenticated(self, value):
        self.authenticated = value
    
    def set_admin(self, value):
        self.admin = value

    def remove_work(self, key):
        return self.worker.pop(key)

    def get_work(self, key):
        return self.worker[key]

    def add_work(self, key, value):
        self.worker[key] = value
    
    def show_work(self):
        print(self.worker)

    @property
    def is_authenticated(self):
        return self.authenticated

    @property
    def is_admin(self):
        return self.admin

# search user in db
def is_known_user(username):
    conn = create_connection(CONFIG['DB']['auth_db'])
    if conn is not None:
        return check_username_for_login(conn, username)
        conn.close()
    else:
        return False

def get_user_info(username):
    
    conn = create_connection(CONFIG['DB']['auth_db'])
    if conn is not None:
        return retrieve_user_info(conn, username)
        conn.close()
    else:
        return None, None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def add_operator(operator_id, operator_password, operator_name, operator_role):
    
    conn = create_connection(CONFIG['DB']['auth_db'])
    val = insert_operator_info(conn, operator_id, operator_password, operator_name, operator_role)
    conn.close()
    return val

#CHANGED
def register_user(user_id, user_name, image_file, category, deptid, shiftid, descriptor):
    
    vector = pickle.dumps(descriptor)
    try:
        basename = f'{user_id}-0'
        
        face_db_connection = create_connection(CONFIG['DB']['face_db'])
        person_db_connection = create_connection(CONFIG['DB']['person_db'])
        
        #TODO: ADDING DEPARTMENT DETAILS HERE
        # face_db_connection: Connection, person_db_connection: Connection, empid: str, name: str, empstatus: str,deptid :str, shiftid: str, basename: str, vector: bytes,location: str = None,depttimestamp: str = str(datetimemodule.now()),shifttimestamp: str = str(datetimemodule.now())
        cond = register_person(face_db_connection, person_db_connection, user_id, user_name, category, deptid, shiftid, basename, vector)
        
        if category == "HOD":
            warehouse_db_connection = create_connection(CONFIG['DB']['warehouse_db'])
            department_details = get_department_from_db(person_db_connection, return_dc= True, deptid = deptid)[0]
            prev_hod = department_details.depthod
            if prev_hod != "":
                update_person_status(person_db_connection, prev_hod, "Employee")

            update_department_details(person_db_connection, warehouse_db_connection, deptid, depthod = user_id)
            warehouse_db_connection.close()
            
        
        if cond:
            copyfile(image_file, os.path.join(CONFIG['DATA']['face_img_path'], f'{basename}.png'))

        fnames = glob.glob(os.path.join(CONFIG['TEMP']['temp_processing_path'], f'*-{user_id}*'))
        for f in fnames:
            os.unlink(f)

        face_db_connection.close()
        person_db_connection.close()
        return cond
    except Exception as e:
        print(e)
        fnames = glob.glob(os.path.join(CONFIG['TEMP']['temp_processing_path'], f'*-{user_id}*'))
        for f in fnames:
            os.unlink(f)
        try:
            delete_user(face_db_connection, person_db_connection, user_id)
        except Exception as e:
            print(e)
            return False
        return False

def if_face_enrolled(user_id,person_db_connection=None):

    if person_db_connection==None:
        person_db_connection = create_connection(CONFIG['DB']['person_db'])

    return is_face_exists(person_db_connection, user_id)

#CHANGED
def search_by(value, user_id=False, user_name=False, exact=False, return_dc = True):
    
    if (not (user_id or user_name)) or (user_id and user_name):
        raise ValueError('One of user_id or user_name in needed.')
    
    face_db_connection = create_connection(CONFIG['DB']['face_db'])
    person_db_connection = create_connection(CONFIG['DB']['person_db'])

    if user_id:
        person_details, fd = search_by_id(face_db_connection, person_db_connection, value, exact, return_dc = return_dc)
    
    if user_name:
        person_details, fd = search_by_name(face_db_connection, person_db_connection, value, exact, return_dc = return_dc)

    face_db_connection.close()
    person_db_connection.close()
    return person_details, fd
#CHANGED
# def update_threat_details(ids, status):
def update_status_details(ids, new_status_list, old_status_list, old_deptids, new_deptids):
    
    any_updates = False

    try:
        person_db_connection = create_connection(CONFIG['DB']['person_db'])
        warehouse_db_connection = create_connection(CONFIG['DB']['warehouse_db'])
        for i in range(len(ids)):
            #Handling hod condition
            print(1,old_status_list[i], new_status_list[i])
            print(2,old_deptids[i], new_deptids[i])
            if old_status_list[i] == "HOD":

#                 department_details = get_department_from_db(person_db_connection, return_dc= True, deptid = old_deptids[i])[0]
#                 prev_hod = department_details.depthod
                
#                 print(3,prev_hod)
#                 if prev_hod != "":
#                     update_person_status(person_db_connection, prev_hod, "Employee")
                    

                update_department_details(person_db_connection, warehouse_db_connection, old_deptids[i], depthod = "")
           
            if new_status_list[i] == "HOD":
                
                deptid = None
                
                if new_deptids[i] != None:
                    deptid = new_deptids[i]
                else:
                    deptid = old_deptids[i]
                    
                print(4,deptid)
                
                department_details = get_department_from_db(person_db_connection, return_dc= True, deptid = deptid)[0]
                prev_hod = department_details.depthod
                
                print(5,prev_hod)
                if prev_hod != "":
                    update_person_status(person_db_connection, prev_hod, "Employee")

                update_department_details(person_db_connection, warehouse_db_connection, deptid, depthod = ids[i])
                
                
            update_person_status(person_db_connection, ids[i], new_status_list[i])
            any_updates = True
            
        person_db_connection.close()
        warehouse_db_connection.close()
        return any_updates
    except Exception as e:
        print(e)
        return any_updates
#CHANGED
# def update_shift_details(ids, shifts):
def update_employee_shift(ids, shiftids):
    
    any_updates = False

    try:
        person_db_connection = create_connection(CONFIG['DB']['person_db'])
        warehouse_db_connection = create_connection(CONFIG['DB']['warehouse_db'])
        for _id, _shiftid in zip(ids, shiftids):
            res = update_employee_shift_details(person_db_connection, warehouse_db_connection, _id, _shiftid)
            any_updates = any_updates or res
        person_db_connection.close()
        warehouse_db_connection.close()
        return any_updates
    except Exception as e:
        print(e)
        return any_updates

    #def update_employee_department_details(person_db_connection: Connection,warehouse_db_connection:Connection, _empid: str, deptid: str) -> bool:
# def update_employee_department(ids, new_deptids, old_status_list, old_deptids, new_status_list):
def update_employee_department(ids, new_deptids, old_status_list, old_deptids, new_status_list):
    
    any_updates = False

    try:
        person_db_connection = create_connection(CONFIG['DB']['person_db'])
        warehouse_db_connection = create_connection(CONFIG['DB']['warehouse_db'])
        for i in range(len(ids)):
            # print(1, _id, _deptid)
            
            #Handling hod condition
            if new_status_list[i] == None:
                #status is not changed, handling hod case here              
                if old_status_list[i] == "HOD":
                    #old department hod change
                    # department_details = get_department_from_db(person_db_connection, return_dc= True, deptid = old_deptids[i])[0]
                    # prev_hod = department_details.depthod

                    # if prev_hod != "":
                    #     update_person_status(person_db_connection, prev_hod, "Employee")
                        
                    update_department_details(person_db_connection, warehouse_db_connection, old_deptids[i], depthod = "")
                    
                    #new department hod change
                    department_details = get_department_from_db(person_db_connection, return_dc= True, deptid = new_deptids[i])[0]
                    prev_hod = department_details.depthod

                    if prev_hod != "":
                        update_person_status(person_db_connection, prev_hod, "Employee")

                    update_department_details(person_db_connection, warehouse_db_connection, new_deptids[i], depthod = ids[i])
                
            
            res = update_employee_department_details(person_db_connection, warehouse_db_connection, ids[i], new_deptids[i])
            # print(2, res)
            any_updates = any_updates or res
        person_db_connection.close()
        warehouse_db_connection.close()
        return any_updates
    except Exception as e:
        print(e)
        return any_updates
    
def update_department(deptids, deptnames, locations, depthods):
    
    any_updates = False

    try:
        person_db_connection = create_connection(CONFIG['DB']['person_db'])
        warehouse_db_connection = create_connection(CONFIG['DB']['warehouse_db'])
        for i in range(len(deptids)):
            res = update_department_details(person_db_connection, warehouse_db_connection, deptids[i],deptname = deptnames[i], location = locations[i], depthod = depthods[i])
            any_updates = any_updates or res
        person_db_connection.close()
        warehouse_db_connection.close()
        return any_updates
    except Exception as e:
        print(e)
        return any_updates

def delete_entries(ids, entries):

    any_updates = False
    try:
        face_db_connection = create_connection(CONFIG['DB']['face_db'])
        person_db_connection = create_connection(CONFIG['DB']['person_db'])
        for _id, _val in zip(ids, entries):
            #TODO dont delete employee from db instead change status to non-employee
            # update_person_status(person_db_connections, _id, "Non-Employee")
            delete_user(face_db_connection, person_db_connection, _id)
            any_updates = True

            for p in _val[4]:
                print("delete entries", _val[4])
                fname = os.path.join(CONFIG['DATA']['face_img_path'], p)
                os.unlink(fname)

        person_db_connection.close()
        return any_updates
    except:
        return any_updates

def get_alerts(start_date, end_date, user_id=None):
    
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    alerts, unique_user_ids = fetch_alerts(person_db_connection, start_date, end_date, empid = user_id)
    person_db_connection.close()

    banner_suffix = f'From {start_date} - To - {end_date}'

    fname_rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k = 64))
    path = os.path.join(CONFIG['TEMP']['temp_processing_path'], f'alert_report_{fname_rand}.xlsx')
    write_alerts(alerts, path, sheet_name='alert_report', banner_suffix=banner_suffix)

    return path, alerts, unique_user_ids

def get_camera_list():

    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    camera_list = []
    for i in range(int(CONFIG['COMMON']['ip_camera_count'])):
        camera_list.append(CONFIG[f'IPCAMERA_{i+1}']['camera_name'])
    
    camera_list = np.union1d(camera_list, get_cameras_from_db(person_db_connection)).tolist() + ['ALL']
    person_db_connection.close()
    return camera_list

# def get_video_list():
    
#     person_db_connection = create_connection(CONFIG['DB']['person_db'])
#     video_list = get_videos_from_db(person_db_connection) + ['ALL']
#     person_db_connection.close()
#     return video_list

def get_time_message(start_time, end_time):
    msg = f'{time.strftime("%H:%M", time.gmtime(start_time))}-{time.strftime("%H:%M", time.gmtime(end_time))}'
    return msg

def get_roster():
    
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    roster = get_roster_from_db(person_db_connection, return_dc= True)
    person_db_connection.close()

    result = []
    for _res in roster:
        if _res.rid == 'D':
            result.append((_res.rid, f'{_res.name} (9HRS) ({_res.offday})'))
        else:
            msg = get_time_message(_res.starttime, _res.endtime)
            result.append((_res.rid, f'{_res.name} ({msg}) ({_res.offday})'))

    return result

def get_department(deptid = None, raw = False):
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    department_details = get_department_from_db(person_db_connection, return_dc= True, deptid = deptid)

    result = []
    for _res in department_details:
        hod_name = ""
        if _res.depthod!= "":
            hod_name = select_from_person_details(person_db_connection, empid = _res.depthod, return_dc = True)[0].name
        hod_details = _res.depthod+"-"+ hod_name
        if not raw:
            result.append((_res.deptid, f'{_res.deptname} ({_res.location}) ({hod_details})'))
        else:
            result.append((_res.deptid, _res.deptname, _res.location, _res.depthod, hod_name))
        
    person_db_connection.close()
    if deptid != None:
        return result[0]
    
    return result

def get_dept_id(deptname, location):
    
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    
    deptid = select_from_person_department(person_db_connection,deptname=deptname, location = location, return_dc = True)
    
    person_db_connection.close()
    
    if len(deptid)!=1:
        return -1
    else:
        return deptid[0].deptid
    

def get_status_list():
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    category_details = get_category_from_db(person_db_connection, cattype = "Person", return_dc = True)
    person_db_connection.close()
    
    result = []
    for _res in category_details:
        result.append(_res.name)
    
    return result

def get_holiday_types():
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    category_details = get_category_from_db(person_db_connection, cattype = "Holiday", return_dc = True)
    person_db_connection.close()
    
    result = []
    for _res in category_details:
        result.append(_res.name)
    
    return result

def get_weekdays():
    return ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

def get_shift_timing(shift_id):

    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    res = get_shift_timing_from_db(person_db_connection, shift_id, return_dc = True)[0]
    
    person_db_connection.close()

    if res.rid == 'D':
        shift_timing = (res.rid, f'{res.name} (9HRS)')
    else:
        msg = get_time_message(res.starttime, res.endtime)
        shift_timing = (res.rid, f'{res.name} ({msg})')

    return shift_timing

def get_locations():
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    location_details = select_from_locations(person_db_connection, return_dc = True)
    person_db_connection.close()
    
    result = []
    for _res in location_details:
        result.append((_res.location,_res.locationname))
    
    return result

def get_hod_list():
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    return  get_hod_list_from_db(person_db_connection)
    
def get_dept_people(deptid = None, raw = False):
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    res = select_from_person_details(person_db_connection, currdept = deptid, return_dc = True)
    if raw:
        return res
    
    details = []
    for i in res:
        details.append((i.currdept,f'{i.empid}-{i.name}'))
    
    return details
        
        

# def run_video_recognition(video_file_location, rotation):
    
#     rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k = 64))
#     basename = os.path.basename(video_file_location)
#     dirname = os.path.dirname(video_file_location)
#     fname = os.path.splitext(basename)[0]

#     output_file = os.path.join(dirname, f'recog_{fname}_{rand}.avi')

#     face_db_path = CONFIG['DB']['face_db']
#     person_db_path = CONFIG['DB']['person_db']
#     progress_memory = memory_container['progress_bar']

#     proc = Process( name='webapp_video', 
#                     target=run_offline_recognition, 
#                     args=(rand, video_file_location, output_file, rotation, progress_memory, face_db_path, person_db_path))

#     proc.start()
#     return rand, proc, output_file

#CHANGED
def search_operator_from_db(operator, by_name=False, by_username=False, return_dc = False):
    
    conn = create_connection(CONFIG['DB']['auth_db'])

    if by_name:
        return search_operator_by_name(conn, operator, return_dc = return_dc)
    elif by_username:
        return search_operator_by_username(conn, operator, return_dc = return_dc)
    
    conn.close()
    return None

def update_role(operator_role_tuple, new_role):

    operator_role_tuple = list(zip(new_role, operator_role_tuple))

    conn = create_connection(CONFIG['DB']['auth_db'])
    for v in operator_role_tuple:
        update_operator(conn, 'role', v)
    conn.close()

def delete_operators(operator_names):

    conn = create_connection(CONFIG['DB']['auth_db'])
    for opt in operator_names:
        delete_operator(conn, opt)
    conn.close()

def update_password(operator_id, operator_passwd):

    conn = create_connection(CONFIG['DB']['auth_db'])
    status = update_operator_password(conn, operator_id, operator_passwd)
    conn.close()
    return status


def get_all_registered_faces():
    
    face_db_connection = create_connection(CONFIG['DB']['face_db'])
    person_db_connection = create_connection(CONFIG['DB']['person_db'])

    person_details, fd = search_all(face_db_connection, person_db_connection, return_dc = True)

    face_db_connection.close()
    person_db_connection.close()

    return person_details, fd

#CHANGED
def add_roster(rid, name ,start_time, end_time, offday):
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    return add_roster_to_db(person_db_connection, rid, name, start_time, end_time, offday)



def add_department(deptname, depthod,location="Delhi", timestamp = str(datetimemodule.now())):
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    return add_department_to_db(person_db_connection, deptname, location, depthod, timestamp = timestamp)

def add_holiday(date, name, htype = "Company", deptid = None):
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    return add_holiday_to_db(person_db_connection, date, name, htype, deptid)

def add_location(location, locationname):
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    return add_location_to_db(person_db_connection, location, locationname)


def add_category(name, cattype = "Person"):
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    return add_category_to_db(person_db_connection, name, cattype)


#new_function
def get_category():
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    category_details = get_category_from_db(person_db_connection,cattype = 'Person', return_dc= True)
    person_db_connection.close()

    result = []
    for _res in category_details:
        result.append((_res.name, _res.cattype))

    return result

def get_ids():
    face_db_connection = create_connection(CONFIG['DB']['face_db'])
    res = select_from_face_identity(face_db_connection, return_dc= True)
    face_db_connection.close()
    
    result =[]
    for dc in res:
        result.append(dc.empid)
        
    return result

# def get_shift_names:


#reports

#def generate_action_tesa_report(user_list=None, user_name=None, start_date=None, end_date=None, location=None, report_type = ["cam","workhour","daily"]):
#def generate_action_tesa_monthly_report(user_list=None, user_name=None, month=None,year=None, location=None):

DATE_FORMAT = "%Y-%m-%d"
def download_cam_logs_report( user_list = None, user_name = None, shifts = None, departments = None, start_date= str(datetimemodule.now().date()), end_date = str(datetimemodule.now().date()), total_rows = -1):
    
    query=[]
    
    final_user_list = []
    final_user_names = []
    if not user_list and not user_name:
        final_user_list = get_ids()
        final_user_names = [None for i in range(len(final_user_list))]
    else:
        if user_list:
            final_user_list = [i for i in user_list]
            final_user_names = [None for i in range(len(user_list))]
            entry_nos= ",".join(user_list)
            query.append(f"EntryNumbers: {entry_nos}")
        
        if user_name:
            final_user_list.extend([None for i in range(len(user_name))])
            final_user_names.extend(user_name)
            query_names= ",".join(user_name)
            query.append(f"Names: {query_names}")  
    # print("finaluserlistandnames", final_user_list, final_user_names)
    
    if datetimemodule.strptime(start_date,DATE_FORMAT)>datetimemodule.strptime(end_date, DATE_FORMAT):
        return -1,-1
    
    res = generate_action_tesa_report(user_list=final_user_list, user_name=final_user_names, start_date=start_date, end_date=end_date, location=None, report_type = ["cam"])[0]
    
    if len(res)<1:
        return -2,-2
    
    # print("shifts,departments", shifts,departments)
    if shifts:   
        res = res[res['SHIFT'].isin(shifts)]# & res['DEPARTMENT'].isin(departments)]
        q_shifts= ",".join(shifts)
        query.append(f"Shifts: {q_shifts}")
    if departments:
        res = res[res['DEPARTMENT'].isin(departments)]
        q_depts= ",".join(departments)
        query.append(f"Departments: {q_depts}") 

    fname_rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k = 64))
    path = CONFIG['TEMP']['temp_processing_path']
    filename = f'camlogs_report_{fname_rand}.xlsx'
    banner_suffix=''
    if start_date:
        banner_suffix += f'From {start_date}'
    if end_date:
        if banner_suffix == '':
            banner_suffix += f'To {end_date}'
        else:
            banner_suffix += f' - To {end_date}'
     
    query = "||".join(query)
    # print('cam info:', len(res), "\nquery:",query,"\nbannersuffix:", banner_suffix)
            
    write_report_all_logs(res, path, filename=filename, query=query, banner_suffix = banner_suffix)
    
    file_path= os.path.join(path, filename)
    # print("file path", file_path)
    
    return file_path, res

def download_workhour_logs_report( user_list = None, user_name = None, shifts = None, departments = None, start_date= str(datetimemodule.now().date()), end_date = str(datetimemodule.now().date()), total_rows = -1):
    
    query=[]
    
    final_user_list = []
    final_user_names = []
    if not user_list and not user_name:
        final_user_list = get_ids()
        final_user_names = [None for i in range(len(final_user_list))]
    else:
        if user_list:
            final_user_list = [i for i in user_list]
            final_user_names = [None for i in range(len(user_list))]
            entry_nos= ",".join(user_list)
            query.append(f"EntryNumbers: {entry_nos}")
        
        if user_name:
            final_user_list.extend([None for i in range(len(user_name))])
            final_user_names.extend(user_name)
            query_names= ",".join(user_name)
            query.append(f"Names: {query_names}")  
    # print("finaluserlistandnames", final_user_list, final_user_names)
    
    if datetimemodule.strptime(start_date,DATE_FORMAT)>datetimemodule.strptime(end_date, DATE_FORMAT):
        return -1,-1
    
    res = generate_action_tesa_report(user_list=final_user_list, user_name=final_user_names, start_date=start_date, end_date=end_date, location=None, report_type = ["workhour"])[1]
    
    if len(res)<1:
        return -2,-2
    
    # print("shifts,departments", shifts,departments)
    if shifts:   
        res = res[res['SHIFT'].isin(shifts)]# & res['DEPARTMENT'].isin(departments)]
        q_shifts= ",".join(shifts)
        query.append(f"Shifts: {q_shifts}")
    if departments:
        res = res[res['DEPARTMENT'].isin(departments)]
        q_depts= ",".join(departments)
        query.append(f"Departments: {q_depts}") 

    fname_rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k = 64))
    path = CONFIG['TEMP']['temp_processing_path']
    filename = f'workhourlogs_report_{fname_rand}.xlsx'
    banner_suffix=''
    if start_date:
        banner_suffix += f'From {start_date}'
    if end_date:
        if banner_suffix == '':
            banner_suffix += f'To {end_date}'
        else:
            banner_suffix += f' - To {end_date}'
     
    query = "||".join(query)
    # print('work hour info:', len(res), "\nquery:",query,"\nbannersuffix:", banner_suffix)
            
    write_report_working_hours(res, path, filename=filename, query=query, banner_suffix = banner_suffix)
    
    file_path= os.path.join(path, filename)
    # print("file path", file_path)
    
    return file_path, res


def download_daily_report( user_list = None, user_name = None, shifts = None, departments = None, start_date= str(datetimemodule.now().date()), end_date = str(datetimemodule.now().date()), total_rows = -1, status_list= None):
    
    query=[]
    
    final_user_list = []
    final_user_names = []
    if not user_list and not user_name:
        final_user_list = get_ids()
        final_user_names = [None for i in range(len(final_user_list))]
    else:
        if user_list:
            final_user_list = [i for i in user_list]
            final_user_names = [None for i in range(len(user_list))]
            entry_nos= ",".join(user_list)
            query.append(f"EntryNumbers: {entry_nos}")
        
        if user_name:
            final_user_list.extend([None for i in range(len(user_name))])
            final_user_names.extend(user_name)
            query_names= ",".join(user_name)
            query.append(f"Names: {query_names}")  
    # print("finaluserlistandnames", final_user_list, final_user_names)
    
    if datetimemodule.strptime(start_date,DATE_FORMAT)>datetimemodule.strptime(end_date, DATE_FORMAT):
        return -1,-1
    
    res = generate_action_tesa_report(user_list=final_user_list, user_name=final_user_names, start_date=start_date, end_date=end_date, location=None, report_type = ["daily"])[2]
    
    if len(res)<1:
        return -2,-2
    
    # print("shifts,departments, status", shifts,departments, status_list)
    if shifts:   
        res = res[res['SHIFT'].isin(shifts)]# & res['DEPARTMENT'].isin(departments)]
        q_shifts= ",".join(shifts)
        query.append(f"Shifts: {q_shifts}")
    if departments:
        res = res[res['DEPARTMENT'].isin(departments)]
        q_depts= ",".join(departments)
        query.append(f"Departments: {q_depts}")
    if status_list:
        res = res[res['STATUS'].isin(status_list)]
        q_status= ",".join(status_list)
        query.append(f"Status: {q_status}")

    fname_rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k = 64))
    path = CONFIG['TEMP']['temp_processing_path']
    filename = f'daily_report_{fname_rand}.xlsx'
    banner_suffix=''
    if start_date:
        banner_suffix += f'From {start_date}'
    if end_date:
        if banner_suffix == '':
            banner_suffix += f'To {end_date}'
        else:
            banner_suffix += f' - To {end_date}'
     
    query = "||".join(query)
    # print('daily report info:', len(res), "\nquery:",query,"\nbannersuffix:", banner_suffix)
            
    write_report_daily(res, path, filename=filename, query=query, banner_suffix = banner_suffix)
    
    file_path= os.path.join(path, filename)
    # print("file path", file_path)
    
    return file_path, res

def download_monthly_report( user_list = None, user_name = None, shifts = None, departments = None, month= datetimemodule.now().month, year = datetimemodule.now().year, total_rows = -1):
    
    query=[]
    
    final_user_list = []
    final_user_names = []
    if not user_list and not user_name:
        final_user_list = get_ids()
        final_user_names = [None for i in range(len(final_user_list))]
    else:
        if user_list:
            final_user_list = [i for i in user_list]
            final_user_names = [None for i in range(len(user_list))]
            entry_nos= ",".join(user_list)
            query.append(f"EntryNumbers: {entry_nos}")
        
        if user_name:
            final_user_list.extend([None for i in range(len(user_name))])
            final_user_names.extend(user_name)
            query_names= ",".join(user_name)
            query.append(f"Names: {query_names}")  
    # print("finaluserlistandnames", final_user_list, final_user_names)
    
    # generate_action_tesa_monthly_report(user_list=None, user_name=None, month=None,year=None, location=None)
    # res = generate_action_tesa_report(user_list=final_user_list, user_name=final_user_names, start_date=start_date, end_date=end_date, location=None, report_type = ["daily"])[2]
    res= generate_action_tesa_monthly_report(user_list=final_user_list, user_name=final_user_names, month=int(month), year=int(year))
    
    if len(res)<1:
        return -1,-1
    
    print("shifts,departments", shifts,departments)
    if shifts:   
        res = res[res['SHIFT'].isin(shifts)]# & res['DEPARTMENT'].isin(departments)]
        q_shifts= ",".join(shifts)
        query.append(f"Shifts: {q_shifts}")
    if departments:
        res = res[res['DEPARTMENT'].isin(departments)]
        q_depts= ",".join(departments)
        query.append(f"Departments: {q_depts}")

    fname_rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k = 64))
    path = CONFIG['TEMP']['temp_processing_path']
    filename = f'monthly_report_{fname_rand}.xlsx'
    banner_suffix=''
    if month:
        month = str(datetimemodule.strptime(str(month), "%m").strftime("%B"))
        banner_suffix += f'Month : {month}'
    if year:
        banner_suffix += f', Year : {year}'
     
    query = "||".join(query)
    print('monthly report info:', len(res), "\nquery:",query,"\nbannersuffix:", banner_suffix)
            
    write_report_monthly(res, path, filename=filename, query=query, banner_suffix = banner_suffix)
    
    file_path= os.path.join(path, filename)
    # print("file path", file_path)
    
    return file_path, res
    
    
    
    
    