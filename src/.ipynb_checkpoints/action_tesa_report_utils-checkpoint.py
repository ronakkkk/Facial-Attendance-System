from datetime import datetime,timedelta,date
from .load_config import CONFIG
from .dbutils import run_fetch_query, run_query_noreturn,create_connection

from .dbcontainers import Auth_Login_Container, Auth_User_Container, Face_Identity_Container,\
                          Face_Vector_Container,Person_Alerts_container, Person_Attendance_Log_container, Person_Department_Container,\
                          Person_Holiday_Container, Person_Location_Container, Person_Person_Details_Container,\
                          Person_Roster_Container, Warehouse_Olddeptchange_Container, Warehouse_Oldempdept_Container,\
                          Warehouse_Oldempshifts_Container, DB_Container, base_dataclass

from .queries import select_from_warehouse_oldempshifts, select_from_person_roster, get_department_from_db, run_select_query, select_from_holiday#, select_from_warehouse_olddeptchange, select_from_warehouse_oldempdept

# import random, string, os
# from .report import write_report
from calendar import monthrange
# import xlsxwriter

IN_TIME_FORMAT="%Y-%m-%d %H:%M:%S.%f"
SHIFT_TIMESTAMP_FORMAT = IN_TIME_FORMAT
DEPARTMENT_TIMESTAMP_FORMAT = IN_TIME_FORMAT

DEBUG = False

def time_to_seconds(time):
    return (time.hour * 60 + time.minute) * 60 + time.second
                        
def get_time_difference(in_time,out_time,time_format=IN_TIME_FORMAT):
    in_time=datetime.strptime(in_time,time_format)
#     in_time=time_to_seconds(in_time.time())
                        
    out_time=datetime.strptime(out_time,time_format)
#     out_time=time_to_seconds(out_time.time())
    
    td=out_time-in_time
    h,m=td.seconds//3600, (td.seconds//60)%60
    s=td.seconds-h*3600-m*60
    return str(timedelta(hours=h,minutes=m,seconds=s))

def get_dates_in_between(start_date,end_date):
    start_date=datetime.strptime(start_date,"%Y-%m-%d")
    end_date=datetime.strptime(end_date,"%Y-%m-%d")
    
    dates_in_between=[]
#     print("gap:",(end_date-start_date).days)
    for i in range((end_date-start_date).days+1):
        date=start_date+timedelta(days=i)
#         print("day:",i,date)
        dates_in_between.append(str(date.date()))
        
    return dates_in_between

def get_next_date(date,date_format="%Y-%m-%d"):
    date=datetime.strptime(date,date_format)+timedelta(days=1)
    return str(date.date())

def get_prev_date(date,date_format="%Y-%m-%d"):
    date=datetime.strptime(date,date_format)+timedelta(days=-1)
    return str(date.date())


def string_to_time(time_string,string_format="%H:%M:%S"):
    time=datetime.strptime(time_string,string_format)
    return time.time()

def string_to_seconds(time_string,string_format="%H:%M:%S"):
    return time_to_seconds(string_to_time(time_string,string_format=string_format))


def days_of_month(month=datetime.now().month,year=datetime.now().year):
    nb_days = monthrange(year, month)[1]

    return [str(date(year, month, day)) for day in range(1, nb_days+1)]

def get_date_and_time(timestamp_string,timestamp_format=IN_TIME_FORMAT):
    dt=datetime.strptime(timestamp_string,timestamp_format)
    date=str(dt.date())
    time=str(dt.strftime("%H:%M:%S"))
    return date,time


def get_shift(empid,emp_shift_id, emp_curr_shift_timestamp, timestamp,timestamp_format="%Y-%m-%d"):
    
    # print(datetime.strptime(timestamp, timestamp_format), datetime.strptime(emp_curr_shift_timestamp, SHIFT_TIMESTAMP_FORMAT))
    if datetime.strptime(timestamp, timestamp_format) >= datetime.strptime(emp_curr_shift_timestamp, SHIFT_TIMESTAMP_FORMAT):
        # print(1)
        person_db_connection = create_connection(CONFIG['DB']['person_db'])
        res = select_from_person_roster(person_db_connection, rid = emp_shift_id, return_dc = True)
        person_db_connection.close()
        
        if len(res) > 0:
            return 0,res[0]
        else:
            return -2 
    
    
    warehouse_db_connection=create_connection(CONFIG['DB']['warehouse_db'])
    
    query = f'SELECT * FROM {Warehouse_Oldempshifts_Container.field.tablename} WHERE {Warehouse_Oldempshifts_Container.field.empid} = ? AND {Warehouse_Oldempshifts_Container.field.fromdate} <= ? AND {Warehouse_Oldempshifts_Container.field.todate} >= ? ORDER BY {Warehouse_Oldempshifts_Container.field.datetime} ASC'
    
    values=(empid,timestamp, timestamp)
    # print(query, values)
    
    rows= run_select_query(warehouse_db_connection, query, values, Warehouse_Oldempshifts_Container, return_dc=True)
    # print(1, len(rows))
    
    warehouse_db_connection.close()
    
    if len(rows)==1:
        return 1,rows[0]
    elif len(rows)==0:
        if datetime.strptime(timestamp,timestamp_format) < datetime.strptime(CONFIG['ARCHIVE']['start_date'],"%Y-%m-%d"):
            # raise ValueError("There is no shift for selected date")
            if DEBUG:
                print("Shift: Time stamp is before archives startime")
            return -1
        else:
            if DEBUG:
                print('employee not registered at that time')
            return -3
    else:
        # print("Shift rows:",rows)
        if DEBUG:
            print("shift is found in more than one archive duration")
        return 1,rows[-1]
        # raise Exception("shift is found in more than one archive duration")
        
    # print('ending here')

def get_department(empid,emp_dep_id,emp_curr_dept_timestamp,timestamp,timestamp_format="%Y-%m-%d"):
    
    # print(datetime.strptime(timestamp, timestamp_format), datetime.strptime(emp_curr_dept_timestamp, DEPARTMENT_TIMESTAMP_FORMAT))
    
    final_dept_id = None
    if datetime.strptime(timestamp, timestamp_format) >= datetime.strptime(emp_curr_dept_timestamp, DEPARTMENT_TIMESTAMP_FORMAT):
        
        person_db_connection = create_connection(CONFIG['DB']['person_db'])
        res = get_department_from_db(person_db_connection, deptid = emp_dep_id, return_dc = True)
        # person_db_connection.close()
        
        if len(res) > 0:
            # return res[0]
            # print("inside")
            final_dept_id= res[0].deptid
        else:
            if DEBUG:
                print("department is removed")
            return -2 
        
    warehouse_db_connection=create_connection(CONFIG['DB']['warehouse_db'])
    
    if final_dept_id == None:
        # # rows=run_fetch_query(warehouse_db_connection,query,clause)
        # extra_clause = f'AND {Warehouse_Oldempdept_Container.field.todate} >= {timestamp} AND {Warehouse_Oldempdept_Container.field.fromdate} <= {timestamp} ORDER BY {Warehouse_Oldempdept_Container.field.datetime} ASC'
        # rows = select_from_warehouse_oldempdept(warehouse_db_connection, empid = empid, extra_clause = extra_clause, return_dc = True)
        # warehouse_db_connection.close()

        query = f'SELECT * FROM {Warehouse_Oldempdept_Container.field.tablename} WHERE {Warehouse_Oldempdept_Container.field.empid} = ? AND {Warehouse_Oldempdept_Container.field.fromdate} <= ? AND {Warehouse_Oldempdept_Container.field.todate} >= ? ORDER BY {Warehouse_Oldempdept_Container.field.datetime} ASC'

        values=(empid,timestamp, timestamp) 
        # print(query, values)

        rows= run_select_query(warehouse_db_connection, query, values, Warehouse_Oldempdept_Container, return_dc=True)
        # print(1, len(rows))

        if len(rows)==1:
            # return rows[0]
            final_dept_id = rows[0].deptid
        elif len(rows)==0:
            if datetime.strptime(timestamp,timestamp_format) < datetime.strptime(CONFIG['ARCHIVE']['start_date'],"%Y-%m-%d"):
                # raise ValueError("There is no shift for selected date")
                if DEBUG:
                    print("Dep: Time stamp is before archives startime")
                return -1
            else:
                print('employee not registered at that time')
                return -3
        else:
            # print("Dep rows:",rows)
            if DEBUG:
                print("Department is found in more than one archive duration")
            final_dept_id = rows[-1].deptid
            # raise Exception("shift is found in more than one archive duration")
          
    query = f'SELECT * FROM {Warehouse_Olddeptchange_Container.field.tablename} WHERE {Warehouse_Olddeptchange_Container.field.deptid}  = ? AND {Warehouse_Olddeptchange_Container.field.fromdate} <= ? AND {Warehouse_Olddeptchange_Container.field.todate} >= ? ORDER BY {Warehouse_Olddeptchange_Container.field.datetime} ASC'
    
    values=(final_dept_id,timestamp, timestamp)
    # print(query, values)
    
    rows= run_select_query(warehouse_db_connection, query, values, Warehouse_Olddeptchange_Container, return_dc=True)
    warehouse_db_connection.close()
    
    if not len(rows)>0:
        person_db_connection = create_connection(CONFIG['DB']['person_db'])
        res = get_department_from_db(person_db_connection, deptid = final_dept_id, return_dc = True)
        person_db_connection.close()
        if len(res) > 0:
            return 0, res[0]
        else:
            return -2 
    elif len(rows) == 1:
        return 1,rows[0]
    else:
        if DEBUG:
            print("multiple department details changed in a day:")#,rows)
        return 1,rows[-1]
            
def get_compay_holiday_list(year):
    #import from db any holidays other than usual
    republic_day = date(day=26,month=1, year=year)
    independence_day = date(day=15,month=8, year=year)
    gandhi_jayanthi = date(day=2,month=10, year=year)
    holidays = [republic_day, independence_day, gandhi_jayanthi]

    fromdate =str(date(day=1, month= 1, year= year))
    todate =str(date(day=31, month= 12, year= year))
    
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    holidays_from_db = select_from_holiday(person_db_connection,htype = "Company",fromdate=fromdate,todate=todate, return_dc= True)
    person_db_connection.close()
    
    holidays_from_db = [str(i.date) for i in holidays_from_db]
    holidays.extend(holidays_from_db)
    
    return holidays

def get_department_holiday_list(year, deptid = None):
    #import from db
    if deptid == None:
        return []
    
    fromdate =str(date(day=1, month= 1, year= year))
    todate =str(date(day=31, month= 12, year= year))
    
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    holidays_from_db = select_from_holiday(person_db_connection,htype = "Department",fromdate=fromdate,todate=todate,deptid= deptid,return_dc= True)
    person_db_connection.close()
    
    holidays_from_db = [str(i.date) for i in holidays_from_db]
    return holidays_from_db










