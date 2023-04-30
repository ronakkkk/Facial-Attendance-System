
#REPORT
from src.action_tesa_report_new import *

from src.action_tesa_report_utils import *

# # timestamp_string="2021-10-20 14:46:34.568802"
# # print(get_date_and_time(timestamp_string))
# user_map=get_user_rid_map([1],[None])
# print("up",user_map)
a,b,c = None,None,None


# a,b,c=extract_action_tesa_daily_report_data(create_connection(CONFIG["DB"]["person_db"]), user_map, start_date="2021-10-21", end_date="2021-10-21",location=None,day_start_time="00:00:01",include_prev_day=False)

# a,b,c=extract_action_tesa_report_data(create_connection(CONFIG["DB"]["person_db"]), user_map, start_date="2021-10-27", end_date="2021-11-03",location=None)
# c1
# a,b,c=extract_action_tesa_report_data(create_connection(CONFIG["DB"]["person_db"]), get_user_rid_map([1],[None]), start_date="2021-10-27", end_date="2021-10-28",location=None)
# c2
# a,b,c=extract_action_tesa_report_data(create_connection(CONFIG["DB"]["person_db"]), get_user_rid_map([28],[None]), start_date="2021-10-28", end_date="2021-10-28",location=None)
# a,b,c=extract_action_tesa_report_data(create_connection(CONFIG["DB"]["person_db"]), get_user_rid_map([1],[None]), start_date="2021-10-20", end_date="2021-10-21",location=None)

# print("TEST",c["STATUS"][0],c['DAY TYPE'][0],type(c['DAY TYPE']))
# c.loc[ c['DAY TYPE'][0] == "Working Day" or c['DAY TYPE'][0] == "Company Holiday" or c['DAY TYPE'][0] == "Department Holiday", "STATUS"] = c['DAY TYPE'][0]

# c4 full day leave late by 10 hours
# a,b,c=extract_action_tesa_report_data(create_connection(CONFIG["DB"]["person_db"]), get_user_rid_map([3],[None]), start_date="2021-10-30", end_date="2021-10-30",location=None)

# c5 only entry log present showing full day absent, shall be mispunched 
# a,b,c=extract_action_tesa_report_data(create_connection(CONFIG["DB"]["person_db"]), get_user_rid_map([31],[None]), start_date="2021-11-02", end_date="2021-11-02",location=None)

# c6 mispunch on weekly off
# a,b,c=extract_action_tesa_report_data(create_connection(CONFIG["DB"]["person_db"]), get_user_rid_map([9],[None]), start_date="2021-10-27", end_date="2021-10-27",location=None)

# c7 no log showing but status is mispunched
# a,b,c=extract_action_tesa_report_data(create_connection(CONFIG["DB"]["person_db"]), get_user_rid_map([9],[None]), start_date="2021-11-11", end_date="2021-11-11",location=None)

# a,b,c = generate_action_tesa_report(user_list=[i for i in range(1,48)], user_name=[None for i in range(1,48)], start_date="2021-11-01", end_date="2021-11-30", location=None)

# print(type(a), type(b), type(c), len(a), len(b), len(c))


# d = generate_action_tesa_monthly_report(user_list=[i for i in range(1,48)], user_name=[None for i in range(1,48)], month=10,year=2021, location=None)

#c1
d = generate_action_tesa_monthly_report(user_list=[1], user_name=[None], month=10,year=2021, location=None)

print(d)
print(type(d))
print(len(d))
print(d.columns)
print(len(d.columns))



cond = 6
if cond==0:
    print(1,"\n:",a.to_string())
    print(2,"\n:",b.to_string())
    print(3,"\n:",c.to_string())
elif cond==1:
    print(1,"\n:",a)
    print(2,"\n:",b)
    print(3,"\n:",c)

#downloading reports
from src.excel_report_format import *

if cond == 2:
    write_report_daily(c,"temp", filename= "11.xlsx")
    
if cond==3:
    write_report_monthly(d,"temp", filename ="6month.xlsx")



# #QUERIES
from src.queries import *

# # print(get_point_clause(['a','b'],['c','d']))

# # print(get_range_clause(['a','b'],[('c','d'),('e','f')]))
# # print(get_range_clause(['a','b'],[('c','d'),('e',None)]))

conn=create_connection(CONFIG["DB"]["person_db"])
# query='SELECT * FROM person_details WHERE empid = 50'
# container=Person_Person_Details_Container
# # print(run_select_query(conn,query,()))
# # res_dc=run_select_query(conn,query,(),container,True)
# # print(res_dc)
# # print(res_dc[0].empid)

# # clause=''
# # print(format_query(query,clause))
# # clause='WHERE empid = 1'
# # print(format_query(query,clause))

auth_conn=create_connection(CONFIG["DB"]["auth_db"])

# # print(select_from_auth_user(auth_conn))


# # print(select_from_person_alerts(conn,alertid=3))

# query = f'INSERT INTO {Person_Alerts_container.field.tablename}({Person_Alerts_container.field.empid}, {Person_Alerts_container.field.datetime}, {Person_Alerts_container.field.date}, {Person_Alerts_container.field.location}) VALUES(?, ?, ?, ?)'
# # run_query_noreturn(conn, query, (1, "1:0:0", "2021-2-11", ""))


# # def fun(x:int)->Union[str,NoReturn]:
# #     if x==1:
# #         return
# #     else:
# #         return ""
    
# # print(fun(1))
# # print(fun(2))

face_conn=create_connection(CONFIG["DB"]["face_db"])
# # person_details,fd=search_all(face_conn,conn)
# # print(fd)


# # print([i for i in Person_Alerts_container.field])



# # class A:
# #     name='a'
    
# # y=A
# # x="name"
# # print(eval(f"A.{x}"))

# print(Person_Person_Details_Container.enum.empid.value)

#APP

# from src.flaskapp import app
# # app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# # app.config['UPLOAD_FOLDER'] = CONFIG['UPLOAD']['webapp_upload_path']
# # app.config['TEMP_FOLDER'] = CONFIG['TEMP']['temp_processing_path']
# app.run(host="127.0.0.1", port=8000, debug=True, threaded=True)


from src.queries import *

from src.webapp_utils import *

# print(is_known_user(None))

# print(get_department())
# print(get_roster())
# print(get_shift_timing(2))

# print(add_department("sales", "delhi", "hod1"))

# print(update_employee_department(["47"], ['2']))

# print(add_holiday("2021-12-25", "Christmas"))

#foreign constraint fails
# print(add_holiday("2021-12-25", "Christmas","department",4))

# print(add_location("haryana", "haryana"))

# print(add_category("Non-Employee", "Person"))

# print(update_department([1], ["Department1"], ["delhi"], ["headofdep1"]))

# print(get_locations())
# print(get_status_list())
# print(get_holiday_types())

# print(update_employee_shift(['47'],['D']))

# import glob, os

# fnames = glob.glob(os.path.join(CONFIG['TEMP']['temp_processing_path'], f'*-{1}*'))
# for f in fnames:
#     os.unlink(f)

# print(get_department())

# # print(select_from_person_details(conn,empid='4'))

# print(get_hod_list())

warehouse_db_connection = create_connection(CONFIG["DB"]["warehouse_db"])

# print(update_department_details(conn, warehouse_db_connection, 2, depthod = ""))

# print(update_department([6], ["sales3"], ["punjab"], [None]))

# print(select_from_attendance_logs(conn, empid = 6,start_date = "2021-10-29",end_date = "2021-11-1", return_dc = True))


from src.action_tesa_report_utils import *


timestamp = datetime.strptime("2021-12-24","%Y-%m-%d").date()
# timestamp = "2022/10/25"
# extra_clause = f'AND {Warehouse_Oldempshifts_Container.field.todate} > {str((datetime.strptime(timestamp, timestamp_format)+timedelta(days=-1)).date())} AND {Warehouse_Oldempshifts_Container.field.fromdate} > {str((datetime.strptime(timestamp, timestamp_format)+timedelta(days=1)).date())} ORDER BY {Warehouse_Oldempshifts_Container.field.datetime} ASC'
# extra_clause = f'AND {Warehouse_Oldempshifts_Container.field.todate} > {timestamp} AND {Warehouse_Oldempshifts_Container.field.fromdate} >= {timestamp}'# ORDER BY {Warehouse_Oldempshifts_Container.field.datetime} ASC'

# rows = select_from_warehouse_oldempshifts(warehouse_db_connection, empid = 1, extra_clause = extra_clause, return_dc = True)

# query = f'SELECT * FROM {Warehouse_Oldempshifts_Container.field.tablename} WHERE empid = ? AND {Warehouse_Oldempshifts_Container.field.todate} <= ? AND {Warehouse_Oldempshifts_Container.field.fromdate} >= ?'

# values=(47,str(timestamp), str(timestamp))
# print(query, values)
# rows= run_select_query(warehouse_db_connection, query, values, Warehouse_Oldempshifts_Container, return_dc=True)
# print(rows)
# if rows:
#     print(len(rows))


# print(get_shift(empid,emp_shift_id, emp_curr_shift_timestamp, timestamp,timestamp_format="%Y-%m-%d"))
# print(get_shift(47, 1, "2021-12-26 21:49:37.125315", "2021-12-24",timestamp_format="%Y-%m-%d"))

# print(get_department(empid,emp_dep_id,emp_curr_dept_timestamp,timestamp,timestamp_format="%Y-%m-%d"))

# print(get_department(47,6,"2021-12-27 03:21:01.115615","2021-12-24",timestamp_format="%Y-%m-%d"))



# import holidays
# india_holidays = holidays.India(years=2020)
# # prov = ['AP', 'AS','BR','CG','GJ','HR','KA','KL','MH','MP','OD','RJ','SK','TN','TN','UK','UP','WB']
# prov =[1]
# for pr in prov:
#     # print("\n\n",pr)
#     # india_holidays =holidays.CountryHoliday('IN',prov=pr,years=2020)
#     for date, occasion in india_holidays.items():
#         print(f'{date} - {occasion}')
        
# year =2020
# fromdate =str(date(day=1, month= 1, year= year))
# todate =str(date(day=31, month= 12, year= year))
# deptid = 1
# holidays = select_from_holiday(conn,fromdate=fromdate,todate=todate,deptid= deptid,return_dc= True)
# holidays = [(str(i.date),type(i.deptid),i.deptid) for i in holidays]

# year =2022
# deptid = 1
# # holidays = get_compay_holiday_list(year)
# holidays = get_department_holiday_list(year, deptid = deptid)

# print(holidays,'\n', len(holidays))
        
        


# print(get_dept_id("sales", "delhi"))

# print(get_ids())


#downloading reports
# data =  {'start_ent': ['0'], 'end_ent': ['100'], 'shift': ['D', '2'], 'dpmt': ['1', '4'],'from_date': '2021-10-12', 'to_date': '2021-11-03'}
# start_ent =  data.get("start_ent", None)
# end_ent = data.get('end_ent', None)
# start_date = data.get('from_date',None)
# end_date = data.get('to_date', None)
# emp_ids = data.get('emp_ids', None)
# emp_names = data.get('emp_name', None)
# shifts = data.get('shift', None)
# departments = data.get('dpmt', None)

# print("datesd",start_date, end_date)

# res= download_cam_logs_report( user_list = emp_ids, user_name = emp_names, shifts = shifts, departments = departments, start_date= start_date, end_date = end_date, total_rows = int(end_ent[0])-int(start_ent[0]))
# # print(res.to_string())
# # print(type(res))

# shifts= ['Dynamic']
# department = ['Department1']
# res = res[res['SHIFT'].isin(shifts) & res['DEPARTMENT'].isin(department)]
# # print(res.to_string())

# cond = 1
# if cond ==0 :
#     write_report_all_logs(res, "/temp", filename='cam1.xlsx', query='' , banner_suffix='')

