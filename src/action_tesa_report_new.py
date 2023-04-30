import pandas as pd
import numpy as np
from .dbutils import create_connection
from .load_config import CONFIG
from .dbutils import run_fetch_query, run_query_noreturn
# from .global_vars import PEOPLE_TABLE_FIELDS, PEOPLE_TABLE, ROSTER_TABLE_FIELDS,  \
#                          ROSTER_TABLE, ONLINE_LOG_TABLE_FIELDS, ONLINE_LOG_TABLE
import random, string, os
from .report import write_report

from datetime import datetime,timedelta,date
from calendar import monthrange
import xlsxwriter
from collections import defaultdict

from .action_tesa_report_utils import get_time_difference,get_dates_in_between,get_next_date,get_prev_date,string_to_time,string_to_seconds,days_of_month,get_department,get_shift,get_date_and_time,get_compay_holiday_list,get_department_holiday_list, time_to_seconds

from .dbcontainers import Auth_Login_Container, Auth_User_Container, Face_Identity_Container,\
                          Face_Vector_Container,Person_Alerts_container, Person_Attendance_Log_container, Person_Department_Container,\
                          Person_Holiday_Container, Person_Location_Container, Person_Person_Details_Container,\
                          Person_Roster_Container, Warehouse_Olddeptchange_Container, Warehouse_Oldempdept_Container,\
                          Warehouse_Oldempshifts_Container, DB_Container, base_dataclass

from .queries import select_from_person_details

# from .global_vars import Warehouse_Oldempdept,Warehouse_Oldempdept_Fields,Warehouse_Oldempshifts,Warehouse_Oldempshifts_Fields,Person_Roster,Person_Roster_Fields,Person_Person_Details,Person_Person_Details_Fields,Person_Location,Person_Location_Fields,Person_Holiday,Person_Holiday_Fields,Person_Department,Person_Department_Fields,Person_Attendance_Log,Person_Attendance_Log_Fields

ENTRY_CAMERA_NAME="ENTRY"#CONFIG["IPCAMERA_1"]["camera_name"]
EXIT_CAMERA_NAME="EXIT"#CONFIG["IPCAMERA_2"]["camera_name"]
IN_TIME_FORMAT="%Y-%m-%d %H:%M:%S.%f"
# static_in_time_string='09:00:00.000000'
# static_in_time=datetime.strptime(static_in_time_string,"%H:%M:%S.%f")
# shift_intime_dict={}
RELAXATION_TIME=int(CONFIG["DAILY_REPORT"]["daily_late_relaxation_time_in_minutes"])*60
RELAXATION_TIME_EXIT=int(CONFIG["DAILY_REPORT"]["daily_late_relaxation_time_in_minutes"])*60

FULL_DAY_LEAVE_LIMIT=int(CONFIG["DAILY_REPORT"]["min_working_hours_for_not_full_day_leave"])*3600

HALF_DAY_LEAVE_LIMIT=int(CONFIG["DAILY_REPORT"]["min_working_hours_for_not_half_day_leave"])*3600


GAP_TIME_HOURS=int(CONFIG["DAILY_REPORT"]["gap_time_between_shift_for_dynamic_shift_in_hours"])


MISPUNCH_GAP_TIME = int(CONFIG['DAILY_REPORT']['mispunch_gap_time_in_minutes'])*60

OFFDAY_GOODWORKING_MIN_TIME = int(CONFIG['DAILY_REPORT']['offday_good_working_minimum_time_in_minutes'])*60
# print("checking daily report: ,",RELAXATION_TIME,GAP_TIME_HOURS)
GAP_TIME_FOR_DYNAMIC=timedelta(seconds=GAP_TIME_HOURS*3600)
DYNAMIC_SHIFT_NAME="Dynamic"
DYNAMIC_SHIFT_ID="D"

EMPLOYEE_TIME_STAMP_FORMAT="%Y-%m-%d %H:%M:%S.%f"


WEEKDAYS = ["Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"]

DEBUG = False

def extract_action_tesa_daily_report_data(person_db_connection, user_map, start_date=None, end_date=None,location=None,day_start_time="00:00:01",include_prev_day=False, first_in_last_out = False, get_cam_logs = False):
    
    # print("\ninclude_prev_day: ",include_prev_day, start_date, end_date)
    
    emp_id=None
    emp_details=None
    for key,value in user_map.items():
        emp_id=key
        emp_details=value
    
    # print("employee details: ",emp_id)#,emp_details)
    emp_name,emp_status,emp_curr_dept,emp_curr_shift,emp_curr_dept_location,emp_details_timestamp=emp_details.name, emp_details.empstatus, emp_details.currdept, emp_details.currshift, emp_details.location, emp_details.depttimestamp
    
    emp_curr_dept_timestamp = emp_details.depttimestamp
    emp_curr_shift_timestamp = emp_details.shifttimestamp
    
    # print("TIMESTAMP", emp_curr_shift_timestamp, emp_curr_dept_timestamp, type(emp_curr_shift_timestamp), type(emp_curr_dept_timestamp))
    
    #TODO replace hod by hod name and entry no - format hodname(entry no)
    emp_curr_dept_hod=None
    #GET DEPARTMENT HOD
    
    emp_curr_dept_name=None
    
    emp_curr_shift_startime=None
    #GET SHIFT START TIME AND NAME AND OFF DAY
    
    emp_curr_shift_end_time=None
    
    emp_curr_shift_name=None
    
    day_type=None
    
    emp_daily_work_status=None
    
    emp_weekly_off_day=None
    
    mispunch_status=False
    
    #if person is unregistered as employee
    if emp_status=="Non-Employee":
        # print("Person: ",emp_name,"is currently not an employee")
        return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
    
    #checking timestamp of employee to get current shift and department details
    # if not datetime.strptime(start_date,"%Y-%m-%d")>=datetime.strptime(emp_details_timestamp,EMPLOYEE_TIME_STAMP_FORMAT):
#     no_log_status=None
        
#     res3_no_log=[[emp_id,emp_curr_dept_hod,emp_name,emp_curr_shift_name,emp_curr_dept_name,start_date_copy,None,start_date_copy,None,None,None,no_log_status,None]]
    
#     res3_names=['ENTRY NUMBER','HOD','NAME','SHIFT','DEPARTMENT','ENTRY DATE','ENTRY TIME','EXIT DATE', 'EXIT TIME', 'LATE BY','TOTAL WORKING TIME','STATUS','DAY TYPE']
#     res3_no_log = pd.DataFrame(res3_no_log,columns=res3_names)
    
    if True:
        
        # print("Date chosen is not in current timestamp")
        shift_details=get_shift(emp_id,emp_curr_shift, str(emp_curr_shift_timestamp), start_date,"%Y-%m-%d")
        # print("sd", shift_details)
        if isinstance(shift_details,int):
            if DEBUG:
                print("Date chosen is before starttime", shift_details)
            return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
        if shift_details[0] == 0:
            shift_details = shift_details[1]
            emp_curr_shift,emp_curr_shift_name,emp_curr_shift_startime,emp_curr_shift_end_time,emp_weekly_off_day=shift_details.rid, shift_details.name, shift_details.starttime, shift_details.endtime, shift_details.offday
        elif shift_details[0] ==1:
            shift_details = shift_details[1]
            emp_curr_shift,emp_curr_shift_name,emp_curr_shift_startime,emp_curr_shift_end_time,emp_weekly_off_day=shift_details.shift, shift_details.shiftname, shift_details.starttime, shift_details.endtime, shift_details.offday
            
        
        department_details=get_department(emp_id,emp_curr_dept,str(emp_curr_dept_timestamp),start_date,"%Y-%m-%d")
        if isinstance(department_details,int):
            if DEBUG:
                print("Date chosen is before starttimne", department_details)
            return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
        
        if department_details[0]==0:
            department_details = department_details[1]
            emp_curr_dept,emp_curr_dept_name,emp_curr_dept_location,emp_curr_dept_hod=department_details.deptid, department_details.deptname, department_details.location, department_details.depthod
        
        elif department_details[0]==1:
            department_details = department_details[1]
            emp_curr_dept,emp_curr_dept_name,emp_curr_dept_location,emp_curr_dept_hod=department_details.deptid, department_details.deptname, department_details.location, department_details.depthod
        
        # print("shift details",shift_details)
        # print("department details",department_details)
    
    # start_date_datetime=datetime.strptime(start_date,"%Y-%m-%d")
    
    # print("department", emp_curr_dept, emp_curr_dept_name)
    
    start_date_copy=start_date
    end_date_copy=end_date
    
    day_start_time_seconds=string_to_seconds(day_start_time,"%H:%M:%S")
    if day_start_time_seconds!=0:
        end_date=get_next_date(end_date,"%Y-%m-%d")
#     print("User map: ",user_map)
    
    table1 = Person_Attendance_Log_container.field.tablename
    table2 = Person_Person_Details_Container.field.tablename
    table3 = Person_Roster_Container.field.tablename
    table4= Person_Department_Container.field.tablename
    
    column_order = ['A.intime', 'A.outtime', 'A.firstlocation','A.lastseenlocation']
    # column_names = ['.'.join(v.split('.')[1:]) for v in column_order]
    # column_names[column_order.index('A.firstlocation')]="TYPE"
    column_names=['INTIME','OUTTIME','TYPE']
    
    res1_indices=[column_order.index(i) for i in ['A.intime', 'A.outtime', 'A.firstlocation']]
    res1_names=['ENTRY NUMBER','NAME','SHIFT','DEPARTMENT','DATE','INTIME','OUTTIME','TYPE']
    
    res1_column_insert_dict={0:('ENTRY NUMBER',emp_id),1:('NAME',emp_name),
                             2:('SHIFT',emp_curr_shift_name),3:('DEPARTMENT',emp_curr_dept_name)}

    column_names2=['ENTRY DATE','ENTRY TIME','EXIT DATE', 'EXIT TIME', 'WORK HOURS SPENT']
    
    res2_names=['ENTRY NUMBER','NAME','SHIFT','DEPARTMENT','ENTRY DATE','ENTRY TIME','EXIT DATE', 'EXIT TIME', 'WORK HOURS SPENT']
    
    res2_column_insert_dict={0:('ENTRY NUMBER',emp_id),1:('NAME',emp_name),
                             2:('SHIFT',emp_curr_shift_name),3:('DEPARTMENT',emp_curr_dept_name)}
    
    column_names3=column_names2[:-1]+['LATE BY','TOTAL WORKING TIME','STATUS','DAY TYPE']
    
    res3_names=['ENTRY NUMBER','HOD','NAME','SHIFT','DEPARTMENT','ENTRY DATE','ENTRY TIME','EXIT DATE', 'EXIT TIME', 'LATE BY','TOTAL WORKING TIME','STATUS','DAY TYPE']
    
    
    res3_column_insert_dict={0:('ENTRY NUMBER',emp_id),1:('HOD',emp_curr_dept_hod),2:('NAME',emp_name),
                             3:('SHIFT',emp_curr_shift_name),4:('DEPARTMENT',emp_curr_dept_name)}
    
    partial_query = [
        'SELECT',
        ', '.join(column_order),
        'FROM', table1, 'AS A'
    ]

    where_clause = []
    search_tuple = []
    
    prev_last_seen_time=None
    if include_prev_day==True:
        prev_day_res=extract_action_tesa_daily_report_data(person_db_connection, user_map, start_date=get_prev_date(start_date_copy,"%Y-%m-%d"), end_date=get_prev_date(end_date_copy,"%Y-%m-%d"),location=location,day_start_time=day_start_time,include_prev_day=False, get_cam_logs = get_cam_logs)
        prev_day_res3=prev_day_res[-1]
        # print("prev day results of :",start_date_copy,"\n", prev_day_res3.to_string())
        if len(prev_day_res3)>0:
            date,time=prev_day_res3.iloc[0]['EXIT DATE'],prev_day_res3.iloc[0]['EXIT TIME']
            
            if time== None:
                prev_last_seen_time= None
            else:
                prev_last_seen_time=date+" "+time
            # print("previous last seen time:", prev_last_seen_time)

    ##setting window for daily logs###
    # print("emp_curr_shift_startime & emp_curr_shift_end_time:", emp_curr_shift_startime, "--", emp_curr_shift_end_time)
    # start_date_window_start_time_seconds = end_date_window_end_time_seconds = 1
    start_date_window_start_time_seconds = end_date_window_end_time_seconds = day_start_time_seconds

    if emp_curr_shift_end_time!=None and emp_curr_shift_startime!=None and abs(emp_curr_shift_end_time-emp_curr_shift_startime)<86400 and not get_cam_logs:
        start_date_window_start_time_seconds = emp_curr_shift_startime - GAP_TIME_HOURS*3600
        end_date_window_end_time_seconds = emp_curr_shift_end_time + GAP_TIME_HOURS*3600

        if emp_curr_shift_end_time > emp_curr_shift_startime:
            end_date = start_date
        else:
            #no change in end_date as it is already one day after start date
            pass

    # print("start_date_window_start_time_seconds, end_date_window_end_time_seconds, GAP_TIME_HOURS are: ", start_date_window_start_time_seconds,  end_date_window_end_time_seconds,  GAP_TIME_HOURS)

    if start_date:
        if day_start_time_seconds!=0:
            where_clause.append('A.intime >= ?')
            start_date=datetime.strptime(start_date,"%Y-%m-%d")
            # start_date=start_date+timedelta(seconds=day_start_time_seconds)
            start_date=start_date+timedelta(seconds= start_date_window_start_time_seconds)
            if prev_last_seen_time!=None:
                prev_last_seen_time=datetime.strptime(prev_last_seen_time,"%Y-%m-%d %H:%M:%S")
                prev_day_gap=start_date-prev_last_seen_time
                prev_day_end=prev_last_seen_time+prev_day_gap
                # print("startdate,prevdaylastseen",start_date, prev_last_seen_time)
                # print("prev_day_gap: ",prev_day_gap)
                # print(prev_day_end)
                if prev_last_seen_time>start_date:
                    start_date=prev_last_seen_time+timedelta(seconds=1)
                    if DEBUG:
                        print("\nstart date changed: ",start_date)
                else:
                    if DEBUG:
                        print("\nno change in start date: ",start_date)
                
            start_date=str(start_date)
        else:
            where_clause.append(f'A.date >= ?')
        search_tuple.append(start_date)
        
    if end_date:
        if day_start_time_seconds!=0:
            where_clause.append(f'A.outtime <= ?')
            end_date=datetime.strptime(end_date,"%Y-%m-%d")
            # end_date=end_date+timedelta(seconds=day_start_time_seconds)
            end_date=end_date+timedelta(seconds=end_date_window_end_time_seconds)
            end_date=str(end_date)
        else:
            where_clause.append(f'A.date <= ?')
        search_tuple.append(end_date)
        
    where_clause.append(f'A.empid = ?')
    search_tuple.append(emp_id)

    where_clause_string = ' AND '.join(where_clause)
    query = ' '.join(partial_query + ['WHERE', where_clause_string])
    
    # print("start date with time: ",start_date)
    # print("end date with time: ",end_date)    
    # print("\n,query : ",query)
    # print("\n values: ",search_tuple)
    res = run_fetch_query(person_db_connection, query=query, values=tuple(search_tuple))
    
    if DEBUG:
        print("results of query:",len(res),"\n")#, res)
    
#     print("res length: ",len(res))
#     print("cam names:",ENTRY_CAMERA_NAME,EXIT_CAMERA_NAME,type(ENTRY_CAMERA_NAME))

    #get day type
    #TODO INCLUDE HOLIDAYS AND MISPUNCH REPORT STATUS
    start_date_datetime=datetime.strptime(start_date_copy,"%Y-%m-%d")
    company_holiday_list=get_compay_holiday_list(start_date_datetime.year)
    department_holiday_list=get_department_holiday_list(start_date_datetime.year, deptid = emp_curr_dept)
    
    if start_date_copy in company_holiday_list:
        day_type="Company Holiday"
    elif start_date_copy in department_holiday_list:
        day_type="Department Holiday"
    elif  WEEKDAYS[start_date_datetime.weekday()]==emp_weekly_off_day:
        day_type="Weekly Off"
    else:
        day_type="Working Day"
    
    # ['ENTRY NUMBER','HOD','NAME','SHIFT','DEPARTMENT','ENTRY DATE','ENTRY TIME','EXIT DATE', 'EXIT TIME', 'LATE BY','TOTAL WORKING TIME','STATUS','DAY TYPE']
    no_log_status=None
    if day_type=="Working Day":
        no_log_status="Full Day Absent"
    else:
        no_log_status=day_type
        
    res3_no_log=[[emp_id,emp_curr_dept_hod,emp_name,emp_curr_shift_name,emp_curr_dept_name,start_date_copy,None,start_date_copy,None,None,None,no_log_status,day_type]]
    
    res3_no_log = pd.DataFrame(res3_no_log,columns=res3_names)
        
    if len(res)<1:
        # print("error",len(res3_no_log),len(res3_names))
        # print("res3nolog",start_date_copy, res3_no_log)
        if DEBUG:
            print("checkpoint5")

        # if emp_daily_work_status == "Mispunched" or no_log_status == "Mispunched":
        #     print("MP LEN -3: ", len(res))
        return pd.DataFrame([]),pd.DataFrame([]),res3_no_log
    
#     print("\nresult1: ",res[0])
    if len(res)==1:
        res1 = pd.DataFrame([tuple(res[0][i] for i in res1_indices)], columns=column_names)

        last_seen_time_index=column_order.index('A.outtime')
        exit_time = get_date_and_time(res[0][last_seen_time_index])[1]
        res1.insert(0,"DATE",0)
        res1['DATE']=res1['INTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[0])
        res1['INTIME']=res1['INTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[1])
        res1['OUTTIME']=res1['OUTTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[1])
        for key,value in res1_column_insert_dict.items():
            res1.insert(key,value[0],value[1])
            
        # print("norows289")
        res2=pd.DataFrame([])
        
        no_log_status = "Mispunched"
        # print(res1["TYPE"][0])
        if res1['TYPE'][0]==EXIT_CAMERA_NAME and not first_in_last_out:
            res3_no_log=[[emp_id,emp_curr_dept_hod,emp_name,emp_curr_shift_name,emp_curr_dept_name,start_date_copy,None,start_date_copy,exit_time,None,None,no_log_status,day_type]]
        else:
            res3_no_log=[[emp_id,emp_curr_dept_hod,emp_name,emp_curr_shift_name,emp_curr_dept_name,start_date_copy,exit_time,start_date_copy,None,None,None,no_log_status,day_type]]
        # res3_no_log=[[emp_id,emp_curr_dept_hod,emp_name,emp_curr_shift_name,emp_curr_dept_name,start_date_copy,None,start_date_copy,None,None,None,no_log_status,day_type]]
        #should consider previous day results
        #if prev last seen time and in time diff is less than gap time, it is full day absent, else:mispunched
        # res3_mispunched=[emp_id,emp_curr_dept_hod,emp_name,emp_curr_shift_name,emp_curr_dept_name,start_date_copy,res1['INTIME'],start_date_copy,res1['OUTTIME'],None,None,,day_type]
        if DEBUG:
            print("checkpoint6")

        # if emp_daily_work_status == "Mispunched" or no_log_status == "Mispunched":
        #     print("MP LEN -2: ", len(res))
        # return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
        return res1,res2,pd.DataFrame(res3_no_log,columns=res3_names)
        
    rows=[]
    last_seen_location=None
    last_seen_time=None
     
    ##Getting first row of the day
    last_seen_location_index=column_order.index('A.lastseenlocation')
    last_seen_time_index=column_order.index('A.outtime')
    in_time=None 

    late_by_seconds=0
    late_by=str(timedelta(seconds=0))
    # mispunch_gap_start = None
    mispunch_gap_max = 0
    k=None
    
    #####CALCULATING LATEBY FOR FILO########
    if first_in_last_out:
        filo_in_time=res[0][last_seen_time_index]
        filo_in_time=string_to_seconds(filo_in_time, IN_TIME_FORMAT)
        # mispunch_gap_start = string_to_seconds(in_time,IN_TIME_FORMAT)
        late_by_seconds=filo_in_time-emp_curr_shift_startime#in shift startime in seconds
        if late_by_seconds>0:##late penalty
            late_by=str(timedelta(seconds=late_by_seconds))
        # print("FILO late_by:", late_by)



    ##################### First in Last out total time ###########################
    first_in_last_out_time_duration_seconds = 0
    if first_in_last_out:
        try:
            # first_in_time = rows[0][column_order.index('A.intime')]
            # last_out_time = rows[-1][column_order.index('A.outtime')]
            first_in_time = res[0][column_order.index('A.intime')]
            last_out_time = res[-1][column_order.index('A.outtime')]
            first_in_last_out_time_duration_seconds = string_to_seconds(get_time_difference(first_in_time, last_out_time, IN_TIME_FORMAT),"%H:%M:%S")
            # print("FILO first_in_last_out_time_duration_seconds: ", first_in_last_out_time_duration_seconds, "hours", first_in_last_out_time_duration_seconds//3600)
        except:
            print("ERROR_FILO")
            pass

        total_time_duration_seconds = 0
        if first_in_last_out and first_in_last_out_time_duration_seconds!=0:
            total_time_duration_seconds = first_in_last_out_time_duration_seconds

       #get daily work status  
        if day_type!="Working Day":
            if total_time_duration_seconds >= OFFDAY_GOODWORKING_MIN_TIME:
                emp_daily_work_status = "Good Working"
            else:
                emp_daily_work_status = day_type
        elif  total_time_duration_seconds<FULL_DAY_LEAVE_LIMIT:
            emp_daily_work_status="Full Day Leave"
        elif total_time_duration_seconds<HALF_DAY_LEAVE_LIMIT:
            emp_daily_work_status="Half Day Leave"
        else:
            if not emp_curr_shift==DYNAMIC_SHIFT_ID:
                # print("error",emp_details, rows[-1][column_order.index('A.outtime')])
                if late_by_seconds>RELAXATION_TIME:
                    emp_daily_work_status="Late Comer"
                else:
                    if first_in_last_out:
                        leaving_time = string_to_seconds(res[-1][column_order.index('A.outtime')],IN_TIME_FORMAT)
                        # print("leaving_time filo:",leaving_time, res[-1][column_order.index('A.outtime')])
                    else:
                        leaving_time = string_to_seconds(rows[-1][column_order.index('A.outtime')],IN_TIME_FORMAT)
                        # print("leaving_time WITHOUT filo:",leaving_time, res[-1][column_order.index('A.outtime')])

                    # print("Early leaver RELAXATION_TIME_EXIT in minutes: ",RELAXATION_TIME_EXIT/60, "early leaving_time in minutes: ",(emp_curr_shift_end_time- leaving_time)/60)

                    if leaving_time <emp_curr_shift_end_time-RELAXATION_TIME_EXIT:
                        emp_daily_work_status="Early Leaver"
        #mispunched and absent categories are dealt above and present is dealt below.
    
        res1 = res2 = res3 = pd.DataFrame([])
        in_time,firstseenlocation,out_time,lastseenlocation=res[0][column_order.index('A.intime')],res[0][column_order.index('A.firstlocation')],res[-1][column_order.index('A.outtime')],res[-1][column_order.index('A.lastseenlocation')]
        in_date,in_time=get_date_and_time(in_time,IN_TIME_FORMAT)
        out_date,out_time=get_date_and_time(out_time,IN_TIME_FORMAT)
        res3=(in_date,in_time,out_date,out_time)
        # print("FILO res3:", res3)

        if day_type=="Working Day" and emp_daily_work_status==None:
            emp_daily_work_status="Present"
        
        if day_type=="Working Day" and mispunch_status==True:
            if not first_in_last_out:
                emp_daily_work_status="Mispunched"
            else:
                if DEBUG:
                    print("mispunch_status is not considered")
                pass

        # total_time_duration=sum([string_to_seconds(i[column_names.index("Time duration")],"%H:%M:%S") for i in rows])
        total_time_duration=str(timedelta(seconds=total_time_duration_seconds))
        if emp_curr_shift==DYNAMIC_SHIFT_ID:
            late_by=str(timedelta(seconds=0))

        res3=[res3+(late_by,total_time_duration,emp_daily_work_status,day_type)]
        res3=pd.DataFrame(res3,columns=column_names3)
        
        for key,value in res3_column_insert_dict.items():
            res3.insert(key,value[0],value[1])
        
        if DEBUG:
            print("filocheckpoint10")

        # if emp_daily_work_status == "Mispunched" or no_log_status == "Mispunched":
        #     print("MP LEN -1: ", len(res))

        return res1,res2,res3

    is_first_seen_location_exit = False
    for i in range(len(res)):
        if res[i][last_seen_location_index]==ENTRY_CAMERA_NAME:
            k=i
            rows.append(list(res[i]))
            in_time=res[i][last_seen_time_index]
            in_time=string_to_seconds(in_time,IN_TIME_FORMAT)
            # mispunch_gap_start = string_to_seconds(in_time,IN_TIME_FORMAT)
            if not first_in_last_out:
                late_by_seconds=in_time-emp_curr_shift_startime#in shift startime in seconds
                if late_by_seconds>0:##late penalty
                    late_by=str(timedelta(seconds=late_by_seconds))##string  H:M:S format
                    # print("late_by NOT FILO:", late_by)
            break
        else:
            is_first_seen_location_exit = True
            
    if k==None:
        if DEBUG:
            print("checkpoint7")
        if is_first_seen_location_exit:
            no_log_status = "Mispunched"
        if len(res)>0:
            exit_time = get_date_and_time(res[0][last_seen_time_index])[1]
        if not first_in_last_out:
            res3_no_log=[[emp_id,emp_curr_dept_hod,emp_name,emp_curr_shift_name,emp_curr_dept_name,start_date_copy,None,start_date_copy,exit_time,None,None,no_log_status,day_type]]
        else:
            res3_no_log=[[emp_id,emp_curr_dept_hod,emp_name,emp_curr_shift_name,emp_curr_dept_name,start_date_copy,exit_time,start_date_copy,None,None,None,no_log_status,day_type]]
        if len(res)>0:
            res1 = pd.DataFrame([tuple(res[j][i] for i in res1_indices) for j in range(len(res))], columns=column_names)
            res1.insert(0,"DATE",0)
            res1['DATE']=res1['INTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[0])
            res1['INTIME']=res1['INTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[1])
            res1['OUTTIME']=res1['OUTTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[1])
            for key,value in res1_column_insert_dict.items():
                res1.insert(key,value[0],value[1])
            return res1,pd.DataFrame([]),pd.DataFrame(res3_no_log,columns=res3_names)
        return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame(res3_no_log,columns=res3_names)
    if k==len(res)-1: 
        res1 = pd.DataFrame([tuple(res[-1][i] for i in res1_indices)], columns=column_names)
        res1.insert(0,"DATE",0)
        res1['DATE']=res1['INTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[0])
        res1['INTIME']=res1['INTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[1])
        res1['OUTTIME']=res1['OUTTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[1])
        for key,value in res1_column_insert_dict.items():
            res1.insert(key,value[0],value[1])
        res2=pd.DataFrame([])
        no_log_status = "Mispunched"
        try:
            single_log_date = res1["DATE"][0]
        except:
            single_log_date = start_date_copy
        res3_no_log=[[emp_id,emp_curr_dept_hod,emp_name,emp_curr_shift_name,emp_curr_dept_name,single_log_date,res1['INTIME'][0],None,None,None,None,no_log_status,day_type]]
        if DEBUG:
            print("checkpoint8")
        return res1,res2,pd.DataFrame(res3_no_log,columns=res3_names)
        
    for i in range(k+1,len(res)):
        time,location=res[i][last_seen_time_index],res[i][last_seen_location_index]
        if location!=last_seen_location:
            if location==EXIT_CAMERA_NAME:
                rows[-1][last_seen_time_index],rows[-1][last_seen_location_index]=time,location
            elif location==ENTRY_CAMERA_NAME:
                rows.append(list(res[i]))
            last_seen_location=location
        else:
            mispunch_gap_start = string_to_seconds(rows[-1][last_seen_time_index], IN_TIME_FORMAT)
            mispunch_gap_end = string_to_seconds(time, IN_TIME_FORMAT)
            mispunch_gap_max =  max(mispunch_gap_end - mispunch_gap_start, mispunch_gap_max)
            if mispunch_gap_max>MISPUNCH_GAP_TIME:
                mispunch_status = True
            # mispunch_gap_start = mispunch_gap_end
            
    current_day_rows_len=len(rows)
    ##INCLUDING NEXT DAY RESULTS FOR DYNAMIC ROSTER
    next_day_res=None
#     print("person shift: ",emp_shift)
#     print("Dynmic shift id:",DYNAMIC_SHIFT_NAME)
    if emp_curr_shift==DYNAMIC_SHIFT_ID:
        if day_start_time_seconds!=0:
            search_tuple[where_clause.index(f'A.intime >= ?')]=end_date
            next_date=get_next_date(end_date,"%Y-%m-%d %H:%M:%S")
            next_date=datetime.strptime(next_date,"%Y-%m-%d")+timedelta(seconds=day_start_time_seconds)
            next_date=str(next_date)
            search_tuple[where_clause.index(f'A.outtime <= ?')]=next_date
        else:
            next_date=get_next_date(end_date)
            search_tuple[where_clause.index(f'A.date >= ?')]=next_date
            search_tuple[where_clause.index(f'A.date <= ?')]=next_date
        next_day_res = run_fetch_query(person_db_connection, query=query, values=tuple(search_tuple))
        # print("startdate,copy",start_date, start_date_copy)
        # print("next day queries and values: ",query,"\n",search_tuple)
        # print("nextdayres", next_day_res)
        # print("last sen location", last_seen_location)
        if last_seen_location==ENTRY_CAMERA_NAME:
            if not len(next_day_res)>0:
                removed=rows.pop()
            elif next_day_res[0][last_seen_location_index]==ENTRY_CAMERA_NAME:
                removed=rows.pop()
            elif next_day_res[0][last_seen_location_index]==EXIT_CAMERA_NAME:
                gap_start_time=next_day_res[0][last_seen_time_index]
                gap_start_time=datetime.strptime(gap_start_time,IN_TIME_FORMAT)
                gap_end_time=gap_start_time
                gap_time=gap_end_time-gap_start_time
                rows[-1][last_seen_time_index]=next_day_res[0][last_seen_time_index]
                rows[-1][last_seen_location_index]=next_day_res[0][last_seen_location_index]
                next_day_rows=[rows.pop()] 
                last_seen_location=EXIT_CAMERA_NAME
                for i in range(1,len(next_day_res)):
                    location=next_day_res[i][last_seen_location_index]
                    time=datetime.strptime(next_day_res[i][last_seen_time_index],IN_TIME_FORMAT)
                    if location!=last_seen_location:
                        if location==ENTRY_CAMERA_NAME:
                            gap_end_time=time
                            gap_time=gap_end_time-gap_start_time
                            if DEBUG:
                                print("in gap time: ",gap_time)
                            if gap_time>=GAP_TIME_FOR_DYNAMIC:
                                break
                            else:
                                next_day_rows.append(list(next_day_res[i]))
                        elif location==EXIT_CAMERA_NAME:
                            gap_start_time=time
                            next_day_rows[-1][last_seen_time_index]=next_day_res[i][last_seen_time_index]
                            next_day_rows[-1][last_seen_location_index]=location
                        last_seen_location=location
                            
                    elif location==last_seen_location:
                        if location==EXIT_CAMERA_NAME:
                            gap_start_time=time
                            mispunch_gap_start = string_to_seconds(next_day_rows[-1][last_seen_time_index], IN_TIME_FORMAT)
                            next_day_rows[-1][last_seen_time_index]=next_day_res[i][last_seen_time_index]
                            
                            mispunch_gap_end = string_to_seconds(next_day_rows[-1][last_seen_time_index], IN_TIME_FORMAT)
                            mispunch_gap_max =  max(mispunch_gap_end - mispunch_gap_start, mispunch_gap_max)
                            if mispunch_gap_max>MISPUNCH_GAP_TIME:
                                mispunch_status = True
                        elif location==ENTRY_CAMERA_NAME:
                            gap_end_time=time
                            mispunch_gap_start = string_to_seconds(next_day_rows[-1][last_seen_time_index], IN_TIME_FORMAT)
                            next_day_rows[-1][last_seen_time_index]=next_day_res[i][last_seen_time_index]
                            
                            mispunch_gap_end = string_to_seconds(next_day_rows[-1][last_seen_time_index], IN_TIME_FORMAT)
                            mispunch_gap_max =  max(mispunch_gap_end - mispunch_gap_start, mispunch_gap_max)
                            if mispunch_gap_max>MISPUNCH_GAP_TIME:
                                mispunch_status = True
                            
#                 print("next day rows: ",next_day_rows)            
                rows.extend(next_day_rows)
                            
        elif last_seen_location==EXIT_CAMERA_NAME and len(next_day_res)>0:
            gap_start_time=rows[-1][last_seen_time_index]
            gap_start_time=datetime.strptime(gap_start_time,IN_TIME_FORMAT)
            gap_end_time=next_day_res[0][last_seen_time_index]
            gap_end_time=datetime.strptime(gap_end_time,IN_TIME_FORMAT)
            gap_time=gap_end_time-gap_start_time
            next_day_rows=[rows.pop()]
#             print("gap time:",gap_time)
#             print("gap start and end: ",rows[-1][last_seen_time_index],next_day_res[0][last_seen_time_index])
#             print("gap start and end: ",gap_start_time,gap_end_time)
            if gap_time<GAP_TIME_FOR_DYNAMIC:
                for i in range(len(next_day_res)):
                    location=next_day_res[i][last_seen_location_index]
                    time=datetime.strptime(next_day_res[i][last_seen_time_index],IN_TIME_FORMAT)
                    if location!=last_seen_location:
                        if location==ENTRY_CAMERA_NAME:
                            gap_end_time=time
                            gap_time=gap_end_time-gap_start_time
                            if gap_time>=GAP_TIME_FOR_DYNAMIC:
                                break
                            else:
                                next_day_rows.append(list(next_day_res[i]))
                        elif location==EXIT_CAMERA_NAME:
                            gap_start_time=time
                            next_day_rows[-1][last_seen_time_index]=next_day_res[i][last_seen_time_index]
                            next_day_rows[-1][last_seen_location_index]=location
                        last_seen_location=location

                    elif location==last_seen_location:
                        if location==EXIT_CAMERA_NAME:
                            gap_start_time=time
                            mispunch_gap_start = string_to_seconds(next_day_rows[-1][last_seen_time_index], IN_TIME_FORMAT)
                            next_day_rows[-1][last_seen_time_index]=next_day_res[i][last_seen_time_index]
                            
                            mispunch_gap_end = string_to_seconds(next_day_rows[-1][last_seen_time_index], IN_TIME_FORMAT)
                            mispunch_gap_max =  max(mispunch_gap_end - mispunch_gap_start, mispunch_gap_max)
                            if mispunch_gap_max>MISPUNCH_GAP_TIME:
                                mispunch_status = True
                        elif location==ENTRY_CAMERA_NAME:
                            gap_end_time=time
                            mispunch_gap_start = string_to_seconds(next_day_rows[-1][last_seen_time_index], IN_TIME_FORMAT)
                            next_day_rows[-1][last_seen_time_index]=next_day_res[i][last_seen_time_index]
                            
                            mispunch_gap_end = string_to_seconds(next_day_rows[-1][last_seen_time_index], IN_TIME_FORMAT)
                            mispunch_gap_max =  max(mispunch_gap_end - mispunch_gap_start, mispunch_gap_max)
                            if mispunch_gap_max>MISPUNCH_GAP_TIME:
                                mispunch_status = True
#             print("next day rows2: ",next_day_rows)
            rows.extend(next_day_rows)
    else:
        # print("going 3", last_seen_location, ENTRY_CAMERA_NAME)
        if last_seen_location==ENTRY_CAMERA_NAME:
            #adding mispunch as last log of the day is ENTRY
            mispunch_status = True
            ##Add EXIT CAMERA row of next day to count working hours which includes 12 AM
            if day_start_time_seconds!=0:
                search_tuple[where_clause.index(f'A.intime >= ?')]=end_date
                next_date=get_next_date(end_date,"%Y-%m-%d %H:%M:%S")
                next_date=datetime.strptime(next_date,"%Y-%m-%d")+timedelta(seconds=day_start_time_seconds)
                next_date=str(next_date)
                search_tuple[where_clause.index(f'A.outtime <= ?')]=next_date
            else:
                next_date=get_next_date(end_date)
                search_tuple[where_clause.index(f'A.date >= ?')]=next_date
                search_tuple[where_clause.index(f'A.date <= ?')]=next_date
#             search_tuple[where_clause.index(f'A.Date <= ?')]=next_date
            next_day_res = run_fetch_query(person_db_connection, query=query, values=tuple(search_tuple))
            if len(next_day_res)>0:
                if next_day_res[0][last_seen_location_index]==EXIT_CAMERA_NAME:
                    # rows.append(list(next_day_res[0]))
                    #you should add this data to last seen location and last seen time 
                    #uncomment below lines if you want next day exit to be included in the days result
                    # rows[-1][last_seen_time_index]=next_day_res[0][last_seen_time_index]
                    # rows[-1][last_seen_location_index]=next_day_res[0][last_seen_location_index]
                    #adding mispunch as last log of the day is ENTRY 
                    mispunch_status = True
                    #Removing single log 
                    removed = rows.pop()
                    # pass
                else:
                    removed=rows.pop()
                next_day_res=None
            else:
                removed=rows.pop()
                
     ##CREATING DATAFRAMES
    res1=[tuple(i[k] for k in res1_indices) for i in res]
    res1 = pd.DataFrame(res1, columns=column_names)
    
    res1.insert(0,"DATE",0)
    res1['DATE']=res1['INTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[0])
    res1['INTIME']=res1['INTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[1])
    res1['OUTTIME']=res1['OUTTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[1])
    for key,value in res1_column_insert_dict.items():
        res1.insert(key,value[0],value[1])
        
    if len(rows)<1:
        no_log_status = "Mispunched"
        res3_no_log=[[emp_id,emp_curr_dept_hod,emp_name,emp_curr_shift_name,emp_curr_dept_name,start_date_copy,None,start_date_copy,None,None,None,no_log_status,day_type]]
        if DEBUG:
            print("checkpoint9")
        return res1,pd.DataFrame([]),pd.DataFrame(res3_no_log,columns=res3_names)
        
    res2=[]
    total_time_duration_seconds=0
    for row in rows:
        out_time,in_time=row[column_order.index('A.outtime')],row[column_order.index('A.intime')]
        time_diff=get_time_difference(in_time,out_time,IN_TIME_FORMAT)
        total_time_duration_seconds+=string_to_seconds(time_diff,"%H:%M:%S")
        
        in_date,in_time=get_date_and_time(in_time,IN_TIME_FORMAT)
        out_date,out_time=get_date_and_time(out_time,IN_TIME_FORMAT)
        res2.append([in_date,in_time,out_date,out_time,time_diff])
    
    res2=pd.DataFrame(res2,columns=column_names2)
    for key,value in res2_column_insert_dict.items():
        res2.insert(key,value[0],value[1])
     

    ##################### First in Last out total time ###########################
    first_in_last_out_time_duration_seconds = 0
    if first_in_last_out:
        try:
            # first_in_time = rows[0][column_order.index('A.intime')]
            # last_out_time = rows[-1][column_order.index('A.outtime')]
            first_in_time = res[0][column_order.index('A.intime')]
            last_out_time = res[-1][column_order.index('A.outtime')]
            first_in_last_out_time_duration_seconds = string_to_seconds(get_time_difference(first_in_time, last_out_time, IN_TIME_FORMAT),"%H:%M:%S")
            # print("FILO first_in_last_out_time_duration_seconds: ", first_in_last_out_time_duration_seconds, "hours", first_in_last_out_time_duration_seconds//3600)
        except:
            print("ERROR_FILO")
            pass

    if first_in_last_out and first_in_last_out_time_duration_seconds!=0:
        total_time_duration_seconds = first_in_last_out_time_duration_seconds

   #get daily work status  
    if day_type!="Working Day":
        if total_time_duration_seconds >= OFFDAY_GOODWORKING_MIN_TIME:
            emp_daily_work_status = "Good Working"
        else:
            emp_daily_work_status = day_type
    elif  total_time_duration_seconds<FULL_DAY_LEAVE_LIMIT:
        emp_daily_work_status="Full Day Leave"
    elif total_time_duration_seconds<HALF_DAY_LEAVE_LIMIT:
        emp_daily_work_status="Half Day Leave"
    else:
        if not emp_curr_shift==DYNAMIC_SHIFT_ID:
            # print("error",emp_details, rows[-1][column_order.index('A.outtime')])
            if late_by_seconds>RELAXATION_TIME:
                emp_daily_work_status="Late Comer"
            else:
                if first_in_last_out:
                    leaving_time = string_to_seconds(res[-1][column_order.index('A.outtime')],IN_TIME_FORMAT)
                    # print("leaving_time filo:",leaving_time, res[-1][column_order.index('A.outtime')])
                else:
                    leaving_time = string_to_seconds(rows[-1][column_order.index('A.outtime')],IN_TIME_FORMAT)
                    # print("leaving_time WITHOUT filo:",leaving_time, res[-1][column_order.index('A.outtime')])

                # print("Early leaver RELAXATION_TIME_EXIT in minutes: ",RELAXATION_TIME_EXIT/60, "early leaving_time in minutes: ",(emp_curr_shift_end_time- leaving_time)/60)

                if leaving_time <emp_curr_shift_end_time-RELAXATION_TIME_EXIT:
                    emp_daily_work_status="Early Leaver"
    #mispunched and absent categories are dealt above and present is dealt below.
    
    if first_in_last_out:
        in_time,firstseenlocation,out_time,lastseenlocation=res[0][column_order.index('A.intime')],res[0][column_order.index('A.firstlocation')],res[-1][column_order.index('A.outtime')],res[-1][column_order.index('A.lastseenlocation')]
        in_date,in_time=get_date_and_time(in_time,IN_TIME_FORMAT)
        out_date,out_time=get_date_and_time(out_time,IN_TIME_FORMAT)
        res3=(in_date,in_time,out_date,out_time)
        # print("FILO res3:", res3)

    else:
        res3=list(rows[0])
        res3[column_order.index('A.outtime')]=rows[-1][column_order.index('A.outtime')]
        res3[column_order.index('A.lastseenlocation')]=rows[-1][column_order.index('A.lastseenlocation')]
        in_time,firstseenlocation,out_time,lastseenlocation=res3[column_order.index('A.intime')],res3[column_order.index('A.firstlocation')],res3[column_order.index('A.outtime')],res3[column_order.index('A.lastseenlocation')]
        in_date,in_time=get_date_and_time(in_time,IN_TIME_FORMAT)
        out_date,out_time=get_date_and_time(out_time,IN_TIME_FORMAT)
        res3=(in_date,in_time,out_date,out_time)
    
    
    if day_type=="Working Day" and emp_daily_work_status==None:
        emp_daily_work_status="Present"
    
    if day_type=="Working Day" and mispunch_status==True:
        if not first_in_last_out:
            emp_daily_work_status="Mispunched"
        else:
            if DEBUG:
                print("mispunch_status is not considered")
            pass
    
        
    # total_time_duration=sum([string_to_seconds(i[column_names.index("Time duration")],"%H:%M:%S") for i in rows])
    total_time_duration=str(timedelta(seconds=total_time_duration_seconds))
    if emp_curr_shift==DYNAMIC_SHIFT_ID:
        late_by=str(timedelta(seconds=0))
#     print("lateby: ",late_by)
    # print("res3: ",res3)
    # print("column names3",column_names3)
    # print(emp_daily_work_status, day_type, mispunch_status)
    # if first_in_last_out and first_in_last_out_time_duration_seconds!=0:
    #     total_time_duration=str(timedelta(seconds=first_in_last_out_time_duration_seconds))

    res3=[res3+(late_by,total_time_duration,emp_daily_work_status,day_type)]
    # print("res3: ",res3)
    res3=pd.DataFrame(res3,columns=column_names3)
    
    for key,value in res3_column_insert_dict.items():
        res3.insert(key,value[0],value[1])
    
    if DEBUG:
        print("checkpoint10")
    return res1,res2,res3


def extract_action_tesa_report_data(person_db_connection, user_map, start_date=None, end_date=None,location=None, report_type = ["cam","workhour","daily"], first_in_last_out = False):
    
    # print("dates: ",start_date,end_date,type(start_date))
    emp_id=None
    emp_details=None
    for key,value in user_map.items():
        emp_id=key
        emp_details=value
    
    # print("employee details: ",emp_id)
    emp_name,emp_status,emp_curr_dept,emp_curr_shift,emp_curr_dept_location,emp_details_timestamp=emp_details.name, emp_details.empstatus, emp_details.currdept, emp_details.currshift, emp_details.location, emp_details.depttimestamp
    
    emp_curr_dept_timestamp = emp_details.depttimestamp
    emp_curr_shift_timestamp = emp_details.shifttimestamp
#     print("person shift id2: ",person_shift_id)
    
    if emp_curr_shift==DYNAMIC_SHIFT_ID:
        include_prev_day=True
    else:
        include_prev_day=False
        
    # print("employee details: ",emp_id, emp_curr_shift)
    
    reporting_dates=get_dates_in_between(start_date,end_date)
    # print("reporting dates", reporting_dates)
    
    return_cam, return_workhour, return_daily = False, False, False
    
    if "cam" in report_type:
        return_cam = True
    if "workhour" in report_type:
        return_workhour = True
    if "daily" in report_type:
        return_daily = True
        
    results = []
    results2=[]
    results3=[]
    
    # print('return types',return_cam, return_workhour, return_daily)
    
    res,res2,res3=pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
    # print("reporting dates", reporting_dates)
    for date in reporting_dates:
        # print("date", date)
        res,res2,res3=extract_action_tesa_daily_report_data(person_db_connection, user_map,start_date=date, end_date=date,location=location,include_prev_day=include_prev_day, first_in_last_out = first_in_last_out, get_cam_logs = return_cam)
        # print("includeprev",include_prev_day, len(res3), "\ndf",res3)
        if return_cam and res.shape[0] > 0:
            results.append(res)
        if return_workhour and res2.shape[0] > 0:
            results2.append(res2)
        if return_daily and res3.shape[0] > 0:
            results3.append(res3)
                
    if return_cam and len(results) > 0:
        results = pd.concat(results, axis=0).reset_index(drop=True)
    else:
        results=pd.DataFrame([])
            
    if return_workhour and len(results2) > 0:
        results2 = pd.concat(results2, axis=0).reset_index(drop=True)
    else:
        results2=pd.DataFrame([])
            
    if return_daily and len(results3) > 0:
        results3 = pd.concat(results3, axis=0).reset_index(drop=True)
    else:
        results3=pd.DataFrame([])
        
    return results,results2,results3

        
        

def get_user_rid_map(user_list, user_name):
    
#     print("\n User list: ",user_list,"\nUser name: ",user_name)
    
    user_map = dict()

    empid = user_list[0]
    name = user_name[0]    
    if empid and name:
        name = None
        
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    res_dc = select_from_person_details(person_db_connection, empid = empid, name = name, return_dc = True)
    
    # print("\n5: ",res)
    user_map={i.empid : i for i in res_dc}
#     print("\n6: ",user_map)
    return user_map
    



def generate_action_tesa_report(user_list=None, user_name=None, start_date=None, end_date=None, location=None, report_type = ["cam","workhour","daily"], first_in_last_out = False):

    if user_list is None or not isinstance(user_list, list):
        user_list = [user_list]
    elif isinstance(user_list, np.ndarray):
        user_list = user_list.flatten().tolist()
    
    if user_name is None or not isinstance(user_name, list):
        user_name = [user_name]
    elif isinstance(user_name, np.ndarray):
        user_name = user_name.flatten().tolist()
    
    if len(user_name) != len(user_list): # Should we raise a error here?
        return '', pd.DataFrame([])

    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    
    user_map = {}
    for i,j in zip(user_list, user_name):
        user_map.update(get_user_rid_map([i], [j]))
        
    return_cam, return_workhour, return_daily = False, False, False
    
    if "cam" in report_type:
        return_cam = True
    if "workhour" in report_type:
        return_workhour = True
    if "daily" in report_type:
        return_daily = True
        
    
    # print("umap", user_map)
    results = []
    results2=[]
    results3=[]

#     for ul, un in zip(user_list, user_name):
    for ul,un in user_map.items():
        res,res2,res3 = extract_action_tesa_report_data(person_db_connection,
                                                   user_map={ul:un},
                                                   start_date=start_date,
                                                   end_date=end_date,
                                                   location=None, report_type = report_type, first_in_last_out = first_in_last_out)
        if return_cam and res.shape[0] > 0:
            results.append(res)
        if return_workhour and res2.shape[0] > 0:
            results2.append(res2)
        if return_daily and res3.shape[0] > 0:
            results3.append(res3)
    
    if return_cam and len(results) > 0:
        results = pd.concat(results, axis=0).reset_index(drop=True)
    else:
        results=pd.DataFrame([])
            
    if return_workhour and len(results2) > 0:
        results2 = pd.concat(results2, axis=0).reset_index(drop=True)
    else:
        results2=pd.DataFrame([])
            
    if return_daily and len(results3) > 0:
        results3 = pd.concat(results3, axis=0).reset_index(drop=True)
    else:
        results3=pd.DataFrame([])
        
    #testing     
    # return results.to_string(),results2.to_string(),results3.to_string()
    return results, results2, results3


#     fname_rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k = 64))
#     path = os.path.join(CONFIG['TEMP']['temp_processing_path'], f'{info}report_{fname_rand}.xlsx')

#     banner_suffix=''

#     if start_date:
#         banner_suffix += f'From {start_date}'
    
#     if end_date:
#         if banner_suffix == '':
#             banner_suffix += f'To {end_date}'
#         else:
#             banner_suffix += f' - To {end_date}'
    

    
#     results.fillna(value='', inplace=True)
#     results2.fillna(value='', inplace=True)
#     results3.fillna(value='', inplace=True)
    
    
#     write_reports([results,results2,results3], path, sheet_name=['Camera logs','Working Hours logs','Daily Report'], banner_suffix=banner_suffix)
#     person_db_connection.close()
#     return path, results




def extract_action_tesa_monthly_report(person_db_connection, user_map, month=None,year=None,location=None, first_in_last_out = False):
    if month==None:
        month=datetime.now().month
    if year==None:
        year=datetime.now().year
    
    month_days_list=days_of_month(month=month,year=year)
    start_date,end_date=month_days_list[0],month_days_list[-1]
    # print("start date, end date",start_date, end_date)
    
    res1,res2,res3=extract_action_tesa_report_data(person_db_connection, user_map, start_date=start_date, end_date=end_date,location=location, first_in_last_out = first_in_last_out)
    
    # print("monthly",res1,res2,res3)
    if len(res3)<1:
        print("person:",list(user_map.keys())[0] ,"has no log in this month:", month)
        return res3
    
    headings = res3.columns
    # print("headings",headings)

    entry_no_ind=np.where(headings=="ENTRY NUMBER")[0][0]
    hod_ind = np.where(headings == "HOD")[0][0]
    name_ind=np.where(headings=="NAME")[0][0]
    shift_ind=np.where(headings=="SHIFT")[0][0]
    department_ind = np.where(headings == "DEPARTMENT")[0][0]
    column_indices4=[entry_no_ind, hod_ind, name_ind, shift_ind, department_ind]
    
    # print("column indidces", column_indices4)
    late_by_ind=np.where(headings=="LATE BY")[0][0]
    status_ind = np.where(headings == "STATUS")[0][0]
    entry_date_ind = np.where(headings == "ENTRY DATE")[0][0]
    
    # monthly_status_list = ['' for i in range(len(month_days_list))]
    entry_no_monthly_status_dict = defaultdict(lambda: ['' for i in range(len(month_days_list))])
    day_monthly_status_map = {"Present": "P", "Half Day Leave": "HDL" ,"Full Day Leave" : "FDL", "Full Day Absent" : "A", "Weekly Off" : "WO", "Company Holiday" : "CHO", "Department Holiday" : "DHO", "Good Working" : "GWD", "Late Comer":"LC", "Early Leaver":"EL", "Mispunched": "MP" }
    
    monthly_analysis_map = {"PRESENT": "P", "HALF DAY LEAVE": "HDL" ,"FULL DAY LEAVE" : "FDL", "ABSENT" : "A", "WEEKLY OFF" : "WO", "COMPANY HOLIDAYS" : "CHO", "DEPARTMENT HOLIDAYS" : "DHO", "GOOD WORKING DAYS" : "GWD", "LATE COMER":"LC", "EARLY LEAVER":"EL", "MISPUNCHED": "MP" }
    monthly_analysis_columns = list(monthly_analysis_map.keys())
    entry_no_monthly_analysis_dict =  defaultdict(list)
    keys_list = []
    
    res4_dict=defaultdict(list)
    entry_no_late_by_dict= defaultdict(list)
    prev_dept, prev_shift = -1,-1
    for row in res3.values:
        # try:
        late_by=row[late_by_ind]
        entry_no=row[entry_no_ind]
        # print(row, type(row))
        #TODO NEED SEPARATE ROWS FOR SEPARATE DEPARTMENTS AND SHIFTS hint change key of res4dict to entry no departmnet and shift
        dept = row[department_ind]
        shift = row[shift_ind]
        changed = False
        
        if prev_dept==-1:
            prev_dept = dept
        else:
            if prev_dept!= dept:
                # print("dept", prev_dept, dept)
                prev_dept = dept
                changed = True
        if prev_shift == -1:
            prev_shift = shift
        else:
            if prev_shift!= shift:
                # print("shift", prev_shift, shift)
                prev_shift = shift
                changed = True
                
        key = (entry_no, shift, dept)
        
        if len(keys_list)==0 or changed==True:
            keys_list.append(key)
            
        
        res4_dict[key]=[row[i] for i in column_indices4]
        
        if late_by != None:
            entry_no_late_by_dict[key].append(late_by)

        entry_no_monthly_status_dict[key][month_days_list.index(row[entry_date_ind])] = day_monthly_status_map[row[status_ind]]
        
        # except Exception as e:
        #     print(e, len(res3.values))
        #     print(row)
        #     return
        
    for key, monthly_status in entry_no_monthly_status_dict.items():    
        entry_no_monthly_analysis_dict[key].extend([monthly_status.count(monthly_analysis_map[i]) for i in monthly_analysis_columns])
    
    entry_no_late_penalty_dict={i:0 for i in res4_dict.keys()}

    # daily_late_relaxation_time_limit_in_hours=int(CONFIG["MONTHLY REPORT"]["daily_late_relaxation_time_limit_in_hours"])
    
    for key,values in entry_no_late_by_dict.items():
        late_penalty=0
        total_late_by_seconds=0
        late_days_count=0
        #daily_late_relaxation_time_limit_in_hours
        for late_by in values:
            late_by_seconds=time_to_seconds(datetime.strptime(late_by,"%H:%M:%S").time())
            # if late_by_seconds>(daily_late_relaxation_time_limit_in_hours*3600):
            #     late_penalty+=1
            if late_by_seconds>RELAXATION_TIME:
                total_late_by_seconds+=late_by_seconds
                
        late_days_count = entry_no_monthly_analysis_dict[key][monthly_analysis_columns.index("LATE COMER")]
        ##condition for penalty
        if late_days_count<6:
            if total_late_by_seconds>=int(CONFIG["MONTHLY REPORT"]["relaxation_hours_5_days"])*3600:
                late_penalty=int(CONFIG["MONTHLY REPORT"]["penalty_5_days"])
            late_penalty=int(CONFIG["MONTHLY REPORT"]["penalty_5_days"])
        elif 6<=late_days_count<=10:
            late_penalty=int(CONFIG["MONTHLY REPORT"]["penalty_6_to_10_days"])
        elif 11<=late_days_count<=15:
            late_penalty=int(CONFIG["MONTHLY REPORT"]["penalty_11_to_15_days"])
        elif 16<=late_days_count<=20:
            late_penalty=int(CONFIG["MONTHLY REPORT"]["penalty_16_to_20_days"])
        elif 21<=late_days_count<=25:
            late_penalty=int(CONFIG["MONTHLY REPORT"]["penalty_21_to_25_days"])
        elif 26<=late_days_count:
            late_penalty=int(CONFIG["MONTHLY REPORT"]["penalty_26_to_end"])
            
        entry_no_late_penalty_dict[key] = late_penalty
        
    for key in res4_dict.keys():
        res4_dict[key].extend(entry_no_monthly_status_dict[key])
        res4_dict[key].extend(entry_no_monthly_analysis_dict[key])
        res4_dict[key].append(entry_no_late_penalty_dict[key])
        
    column_names4=[headings[i] for i in column_indices4]+[i for i in range(1,len(month_days_list)+1)]+monthly_analysis_columns+["LATE PENALTY"]
    
    
    # print("keys list", len(keys_list), keys_list)
    res4 = None
    try:
        res4=pd.DataFrame(list(res4_dict[i] for i in keys_list),columns=column_names4)
    except:
        print(list(res4_dict[i] for i in keys_list), "\n", entry_no_monthly_status_dict,"\n", entry_no_monthly_analysis_dict, "\n", entry_no_late_by_dict, "\n", entry_no_late_penalty_dict )
    # res4.insert(0,"Reporting Month",str(month)+'-'+str(year))
    # print(list(res4_dict.values()))
    
    return res4

def generate_action_tesa_monthly_report(user_list=None, user_name=None, month=None,year=None, location=None, first_in_last_out = False):

    if user_list is None or not isinstance(user_list, list):
        user_list = [user_list]
    elif isinstance(user_list, np.ndarray):
        user_list = user_list.flatten().tolist()
    
    if user_name is None or not isinstance(user_name, list):
        user_name = [user_name]
    elif isinstance(user_name, np.ndarray):
        user_name = user_name.flatten().tolist()
    
    if len(user_name) != len(user_list): # Should we raise a error here?
        return '', pd.DataFrame([])

    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    
    user_map = {}
    for i,j in zip(user_list, user_name):
        user_map.update(get_user_rid_map([i], [j]))
    
    # print("umap", user_map)
    results = []

#     for ul, un in zip(user_list, user_name):
    for ul,un in user_map.items():
        res = None
        # try:
        res = extract_action_tesa_monthly_report(person_db_connection, {ul:un}, month = month ,year = year,location = location,first_in_last_out = first_in_last_out)
        # except Exception as e:
        #     print(e)
        #     print('ul un', ul, un)
        
        if res.shape[0] > 0:
            results.append(res)

    if len(results) > 0:
        results = pd.concat(results, axis=0).reset_index(drop=True)
    else:
        results=pd.DataFrame([])

    return results
    

    
    

        
if __name__=="__main__":
    print(get_user_rid_map(["1"],["1"]))

                        
                        
                        
                        
                        
                        
                        