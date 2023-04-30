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


from .action_tesa_report_utils import get_time_difference,get_dates_in_between,get_next_date,get_prev_date,string_to_time,string_to_seconds,days_of_month,get_department,get_shift,get_date_and_time,get_compay_holiday_list,get_department_holiday_list#time_to_seconds

from .dbcontainers import Auth_Login_Container, Auth_User_Container, Face_Identity_Container,\
                          Face_Vector_Container,Person_Alerts_container, Person_Attendance_Log_container, Person_Department_Container,\
                          Person_Holiday_Container, Person_Location_Container, Person_Person_Details_Container,\
                          Person_Roster_Container, Warehouse_Olddeptchange_Container, Warehouse_Oldempdept_Container,\
                          Warehouse_Oldempshifts_Container, DB_Container, base_dataclass

from .global_vars import Warehouse_Oldempdept,Warehouse_Oldempdept_Fields,Warehouse_Oldempshifts,Warehouse_Oldempshifts_Fields,Person_Roster,Person_Roster_Fields,Person_Person_Details,Person_Person_Details_Fields,Person_Location,Person_Location_Fields,Person_Holiday,Person_Holiday_Fields,Person_Department,Person_Department_Fields,Person_Attendance_Log,Person_Attendance_Log_Fields

ENTRY_CAMERA_NAME=CONFIG["IPCAMERA_1"]["camera_name"]
EXIT_CAMERA_NAME=CONFIG["IPCAMERA_2"]["camera_name"]
IN_TIME_FORMAT="%Y-%m-%d %H:%M:%S.%f"
# static_in_time_string='09:00:00.000000'
# static_in_time=datetime.strptime(static_in_time_string,"%H:%M:%S.%f")
# shift_intime_dict={}
RELAXATION_TIME=int(CONFIG["DAILY_REPORT"]["daily_late_relaxation_time_in_minutes"])*60
RELAXATION_TIME_EXIT=int(CONFIG["DAILY_REPORT"]["daily_late_relaxation_time_in_minutes"])*60

FULL_DAY_LEAVE_LIMIT=int(CONFIG["DAILY_REPORT"]["min_working_hours_for_not_full_day_leave"])*3600

HALF_DAY_LEAVE_LIMIT=int(CONFIG["DAILY_REPORT"]["min_working_hours_for_not_half_day_leave"])*3600


GAP_TIME_HOURS=int(CONFIG["DAILY_REPORT"]["gap_time_between_shift_for_dynamic_shift_in_hours"])

# print("checking daily report: ,",RELAXATION_TIME,GAP_TIME_HOURS)
GAP_TIME_FOR_DYNAMIC=timedelta(seconds=GAP_TIME_HOURS*3600)
DYNAMIC_SHIFT_NAME="Dynamic"
DYNAMIC_SHIFT_ID="D"

EMPLOYEE_TIME_STAMP_FORMAT="%Y-%m-%d %H:%M:%S.%f"


WEEKDAYS = ["Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"]


def extract_action_tesa_daily_report_data(person_db_connection, user_map, start_date=None, end_date=None,location=None,day_start_time="00:00:01",include_prev_day=False):
    
#     print("nclude_prev_day: ",include_prev_day)
    
    emp_id=None
    emp_details=None
    for key,value in user_map.items():
        emp_id=key
        emp_details=value
    
    print("employee details: ",emp_id,emp_details)
    emp_name,emp_status,emp_curr_dept,emp_curr_shift,emp_curr_dept_location,emp_details_timestamp=emp_details
    
    
    
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
    if emp_status=="N":
        print("Person: ",emp_name,"is currently not an employee")
        return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
    
    #checking timestamp of employee to get current shift and department details
    # if not datetime.strptime(start_date,"%Y-%m-%d")>=datetime.strptime(emp_details_timestamp,EMPLOYEE_TIME_STAMP_FORMAT):
    
    if True:
        
        # print("Date chosen is not in current timestamp")
        shift_details=get_shift(emp_id,emp_curr_shift,start_date,"%Y-%m-%d")
        
        if isinstance(shift_details,int):
            print("Date chosen is before starttimne")
            return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
        emp_curr_shift,emp_curr_shift_name,emp_curr_shift_startime,emp_curr_shift_end_time,emp_weekly_off_day=shift_details
        
        department_details=get_department(emp_id,emp_curr_dept,emp_curr_dept_location,start_date,"%Y-%m-%d")
        if isinstance(department_details,int):
            print("Date chosen is before starttimne")
            return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
        emp_curr_dept,emp_curr_dept_name,emp_curr_dept_location,emp_curr_dept_hod=department_details
        
        print("shift details",shift_details)
        print("employee details",department_details)
    
    # start_date_datetime=datetime.strptime(start_date,"%Y-%m-%d")
    
    
    
    start_date_copy=start_date
    end_date_copy=end_date
    
    day_start_time_seconds=string_to_seconds(day_start_time,"%H:%M:%S")
    if day_start_time_seconds!=0:
        end_date=get_next_date(end_date,"%Y-%m-%d")
#     print("User map: ",user_map)
    
    table1 = Person_Attendance_Log_Fields.tablename
    table2 = Person_Person_Details_Fields.tablename
    table3 = Person_Roster_Fields.tablename
    table4= Person_Department_Fields.tablename
    
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
        prev_day_res=extract_action_tesa_daily_report_data(person_db_connection, user_map, start_date=get_prev_date(start_date_copy,"%Y-%m-%d"), end_date=get_prev_date(end_date_copy,"%Y-%m-%d"),location=location,day_start_time=day_start_time,include_prev_day=False)
        prev_day_res3=prev_day_res[-1]
#         print("prev day results:",prev_day_res3)
        if len(prev_day_res3)>0:
            date,time=prev_day_res3.iloc[0]['EXIT DATE'],prev_day_res3.iloc[0]['EXIT TIME']
            prev_last_seen_time=date+" "+time
            print("previous last seen time:", prev_last_seen_time)

    

    if start_date:
        if day_start_time_seconds!=0:
            where_clause.append('A.intime >= ?')
            start_date=datetime.strptime(start_date,"%Y-%m-%d")
            start_date=start_date+timedelta(seconds=day_start_time_seconds)
            if prev_last_seen_time!=None:
                prev_last_seen_time=datetime.strptime(prev_last_seen_time,"%Y-%m-%d %H:%M:%S")
#                 prev_day_gap=start_date-prev_last_seen_time
#                 print("prev_day_gap: ",prev_day_gap)
#                 prev_day_end=prev_last_seen_time+prev_day_gap
                if prev_last_seen_time>start_date:
                    start_date=prev_last_seen_time+timedelta(seconds=1)
                    print("\n\n\n\nstart date changed: ",start_date)
                else:
                    print("\n\n\n\nno change in start date: ",start_date)
                
            start_date=str(start_date)
#             print("start date with time: ",start_date)
        else:
            where_clause.append(f'A.date >= ?')
        search_tuple.append(start_date)
        
    if end_date:
        if day_start_time_seconds!=0:
            where_clause.append(f'A.outtime <= ?')
            end_date=datetime.strptime(end_date,"%Y-%m-%d")
            end_date=end_date+timedelta(seconds=day_start_time_seconds)
            end_date=str(end_date)
#             print("end date with time: ",end_date)
        else:
            where_clause.append(f'A.date <= ?')
        search_tuple.append(end_date)
        
    where_clause.append(f'A.empid = ?')
    search_tuple.append(emp_id)

    where_clause_string = ' AND '.join(where_clause)
    query = ' '.join(partial_query + ['WHERE', where_clause_string])
        
#     print("\n,query : ",query)
#     print("\n values: ",search_tuple)
    res = run_fetch_query(person_db_connection, query=query, values=tuple(search_tuple))
    
    print("results of query:",res)
    
#     print("res length: ",len(res))
#     print("cam names:",ENTRY_CAMERA_NAME,EXIT_CAMERA_NAME,type(ENTRY_CAMERA_NAME))

    #get day type
    start_date_datetime=datetime.strptime(start_date_copy,"%Y-%m-%d")
    company_holiday_list=get_compay_holiday_list(start_date_datetime.year)
    department_holiday_list=get_department_holiday_list(start_date_datetime.year)
    
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
        no_log_status=None
        
    res3_no_log=[[emp_id,emp_curr_dept_hod,emp_name,emp_curr_shift_name,emp_curr_dept_name,start_date_copy,None,start_date_copy,None,None,None,no_log_status,day_type]]
        
    
    if len(res)<1:
        # print("error",len(res3_no_log),len(res3_names))
        print(pd.DataFrame(res3_no_log,columns=res3_names))
        return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame(res3_no_log,columns=res3_names)
    
#     print("\nresult1: ",res[0])
    if len(res)==1:
        res1 = pd.DataFrame([tuple(res[0][i] for i in res1_indices)], columns=column_names)
        res1.insert(0,"DATE",0)
        res1['DATE']=res1['INTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[0])
        res1['INTIME']=res1['INTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[1])
        res1['OUTTIME']=res1['OUTTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[1])
        for key,value in res1_column_insert_dict.items():
            res1.insert(key,value[0],value[1])
        res2=res3=pd.DataFrame([])
        
        #should consider previous day results
        #if prev last seen time and in time diff is less than gap time, it is full day absent, else:mispunched
        # res3_mispunched=[emp_id,emp_curr_dept_hod,emp_name,emp_curr_shift_name,emp_curr_dept_name,start_date_copy,res1['INTIME'],start_date_copy,res1['OUTTIME'],None,None,,day_type]
        
        return res1,res2,res3
        
    rows=[]
    last_seen_location=None
    last_seen_time=None
     
    ##Getting first row of the day
    last_seen_location_index=column_order.index('A.lastseenlocation')
    last_seen_time_index=column_order.index('A.outtime')
    in_time=None 

    late_by_seconds=0
    late_by=str(timedelta(seconds=0))
    k=None
    for i in range(len(res)):
        if res[i][last_seen_location_index]==ENTRY_CAMERA_NAME:
            k=i
            rows.append(list(res[i]))
            in_time=res[i][last_seen_time_index]
            in_time=string_to_seconds(in_time,IN_TIME_FORMAT)
            late_by_seconds=in_time-emp_curr_shift_startime#in shift startime in seconds
            if late_by_seconds>0:##late penalty
                late_by=str(timedelta(seconds=late_by_seconds))##string  H:M:S format
            break
            
    if k==None:
        return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
    if k==len(res)-1:            
        res1 = pd.DataFrame([tuple(res[-1][i] for i in res1_indices)], columns=column_names)
        res1.insert(0,"DATE",0)
        res1['DATE']=res1['INTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[0])
        res1['INTIME']=res1['INTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[1])
        res1['OUTTIME']=res1['OUTTIME'].apply(lambda x: get_date_and_time(x,IN_TIME_FORMAT)[1])
        for key,value in res1_column_insert_dict.items():
            res1.insert(key,value[0],value[1])
        res2=res3=pd.DataFrame([])
        
        return res1,res2,res3
        
    for i in range(k+1,len(res)):
        time,location=res[i][last_seen_time_index],res[i][last_seen_location_index]
        if location!=last_seen_location:
            if location==EXIT_CAMERA_NAME:
                rows[-1][last_seen_time_index],rows[-1][last_seen_location_index]=time,location
            elif location==ENTRY_CAMERA_NAME:
                rows.append(list(res[i]))
            last_seen_location=location
            
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
#         print("next day queries and values: ",query,"\n",search_tuple)
        
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
                            next_day_rows[-1][last_seen_time_index]=next_day_res[i][last_seen_time_index]
                        elif location==ENTRY_CAMERA_NAME:
                            gap_end_time=time
                            next_day_rows[-1][last_seen_time_index]=next_day_res[i][last_seen_time_index]
                            
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
                            next_day_rows[-1][last_seen_time_index]=next_day_res[i][last_seen_time_index]
                        elif location==ENTRY_CAMERA_NAME:
                            gap_end_time=time
                            next_day_rows[-1][last_seen_time_index]=next_day_res[i][last_seen_time_index]
#             print("next day rows2: ",next_day_rows)
            rows.extend(next_day_rows)
    else:
#         print("going 3")
        if last_seen_location==ENTRY_CAMERA_NAME:
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
                    #you should add this data to last seen location and last seen time 
                    # rows.append(list(next_day_res[0]))
                    rows[-1][last_seen_time_index]=next_day_res[0][last_seen_time_index]
                    rows[-1][last_seen_location_index]=next_day_res[0][last_seen_location_index]
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
        return res1,pd.DataFrame([]),pd.DataFrame([]) 
        
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
        
        
        
   #get daily work status  
    if day_type!="Working Day":
        emp_daily_work_status="Good Working"
    elif  total_time_duration_seconds<FULL_DAY_LEAVE_LIMIT:
        emp_daily_work_status="Full Day Leave"
    elif total_time_duration_seconds<HALF_DAY_LEAVE_LIMIT:
        emp_daily_work_status="Half Day Leave"
    else:
        if not emp_curr_shift==DYNAMIC_SHIFT_ID:
            if late_by_seconds>RELAXATION_TIME:
                emp_daily_work_status="Late Comer"
            elif string_to_seconds(rows[-1][column_order.index('A.outtime')],"%H:%M:%S")<emp_curr_shift_end_time-RELAXATION_TIME_EXIT:
                emp_daily_work_status="Early Leaver"
    #mispunched and absent categories are dealt above and present is dealt below.
    

    res3=list(rows[0])
    res3[column_order.index('A.outtime')]=rows[-1][column_order.index('A.outtime')]
    res3[column_order.index('A.lastseenlocation')]=rows[-1][column_order.index('A.lastseenlocation')]
    in_time,firstseenlocation,out_time,lastseenlocation=res3[column_order.index('A.intime')],res3[column_order.index('A.firstlocation')],res3[column_order.index('A.outtime')],res3[column_order.index('A.lastseenlocation')]
    in_date,in_time=get_date_and_time(in_time,IN_TIME_FORMAT)
    out_date,out_time=get_date_and_time(out_time,IN_TIME_FORMAT)
    res3=(in_date,in_time,out_date,out_time)
    # if day_type!="Working Day":
    #     if mispunch_status==True:
    #         emp_daily_work_status="Mispunched"
    
    
    if day_type==None:
        emp_daily_work_status="Present"
        
    # total_time_duration=sum([string_to_seconds(i[column_names.index("Time duration")],"%H:%M:%S") for i in rows])
    total_time_duration=str(timedelta(seconds=total_time_duration_seconds))
    if emp_curr_shift==DYNAMIC_SHIFT_ID:
        late_by=str(timedelta(seconds=0))
#     print("lateby: ",late_by)
    # print("res3: ",res3)
    # print("column names3",column_names3)
    res3=[res3+(late_by,total_time_duration,emp_daily_work_status,day_type)]
    # print("res3: ",res3)
    res3=pd.DataFrame(res3,columns=column_names3)
    
    for key,value in res3_column_insert_dict.items():
        res3.insert(key,value[0],value[1])
    
    return res1,res2,res3


def extract_action_tesa_report_data(person_db_connection, user_map, start_date=None, end_date=None,location=None):
    
#     print("dates: ",start_date,end_date,type(start_date))
    emp_id=None
    emp_details=None
    for key,value in user_map.items():
        emp_id=key
        emp_details=value
    
    # print("employee details: ",emp_details)
    emp_name,emp_status,emp_curr_dept,emp_curr_shift,emp_curr_dept_location,emp_details_timestamp=emp_details 
#     print("person shift id2: ",person_shift_id)
    
    if emp_curr_shift==DYNAMIC_SHIFT_ID:
        include_prev_day=True
    else:
        include_prev_day=False
    
    reporting_dates=get_dates_in_between(start_date,end_date)

    results = []
    results2=[]
    results3=[]
    
    res,res2,res3=pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
    for date in reporting_dates:
        res,res2,res3=extract_action_tesa_daily_report_data(person_db_connection, user_map,start_date=date, end_date=date,location=location,include_prev_day=include_prev_day)
        if res.shape[0] > 0:
            results.append(res)
        if res2.shape[0] > 0:
            results2.append(res2)
        if res3.shape[0] > 0:
            results3.append(res3)

    if len(results) > 0:
        results = pd.concat(results, axis=0).reset_index(drop=True)
    else:
        results=pd.DataFrame([])
        
    if len(results2) > 0:
        results2 = pd.concat(results2, axis=0).reset_index(drop=True)
    else:
        results2=pd.DataFrame([])
        
    if len(results3) > 0:
        results3 = pd.concat(results3, axis=0).reset_index(drop=True)
    else:
        results3=pd.DataFrame([])
        
        
    return results,results2,results3

        
        

def get_user_rid_map(user_list, user_name):
    
#     print("\n User list: ",user_list,"\nUser name: ",user_name)
    
    user_map = dict()

    partial_query = f'SELECT {Person_Person_Details_Fields.empid}, {Person_Person_Details_Fields.name},{Person_Person_Details_Fields.empstatus},{Person_Person_Details_Fields.currdept},{Person_Person_Details_Fields.currshift},{Person_Person_Details_Fields.location},{Person_Person_Details_Fields.timestamp} FROM {Person_Person_Details_Fields.tablename}'

    if len(user_list) == 1 and user_list[0] is None and user_name[0] is None:
        
        query = partial_query
        clause = ()

    elif len(user_list) == 1 and user_list[0] is None and user_name[0] is not None:

        query = f'{partial_query} WHERE {Person_Person_Details_Fields.name} = ?'
        clause = (user_name[0],)
    
    elif len(user_list) == 1 and user_list[0] is not None and user_name[0] is None:

        query = f'{partial_query} WHERE {Person_Person_Details_Fields.empid} = ?'
        clause = (user_list[0], )
    
    elif len(user_list) == 1 and user_list[0] is not None and user_name[0] is not None:

        query = f'{partial_query} WHERE {Person_Person_Details_Fields.empid} = ?'
        clause = (user_list[0], )

#     elif len(user_list) > 1:
#         clause = ()#tuple(user_list)
#         query = f'{partial_query} WHERE {Person_Person_Details_Fields.empid} IN {tuple(user_list)}'
    
#     elif len(user_name)>1:
#         query = f'{partial_query} WHERE {Person_Person_Details_Fields.name} IN {tuple(user_name)}'
#         clause = ()
        
    # print("1: ",user_list,"\n2: ",user_name,"\n3: ",clause,"\n4: ",query)    
        
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    res=run_fetch_query(person_db_connection,query,clause)
    
    # print("\n5: ",res)
    user_map={i[0]:i[1:] for i in res}
#     print("\n6: ",user_map)
    return user_map
    



def generate_action_tesa_report(user_list=None, user_name=None, start_date=None, end_date=None, location=None, info=''):

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

    user_map = get_user_rid_map(user_list, user_name)

    results = []
    results2=[]
    results3=[]

#     for ul, un in zip(user_list, user_name):
    for ul,un in user_map.items():
        res,res2,res3 = extract_action_tesa_report_data(person_db_connection,
                                                   user_map={ul:un},
                                                   start_date=start_date,
                                                   end_date=end_date,
                                                   location=None)
        
        if res.shape[0] > 0:
            results.append(res)
        if res2.shape[0] > 0:
            results2.append(res2)
        if res3.shape[0] > 0:
            results3.append(res3)

    if len(results) > 0:
        results = pd.concat(results, axis=0).reset_index(drop=True)
    else:
        results=pd.DataFrame([])
        
    if len(results2) > 0:
        results2 = pd.concat(results2, axis=0).reset_index(drop=True)
    else:
        results2=pd.DataFrame([])
        
    if len(results3) > 0:
        results3 = pd.concat(results3, axis=0).reset_index(drop=True)
    else:
        results3=pd.DataFrame([])
        
    #testing     
    return results.to_string(),results2.to_string(),results3.to_string()


    fname_rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k = 64))
    path = os.path.join(CONFIG['TEMP']['temp_processing_path'], f'{info}report_{fname_rand}.xlsx')

    banner_suffix=''

    if start_date:
        banner_suffix += f'From {start_date}'
    
    if end_date:
        if banner_suffix == '':
            banner_suffix += f'To {end_date}'
        else:
            banner_suffix += f' - To {end_date}'
    

    
    results.fillna(value='', inplace=True)
    results2.fillna(value='', inplace=True)
    results3.fillna(value='', inplace=True)
    
    
    write_reports([results,results2,results3], path, sheet_name=['Camera logs','Working Hours logs','Daily Report'], banner_suffix=banner_suffix)
    person_db_connection.close()
    return path, results




def extract_action_tesa_monthly_report(person_db_connection, user_map, month=None,year=None,location=None):
    if month==None:
        month=datetime.now().month
    if year==None:
        year=datetime.now().year
    
    month_days_list=days_of_month(month=month,year=year)
    start_date,end_date=month_days_list[0],month_days_list[-1]
    
    res1,res2,res3=extract_action_tesa_report_data(person_db_connection, user_map, start_date=start_date, end_date=end_date,location=location)
    
    headings = res3.columns
    late_by_ind=np.where(headings=="Late_by")[0]
    entry_no_ind=np.where(headings=="entry_no")[0]
    name_ind=np.where(headings=="name")[0]
    threat_ind=np.where(headings=="threat")[0]
    shift_ind=np.where(headings=="shift")[0]
    shift_start_time_ind=np.where(headings=="Shift_starttime")[0]
    
    column_indices4=[entry_no_ind,name_ind,threat_ind,shift_ind,shift_start_time_ind]
    res4_dict={}
    
    entry_no_late_by_dict={}
    for row in res3.values:
        late_by=row[late_by_ind][0]##str-"%H:%M:%S"
        entry_no=row[entry_no_ind][0]#int
        if not entry_no_late_by_dict.get(entry_no):
            entry_no_late_by_dict[entry_no]=[]
        if not res4_dict.get(entry_no):
            res4_dict[entry_no]=[row[i[0]] for i in columns_indices4]
        entry_no_late_by_dict[entry_no].append(late_by)
        
    
    entry_no_late_penalty_dict={i:"" for i in entry_no_late_by_dict.keys()}
    
    
    daily_late_relaxation_time_limit_in_hours=int(CONFIG["MONTHLY REPORT"]["daily_late_relaxation_time_limit_in_hours"])
    for entry_no,values in entry_no_late_by_dict.items():
        late_penalty=0
        total_late_by_seconds=0
        late_days_count=0
        
        #daily_late_relaxation_time_limit_in_hours
        
        for late_by in values:
            late_by_seconds=time_to_seconds(datetime.strptime(late_by,"%H:%M:%S").time())
            if late_by_seconds>(daily_late_relaxation_time_limit_in_hours*3600):
                late_penalty+=1
            elif late_by_seconds>RELAXATION_TIME:
                late_days_count+=1
                total_late_by_seconds+=late_by_seconds
        ##condition for penalty
        if late_days_count<6:
#             if total_late_by_seconds>=int(CONFIG["MONTHLY REPORT"]["relaxation_hours_5_days"])*3600:
#                 late_penalty=int(CONFIG["MONTHLY REPORT"]["penalty_5_days"])
            late_penalty=int(CONFIG["MONTHLY REPORT"]["penalty_5_days"])
        elif 6<=late_days_count<=10:
            late_penalty=int(CONFIG["MONTHLY REPORT"]["penalty_6_to_10_days"])
        elif 11<=late_days_count<=15:
            late_penalty=int(CONFIG["MONTHLY REPORT"]["penalty_11_to_15_days"])
        elif 16<=late_days_count<=20:
            late_penalty=int(CONFIG["MONTHLY REPORT"]["penalty_16_to_20_days"])
        elif 21<=late_days_count<=25:
            late_penalty=int(CONFIG["MONTHLY REPORT"]["penalty_21_to_25_days"])
        elif 26<=late_days_count<=30:
            late_penalty=int(CONFIG["MONTHLY REPORT"]["penalty_26_to_30_days"])
        
        res4_dict.append(late_penalty)
        
    column_names4=[headings[i][0] for i in columns_indices4]+["Late Penalty"]
    
    res4=pd.DataFrame(list(res4_dict.values()),columns=column_names4)
    res4.insert(0,"Reporting Month",str(month)+'-'+str(year)) 
    
    return res3,res4
    

def write_reports(reports, path, sheet_name=None, banner_suffix=''):
    #report.to_excel(path)

#     if sheet_name is None:
#         sheet_name = os.path.splitext(os.path.basename(path))[0]
    
    
    workbook = xlsxwriter.Workbook(path)
    
    worksheets=[]
    if sheet_name is None:
        sheet_name = os.path.splitext(os.path.basename(path))[0]
    elif isinstance(sheet_name,list):
        for i in range(len(reports)):
            worksheet = workbook.add_worksheet(sheet_name[i])
            worksheets.append(worksheet)
    else:
        for i in range(len(reports)):
            worksheet = workbook.add_worksheet(sheet_name+"_"+str(i))
            worksheets.append(worksheet)
    
        

    label_format = workbook.add_format({'bold': True, 'bg_color': 'yellow','align':'center','border_color':'black','border':1})
    entry_format = workbook.add_format({'indent':1,'align':'center','num_format':'General'})
    number_entry_format = workbook.add_format({'indent':1,'align':'center','num_format':'dd/mm/yy hh:mm AM/PM'})
    entry_format_warning = workbook.add_format({'indent':1,'align':'center','num_format':'General', 'bg_color': 'red', 'font_color': 'white'})
    number_entry_format_warning = workbook.add_format({'indent':1,'align':'center','num_format':'General', 'bg_color': 'red', 'font_color': 'white'})
    
    entry_format_late=workbook.add_format({'indent':1,'align':'center','num_format':'General', 'bg_color': 'orange', 'font_color': 'white'})
    number_entry_format_late= workbook.add_format({'indent':1,'align':'center','num_format':'General', 'bg_color': 'orange', 'font_color': 'white'})
    
    for i in range(len(reports)):
        worksheet=worksheets[i]
        worksheet.set_column(0, 12, 30)

        worksheet.insert_image('D1', CONFIG['REPORT']['report_logo'], {'x_offset': -105, 'y_offset': 0})

    banner = CONFIG['REPORT']['report_banner']
    if banner_suffix != '':
        banner = f'{banner} {banner_suffix}'
        
    for i in range(len(reports)):
        worksheet=worksheets[i]
        worksheet.write('C4', banner)

    for i in range(len(reports)):
        worksheet=worksheets[i] 
        report=reports[i]
        if len(report)==0:
            continue
        
        headings_row = 5
        headings_col = 0
        headings = report.columns
        threat_ind = np.where(headings == 'threat')[0]
        if "Time" in headings:
            in_time_ind=np.where(headings == 'Time')[0]
        elif 'InTime' in headings:
            in_time_ind=np.where(headings == 'InTime')[0]
            
        if "Late_by" in headings:
            late_by_ind=np.where(headings=="Late_by")[0]
            
        shift_ind=np.where(headings=="shift")[0]
            
        for name in headings:
            worksheet.write(headings_row, headings_col, name, label_format)
            headings_col += 1
        entry_row = 6
        

        
    
        data = report.values
        for row in data:
            if row[threat_ind] == 'y':
                nb_format = number_entry_format_warning
                ef = entry_format_warning
            else:
                if row[shift_ind]=="D":
                    nb_format = number_entry_format
                    ef = entry_format
                elif "Late_by" in headings:
                    late_by_seconds=time_to_seconds(datetime.strptime(row[late_by_ind][0],"%H:%M:%S").time())
#                     print("late by seconds: ",late_by_seconds,row[late_by_ind])
                    if late_by_seconds>RELAXATION_TIME:
                        nb_format = number_entry_format_late
                        ef = entry_format_late
                    else:
                        nb_format = number_entry_format
                        ef = entry_format
                else:
                    nb_format = number_entry_format
                    ef = entry_format 
                        
                        

            entry_col = 0
            for index, i in enumerate(row):
#                 if(index in [3, 4]):
#                     worksheet.write(entry_row, entry_col, i, nb_format)
#                 else:
                    
                worksheet.write(entry_row, entry_col, i, ef)
                entry_col+=1
            entry_row += 1
    workbook.close()
    
    

        
if __name__=="__main__":
    print(get_user_rid_map(["1"],["1"]))

                        
                        
                        
                        
                        
                        
                        