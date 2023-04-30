import pandas as pd
import numpy as np
from .dbutils import create_connection
from .load_config import CONFIG
from .dbutils import run_fetch_query, run_query_noreturn
from .global_vars import PEOPLE_TABLE_FIELDS, PEOPLE_TABLE, ROSTER_TABLE_FIELDS,  \
                         ROSTER_TABLE, ONLINE_LOG_TABLE_FIELDS, ONLINE_LOG_TABLE
import random, string, os
from .report import write_report

from datetime import datetime,timedelta,date
from calendar import monthrange
import xlsxwriter


from .action_tesa_report_utils import get_time_difference,get_dates_in_between,get_next_date,get_prev_date,string_to_time,string_to_seconds,days_of_month,#time_to_seconds

ENTRY_CAMERA_NAME=CONFIG["IPCAMERA_1"]["camera_name"]
EXIT_CAMERA_NAME=CONFIG["IPCAMERA_2"]["camera_name"]
IN_TIME_FORMAT="%Y-%m-%d %H:%M:%S.%f"
# static_in_time_string='09:00:00.000000'
# static_in_time=datetime.strptime(static_in_time_string,"%H:%M:%S.%f")
# shift_intime_dict={}
RELAXATION_TIME=int(CONFIG["DAILY_REPORT"]["daily_late_relaxation_time_in_minutes"])*60


GAP_TIME_HOURS=int(CONFIG["DAILY_REPORT"]["gap_time_between_shift_for_dynamic_shift_in_hours"])

# print("checking daily report: ,",RELAXATION_TIME,GAP_TIME_HOURS)
GAP_TIME_FOR_DYNAMIC=timedelta(seconds=GAP_TIME_HOURS*3600)
DYNAMIC_SHIFT_NAME="Dynamic"
DYNAMIC_SHIFT_ID="D"

def extract_action_tesa_daily_report_data(person_db_connection, user_map, start_date=None, end_date=None,location=None,day_start_time="00:00:01",include_prev_day=False):
    
#     print("nclude_prev_day: ",include_prev_day)
    
    person_ids=[]
    roster_ids=[]
    for person_id,roster_id in user_map.items():
        person_ids.append(person_id)
        roster_ids.append(roster_id)  
    person_shift_id=None
    if len(roster_ids)==1:
        person_shift_id=roster_ids[0]    
#     print("person shift id: ",person_shift_id)
    
    start_date_copy=start_date
    end_date_copy=end_date
    
    day_start_time_seconds=string_to_seconds(day_start_time,"%H:%M:%S")
    if day_start_time_seconds!=0:
        end_date=get_next_date(end_date,"%Y-%m-%d")
#     print("User map: ",user_map)
    table2 = PEOPLE_TABLE_FIELDS.table_name


    table1 = ONLINE_LOG_TABLE_FIELDS.table_name
    
    table3= ROSTER_TABLE_FIELDS.table_name
    
    column_order = ['A.entry_no', 'B.name', 'B.threat','C.name','C.starttime','A.InTime', 'A.OutTime', 'A.FirstLocation', 'A.LastSeenLocation']
    column_names = ['.'.join(v.split('.')[1:]) for v in column_order]
    column_names[column_order.index('C.starttime')]="Shift_starttime"
    column_names[column_order.index("C.name")]="shift"
    column_names.append("Time duration")

    column_order2 = ['A.entry_no', 'B.name', 'B.threat','C.name','C.starttime','A.InTime','A.FirstLocation']
    column_names2 = ['.'.join(v.split('.')[1:]) for v in column_order2]
    column_names2[column_order2.index("A.FirstLocation")]="Location"
    column_names2[column_order2.index("A.InTime")]="Time"
    column_names2[column_order2.index("C.starttime")]="Shift_starttime"
    column_names2[column_order2.index("C.name")]="shift"
    
    column_names3=column_names[:-1]+["Late_by","Total Time"]
    
    partial_query = [
        'SELECT',
        ', '.join(column_order),
        'FROM', table1, 'AS A',
        'INNER JOIN', table2, 'AS B',
        'ON A.entry_no = B.entry_no',
        'INNER JOIN', table3, 'AS C',
        'ON C.rid = B.shift'
    ]

    where_clause = []
    search_tuple = []
    
    prev_last_seen_time=None
    if include_prev_day==True:
        prev_day_res=extract_action_tesa_daily_report_data(person_db_connection, user_map, start_date=get_prev_date(start_date_copy,"%Y-%m-%d"), end_date=get_prev_date(end_date_copy,"%Y-%m-%d"),location=location,day_start_time=day_start_time,include_prev_day=False)
        prev_day_res3=prev_day_res[-1]
#         print("prev day results:",prev_day_res3)
        if len(prev_day_res3)>0:
#             print("prev day time:","\n",type(prev_day_res3))
            prev_last_seen_time=prev_day_res3.iloc[0][column_names3[column_order.index('A.OutTime')]]
#             print("prev day time: ",prev_last_seen_time,type(prev_last_seen_time))
#             print("string to time:",string_to_time(prev_last_seen_time,IN_TIME_FORMAT))
#             print("string to seconds:",string_to_seconds(prev_last_seen_time,IN_TIME_FORMAT))
#             prev_last_seen_seconds=string_to_seconds(prev_last_seen_time,IN_TIME_FORMAT)
#             if prev_last_seen_seconds>day_start_time_seconds:
#                 day_start_time_seconds_in=prev_last_seen_seconds
#                 print("more: ",day_start_time_seconds_in)
#             else:
#                 print("less: ",prev_last_seen_seconds)
    

    if start_date:
        if day_start_time_seconds!=0:
            where_clause.append('A.InTime >= ?')
            start_date=datetime.strptime(start_date,"%Y-%m-%d")
            start_date=start_date+timedelta(seconds=day_start_time_seconds)
            if prev_last_seen_time!=None:
                prev_last_seen_time=datetime.strptime(prev_last_seen_time,IN_TIME_FORMAT)
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
            where_clause.append(f'A.Date >= ?')
        search_tuple.append(start_date)
        
    if end_date:
        if day_start_time_seconds!=0:
            where_clause.append(f'A.OutTime <= ?')
            end_date=datetime.strptime(end_date,"%Y-%m-%d")
            end_date=end_date+timedelta(seconds=day_start_time_seconds)
            end_date=str(end_date)
#             print("end date with time: ",end_date)
        else:
            where_clause.append(f'A.Date <= ?')
        search_tuple.append(end_date)
        
    if len(person_ids)==1:
        where_clause.append(f'A.entry_no = ?')
        search_tuple.append(person_ids[0])
    elif len(person_ids)>0:
        where_clause.append(f'A.entry_no in ?')
        search_tuple.append(person_ids)
    elif len(person_ids)==0:
        pass
    
    
    

    where_clause_string = ' AND '.join(where_clause)
    query = ' '.join(partial_query + ['WHERE', where_clause_string])
        
#     print("\n,query : ",query)
#     print("\n values: ",search_tuple)
    res = run_fetch_query(person_db_connection, query=query, values=tuple(search_tuple))
    
#     print("results of query:",res)
    
    person_shift=None
    if len(res)>=1:
        person_shift=res[0][column_names.index("shift")]
    
    
#     print("res length: ",len(res))
#     print("cam names:",ENTRY_CAMERA_NAME,EXIT_CAMERA_NAME,type(ENTRY_CAMERA_NAME))
    
    if len(res)<1:
        return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
    
#     print("\nresult1: ",res[0])
    
    res1_indices=[column_order.index(i) for i in column_order2]
    
    if len(res)==1:
        res2 = pd.DataFrame([list(res[0])+[str(timedelta(seconds=0))]], columns=column_names)
        res1=[tuple(i[k] for k in res1_indices) for i in res]
        res3=list(res[0])
        total_time_duration=0
        total_time_duration=str(timedelta(seconds=total_time_duration))
        late_by=str(timedelta(seconds=0))
        res3=[tuple(res3)+(late_by,total_time_duration)]
        res3=pd.DataFrame(res3,columns=column_names3)
        res1=pd.DataFrame(res1,columns=column_names2)
        
        #updates
        res2.insert(0,"Reporting date",start_date_copy)
        res2[column_names[column_order.index("C.starttime")]]=res2[column_names[column_order.index("C.starttime")]].apply(lambda x: str(timedelta(seconds=x)))
        res3.insert(0,"Reporting date",start_date_copy)
        res3[column_names[column_order.index("C.starttime")]]=res3[column_names[column_order.index("C.starttime")]].apply(lambda x: str(timedelta(seconds=x)) if person_shift!=DYNAMIC_SHIFT_NAME else "")
        res1["shift"]=res1["shift"].apply(lambda x: person_shift)
        res1[column_names2[column_order2.index("C.starttime")]]=res1[column_names2[column_order2.index("C.starttime")]].apply(lambda x: str(timedelta(seconds=x)) if person_shift!=DYNAMIC_SHIFT_NAME else "")
        return res1,res2,res3
#     print("\nresult2: ",res[0])
    
    #Assuming first location is through entry camera,add condition if its not the case
#     rows=[res[0]]
#     last_seen_time=res[0][ONLINE_LOG_TABLE.last_seen_time.value]
#     last_seen_location=res[0][ONLINE_LOG_TABLE.last_seen_location.value]
    
#     print("res before rows: ",res)

    
    rows=[]
    last_seen_location=ENTRY_CAMERA_NAME
    last_seen_time=None
    k=None
    
    
    
    ##Getting first row of the day
    last_seen_location_index=column_order.index('A.LastSeenLocation')
    last_seen_time_index=column_order.index('A.OutTime')
    in_time=None
    
    #collecting previous day result for dynamic roster
#     prev_day_res=None
#     if person_shift_id==DYNAMIC_SHIFT_ID:
#         if day_start_time_seconds!=0:
            
#             prev_date=get_prev_date(start_date,"%Y-%m-%d %H:%M:%S")
#             prev_date=datetime.strptime(prev_date,"%Y-%m-%d")+timedelta(seconds=day_start_time_seconds)
#             prev_date=str(prev_date)
            
#             search_tuple[where_clause.index(f'A.InTime >= ?')]=prev_date
#             search_tuple[where_clause.index(f'A.OutTime <= ?')]=start_date
#         else:
#             prev_date=get_prev_date(end_date)
#             search_tuple[where_clause.index(f'A.Date >= ?')]=prev_date
#             search_tuple[where_clause.index(f'A.Date <= ?')]=prev_date
#         prev_day_res = run_fetch_query(person_db_connection, query=query, values=tuple(search_tuple))
#         print("prev day queries and values: ",query,"\n",search_tuple)
    
    
    late_by_seconds=0
    late_by=str(timedelta(seconds=0))
    shift_intime=res[-1][column_order.index('C.starttime')]
    for i in range(len(res)):
        if res[i][last_seen_location_index]==ENTRY_CAMERA_NAME:
            k=i
            rows.append(list(res[i]))
            in_time=res[i][last_seen_time_index]##datetime str
            
            
            
#             shift=row[column_order.index('B.shift')]
            ##seconds
            in_time=string_to_seconds(in_time,IN_TIME_FORMAT)
            late_by_seconds=in_time-shift_intime
            if late_by_seconds>0:##late penalty
                late_by=str(timedelta(seconds=late_by_seconds))##string  H:M:S format
            break
#     print("rows: ",rows)
#     print("k: ",k)
#     print("\nresult3: ",res[0])
    if k==None:
        return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
    if k==len(res)-1:
#         print("rows1: ",rows)
        for row in rows:
#             print("row in :",row)
            out_time,in_time=row[column_order.index('A.OutTime')],row[column_order.index('A.InTime')]
#             print("intime: ",in_time,out_time)
            time_diff=get_time_difference(in_time,out_time)
            row.append(time_diff)
#         if len(rows[0])!=len(column_names):
#             print("rows1: ",rows)
#             print("column names :",column_names)
#             print("res: ",res)
            
        res2 = pd.DataFrame(rows, columns=column_names)
#         try:
#             res2 = pd.DataFrame(rows, columns=column_names)
#         except:
#             print("\n\n\nexceptino: ",rows,"\n",column_names)
        
#         print("rows2: ",type(rows),"\n",rows)
        res3=list(rows[0])
        res3[column_order.index('A.OutTime')]=rows[-1][column_order.index('A.OutTime')]
        res3[column_order.index('A.LastSeenLocation')]=rows[-1][column_order.index('A.LastSeenLocation')]
        total_time_duration=sum([string_to_seconds(i[column_names.index("Time duration")],"%H:%M:%S") for i in rows])
        total_time_duration=str(timedelta(seconds=total_time_duration))
        res3=[tuple(res3[:-1])+(late_by,total_time_duration)]
        res3=pd.DataFrame(res3,columns=column_names3)
#         try:
#             res3=pd.DataFrame(res3,columns=column_names3)
#         except:
#             print("\nres3 errors: ",res3,"\ncolmn names: ",column_names3)
        res1=[tuple(i[k] for k in res1_indices) for i in rows]
        res1=pd.DataFrame(res1,columns=column_names2)
        
        #updates
        res2.insert(0,"Reporting date",start_date_copy)
        res2[column_names[column_order.index("C.starttime")]]=res2[column_names[column_order.index("C.starttime")]].apply(lambda x: str(timedelta(seconds=x)))
        res3.insert(0,"Reporting date",start_date_copy)
        res3[column_names[column_order.index("C.starttime")]]=res3[column_names[column_order.index("C.starttime")]].apply(lambda x: str(timedelta(seconds=x)) if person_shift!=DYNAMIC_SHIFT_NAME else "")
        res1["shift"]=res1["shift"].apply(lambda x: person_shift)
        res1[column_names2[column_order2.index("C.starttime")]]=res1[column_names2[column_order2.index("C.starttime")]].apply(lambda x: str(timedelta(seconds=x)) if person_shift!=DYNAMIC_SHIFT_NAME else "")
        return res1,res2,res3

#     print("\nresult4: ",res[0])
    
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
#     print("person shift: ",person_shift)
#     print("Dynmic shift id:",DYNAMIC_SHIFT_NAME)
    if person_shift==DYNAMIC_SHIFT_NAME:
        if day_start_time_seconds!=0:
            search_tuple[where_clause.index(f'A.InTime >= ?')]=end_date
            next_date=get_next_date(end_date,"%Y-%m-%d %H:%M:%S")
            next_date=datetime.strptime(next_date,"%Y-%m-%d")+timedelta(seconds=day_start_time_seconds)
            next_date=str(next_date)
            search_tuple[where_clause.index(f'A.OutTime <= ?')]=next_date
        else:
            next_date=get_next_date(end_date)
            search_tuple[where_clause.index(f'A.Date >= ?')]=next_date
            search_tuple[where_clause.index(f'A.Date <= ?')]=next_date
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
                search_tuple[where_clause.index(f'A.InTime >= ?')]=end_date
                next_date=get_next_date(end_date,"%Y-%m-%d %H:%M:%S")
                next_date=datetime.strptime(next_date,"%Y-%m-%d")+timedelta(seconds=day_start_time_seconds)
                next_date=str(next_date)
                search_tuple[where_clause.index(f'A.OutTime <= ?')]=next_date
            else:
                next_date=get_next_date(end_date)
                search_tuple[where_clause.index(f'A.Date >= ?')]=next_date
                search_tuple[where_clause.index(f'A.Date <= ?')]=next_date
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
#     print("\n\nCREATING DATAFRAMES")
    res1=[tuple(i[k] for k in res1_indices) for i in res]
    res1 = pd.DataFrame(res1, columns=column_names2)
    
#     print("rows:",rows)
    
    for row in rows:
        out_time,in_time=row[column_order.index('A.OutTime')],row[column_order.index('A.InTime')]
        time_diff=get_time_difference(in_time,out_time)
        row.append(time_diff)
        
    if len(rows)<1:
        if len(res1)>0:
            #updates
            res1["shift"]=res1["shift"].apply(lambda x: person_shift)
            res1[column_names2[column_order2.index("C.starttime")]]=res1[column_names2[column_order2.index("C.starttime")]].apply(lambda x: str(timedelta(seconds=x)) if person_shift!=DYNAMIC_SHIFT_NAME else "")
            return res1,pd.DataFrame([]),pd.DataFrame([])
        else:
            return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
    
    res3=list(rows[0])
    res3[column_order.index('A.OutTime')]=rows[-1][column_order.index('A.OutTime')]
    res3[column_order.index('A.LastSeenLocation')]=rows[-1][column_order.index('A.LastSeenLocation')]
    total_time_duration=sum([string_to_seconds(i[column_names.index("Time duration")],"%H:%M:%S") for i in rows])
    total_time_duration=str(timedelta(seconds=total_time_duration))
    if person_shift==DYNAMIC_SHIFT_NAME:
        late_by=str(timedelta(seconds=0))
#     print("lateby: ",late_by)
    res3=[tuple(res3[:-1])+(late_by,total_time_duration)]
    res3=pd.DataFrame(res3,columns=column_names3)
    
    
    res2=rows
    res2 = pd.DataFrame(res2, columns=column_names)
    
    #updates
    res2.insert(0,"Reporting date",start_date_copy)
    res2[column_names[column_order.index("C.starttime")]]=res2[column_names[column_order.index("C.starttime")]].apply(lambda x: str(timedelta(seconds=x)))
    res3.insert(0,"Reporting date",start_date_copy)
    res3[column_names[column_order.index("C.starttime")]]=res3[column_names[column_order.index("C.starttime")]].apply(lambda x: str(timedelta(seconds=x)) if person_shift!=DYNAMIC_SHIFT_NAME else "")
    res1["shift"]=res1["shift"].apply(lambda x: person_shift)
    res1[column_names2[column_order2.index("C.starttime")]]=res1[column_names2[column_order2.index("C.starttime")]].apply(lambda x: str(timedelta(seconds=x)) if person_shift!=DYNAMIC_SHIFT_NAME else "")

    #entry exit location name
    
    
#     print("final :",res1,"\n\n",res2,"\n\n",res3)
    
    return res1,res2,res3


def extract_action_tesa_report_data(person_db_connection, user_map, start_date=None, end_date=None,location=None):
    
#     print("dates: ",start_date,end_date,type(start_date))
    person_ids=[]
    roster_ids=[]
    for person_id,roster_id in user_map.items():
        person_ids.append(person_id)
        roster_ids.append(roster_id)  
    person_shift_id=None
    if len(roster_ids)==1:
        person_shift_id=roster_ids[0]    
#     print("person shift id2: ",person_shift_id)
    
    if person_shift_id==DYNAMIC_SHIFT_ID:
        include_prev_day=True
    else:
        include_prev_day=False
    
    reporting_dates=get_dates_in_between(start_date,end_date)
    
#     print("reporting dates: ",reporting_dates)
#     return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
    results = []
    results2=[]
    results3=[]
    
    res,res2,res3=pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
    for date in reporting_dates:
#         try:
#             res,res2,res3=extract_action_tesa_daily_report_data(person_db_connection, user_map,start_date=date, end_date=date,location=location,include_prev_day=include_prev_day)
#         except:
#             print("",start_date,end_date,user_map)
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
        
#     print("results:",type(results)," \n\n",results,"\n\n",results2,"\n\n",results3)   
#     if len(results)==0 or len(results2)==0 or len(results3)==0:
#         return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
        
    return results,results2,results3
        
        

def get_user_rid_map(user_list, user_name):
    
#     print("\n User list: ",user_list,"\nUser name: ",user_name)
    
    user_map = dict()

    partial_query = f'SELECT {PEOPLE_TABLE_FIELDS.field_identity}, {PEOPLE_TABLE_FIELDS.field_shift} FROM {PEOPLE_TABLE_FIELDS.table_name}'

    if len(user_list) == 1 and user_list[0] is None and user_name[0] is None:
        
        query = partial_query
        clause = ()

    elif len(user_list) == 1 and user_list[0] is None and user_name[0] is not None:

        query = f'{partial_query} WHERE {PEOPLE_TABLE_FIELDS.field_name} = ?'
        clause = (user_name[0],)
    
    elif len(user_list) == 1 and user_list[0] is not None and user_name[0] is None:

        query = f'{partial_query} WHERE {PEOPLE_TABLE_FIELDS.field_identity} = ?'
        clause = (user_list[0], )
    
    elif len(user_list) == 1 and user_list[0] is not None and user_name[0] is not None:

        query = f'{partial_query} WHERE {PEOPLE_TABLE_FIELDS.field_identity} = ?'
        clause = (user_list[0], )

    elif len(user_list) > 1:

        query = f'{partial_query} WHERE {PEOPLE_TABLE_FIELDS.field_identity} in ?'
        clause = (user_list, )
        
#     print("1: ",user_list,"\n2: ",user_name,"\n3: ",clause,"\n4: ",query)    
        
    person_db_connection = create_connection(CONFIG['DB']['person_db'])
    res=run_fetch_query(person_db_connection,query,clause)
    
#     print("\n5: ",res)
    user_map={i:j for i,j in res}
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
    
#     print("\nresults type",type(results))
#     print("\nresults length: ",len(results),"\n results before: ",results)
#     if len(results)==0 or len(results2)==0 or len(results3)==0:
#         return '', pd.DataFrame([])
    
    results.fillna(value='', inplace=True)
    results2.fillna(value='', inplace=True)
    results3.fillna(value='', inplace=True)
    
    
    
#     print("\nresults: ",results)
#     write_report(results, path, sheet_name='log_report', banner_suffix=banner_suffix)
#     write_reports([results,results2,results3], path, sheet_name='log_report', banner_suffix=banner_suffix)
    write_reports([results,results2,results3], path, sheet_name=['Camera logs','Working Hours logs','Daily Report'], banner_suffix=banner_suffix)
    person_db_connection.close()
    return path, results


# def extract_action_tesa_report_data(person_db_connection, user_map, start_date=None, end_date=None,location=None):

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
        
#     print(entry_no_late_by_dict)
    
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
            
        # print("\ntype :",type(report.values[0][in_time_ind][0]),report.values[0][in_time_ind])
        for name in headings:
            worksheet.write(headings_row, headings_col, name, label_format)
            headings_col += 1
        entry_row = 6
        
        #put this logic in create report and add condition on late by here
#         in_time_format="%Y-%m-%d %H:%M:%S.%f"
#         static_in_time_string='09:00:00.000000'
#         static_in_time=datetime.strptime(static_in_time_string,"%H:%M:%S.%f")
#         shift_intime_dict={}
#         RELAXATION_TIME=5*60
        
    
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
                        
                        
                    
                    #put this logic in create report and add condition on late by here
#                     if "Late_by" in headings:
#                         in_time=row[in_time_ind]##datetime str
#                         shift=row[shift_ind]
#                         shift_intime=shift_intime_dict[shift]##seconds

#                         in_time=datetime.strptime(in_time,in_time_format)#datetime
#                         in_time=in_time.time()
#                         in_time=time_to_seconds(in_time)##to seconds

#                         if in_time-shift_intime>RELAXATION_TIME:##late penalty
#                             late_by=str(timedelta(seconds=(in_time-shift_intime)))##string  H:M:S format
#                             #condition on late penalty
#                             late_penalty='' 
#                             nb_format = number_entry_format_late
#                             ef = entry_format_late
#                         else:
#                             late_by=0
#                             late_penalty=''
#                             nb_format = number_entry_format
#                             ef = entry_format
#                     else:
#                         nb_format = number_entry_format
#                         ef = entry_format

            entry_col = 0
            for index, i in enumerate(row):
#                 if(index in [3, 4]):
#                     worksheet.write(entry_row, entry_col, i, nb_format)
#                 else:
                    
                worksheet.write(entry_row, entry_col, i, ef)
                entry_col+=1
            entry_row += 1
    workbook.close()
    
    

        
    

                        
                        
                        
                        
                        
                        
                        