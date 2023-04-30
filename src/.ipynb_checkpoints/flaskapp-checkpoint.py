from flask import Flask, render_template, send_file, url_for, request, session, flash, jsonify, make_response
import sqlite3
from sqlite3 import Error
import numpy as np
import pandas as pd
# from shutil import copyfile
# import math
from werkzeug import serving
from .webapp_utils import *
from hashlib import md5
import os
import time
import random, string
from pymemcache.client import base
import pickle
import crcmod
import json
import datetime
from zipfile import ZipFile


from .load_config import CONFIG
TEMPLATE_FOLDER = CONFIG['GUI']['gui_template_path']
FAV_ICON = CONFIG['GUI']['fav_icon']
ACTIVE_ICON = CONFIG['GUI']['active_icon']
DEACTIVE_ICON = CONFIG['GUI']['deactive_icon']
SHUTDOWN_ICON = CONFIG['GUI']['shutdown_icon']
HOME_ICON = CONFIG['GUI']['home_icon']
FACE_IMG_FOLDER = CONFIG['DATA']['face_img_path']
MAX_DISPLAY_ROWS = 100

print(CONFIG['GUI']['gui_template_path'])
FACE_DB_PATH = CONFIG['DB']['face_db']
app = Flask(__name__, template_folder=TEMPLATE_FOLDER, root_path=CONFIG['COMMON']['base_path'])
app.config['SECRET_KEY'] = 'abcd'

user_container = base.Client(('localhost', 11211))

logo_file_path = "logo/Logo.jpg"
DEVELOPER_MODE = True

######################## Load Test APIs ##########################################################

compute32_crc = crcmod.mkCrcFun(0x1f1020301, initCrc=0)

@app.route('/api/select/sql/', methods=["GET"])
def process_api_sql():

    session_id = request.args.get('session_id')
    print(f'session_id: {session_id}')
    query = '1'
    display_query = '1'
    sql_columns = ['PART_TYPE']

    con = sqlite3.connect(f"{db_path}")
    cur = con.cursor()
    t1 = time.time()
    cur.execute(f'Select count(*) from "customer" where {query}')
    t2 = time.time()
    print(f'Time taken in selection: {t2-t1}')
    rows_sel = cur.fetchone()[0]
    t3 = time.time()
    print(f'Time taken in fetching: {t3-t2}')

    t4 = time.time()
    cur.execute('SELECT COUNT(*) FROM "customer"')
    t5 = time.time()
    print(f'Time taken in selection: {t5-t4}')
    t6 = time.time()
    total_rows = cur.fetchone()[0]
    t7 = time.time()
    print(f'Time taken in fetching: {t7-t6}')

    tempD = {'total_selection': rows_sel, 'total_rows':total_rows}

    user_container.set(f'{session_id}_counts', pickle.dumps(tempD), noreply=False)
    user_container.set(f'{session_id}_query', pickle.dumps(query), noreply=False)
    user_container.set(f'{session_id}_display_query', pickle.dumps(display_query), noreply=False)
    user_container.set(f'{session_id}_sql_columns', pickle.dumps(sql_columns), noreply=False)

    return jsonify(tempD)                            


@app.route('/api/show/data/', methods=['GET'])
def api_show_data():

    session_id = request.args.get('session_id')
    query = pickle.loads(user_container.get(f'{session_id}_query'))
    display_query = pickle.loads(user_container.get(f'{session_id}_display_query'))
    sql_columns = pickle.loads(user_container.get(f'{session_id}_sql_columns'))
    counts = pickle.loads(user_container.get(f'{session_id}_counts'))
  
    rows = fetch_data('customer', where_clause=query)
    #{'total_selection': total_selection, 'total_rows':total_rows})
    total_selection = counts['total_selection']
    total_rows = counts['total_rows']

    serialized_data = pickle.dumps(rows)
    user_container.set(f'{session_id}_fetched_data', serialized_data, noreply=False)
    crc = compute32_crc(serialized_data)

    return jsonify({'stored bytes len':len(serialized_data), 'CRC':crc})
    
@app.route('/api/check/data/', methods=['GET'])
def check_data():

    session_id = request.args.get('session_id')
    serialized_data = user_container.get(f'{session_id}_fetched_data')
    crc = compute32_crc(serialized_data)
    
    return jsonify({'stored bytes len':len(serialized_data), 'CRC':crc})
    
###################################################################################   

################################# Non-route functions #############################
def fetch_data(table_name, where_clause='1', column_name='*', fetch_type='all'):
    
    con = sqlite3.connect(f'{db_path}')
    cur = con.cursor()

    query = f'SELECT {column_name} FROM "{table_name}" WHERE {where_clause}'
    cur.execute(query)

    if fetch_type == 'all':
        rows = cur.fetchall()
    else:
        rows = cur.fetchone()
    
    cur.close()
    con.close()

    return rows

def fetch_data_order(table_name, where_clause='1', column_name='*', fetch_type='all', order=None):
    
    con = sqlite3.connect(f'{db_path}')
    cur = con.cursor()
    
    if order is None:
        query = f'SELECT {column_name} FROM "{table_name}" WHERE {where_clause}'
    else:
        query = f'SELECT {column_name} FROM "{table_name}" WHERE {where_clause} ORDER BY {order} DESC'
        
    cur.execute(query)

    if fetch_type == 'all':
        rows = cur.fetchall()
    else:
        rows = cur.fetchone()
    
    cur.close()
    con.close()

    return rows

def run_query_ret(query, values=()):

    con = sqlite3.connect(f'{db_path}')
    cur = con.cursor()
    cur.execute(query, values)
    rows = cur.fetchall()
    cur.close()
    con.close()
    return rows
    
############# Common Functions ###########################

def get_processed_tuple(element_list):

    processed_list = [ele.replace(' ', '|') for ele in element_list]
    return [[inner, show] for inner, show in zip(processed_list, element_list)]

def return_home_page(user, add=False):

    #print(len(inspect.stack()))
    # Check for authentication here if not authenticated return login page.
    # faced one error where this function was called but failed for
    # File "D:\ongoing\FacialRecoginitionBased\FRAS\Development\v0.2.0.0\src\webapp.py", line 142, in go_home
    # return return_home_page(current_user)
    # File "D:\ongoing\FacialRecoginitionBased\FRAS\Development\v0.2.0.0\src\webapp.py", line 63, in return_home_page
    # operator_id=user.id,
    # File "C:\Users\NableIT02\AppData\Local\Programs\Python\Python36\Lib\site-packages\werkzeug\local.py", line 348, in __getattr__
    # return getattr(self._get_current_object(), name)
    # AttributeError: 'AnonymousUserMixin' object has no attribute 'id'

    if add:
        if len(user_container.keys()) > 0:
            unique_uid = max(user_container.keys()) + 1
        else:
            unique_uid = 1

        user_container[unique_uid] = user
        session['_tracker_id'] = unique_uid

    end_date = datemodule.today()
    start_date = end_date

    camera_list = get_camera_list()
    #video_list = get_video_list()
    video_list = []

    return render_template('home.html', 
                            start_date=start_date,
                            end_date=end_date,
                            camera_list=get_processed_tuple(camera_list),
                            video_list=get_processed_tuple(video_list),
                            logged_in=True, 
                            operator_id=user.id, 
                            is_admin=user.is_admin)

def get_details_for_display(person_details, face_details):
    
    details_for_display = []
    for user_id, user_name, threat_type, shift_id in person_details:
        image_partial_name = face_details[user_id]

        images = []
        for i in image_partial_name:
            search_path = os.path.join(CONFIG['DATA']['face_img_path'], f'{i[0]}.*')
            fnames = glob.glob(search_path)

            if len(fnames) > 0:
                ext = fnames[0].split('.')[-1]
                images.append(f'{i[0]}.{ext}')
        details_for_display.append([user_id, user_name, threat_type, get_shift_timing(shift_id), images])
    
    return details_for_display

@app.route('/static/files/<filename>', methods=['POST', 'GET'])
def get_file(filename):

    fname = ''

    if filename == 'favicon':
        fname = FAV_ICON
    
    if filename == 'active':
        fname = ACTIVE_ICON
    
    if filename == 'closed':
        fname = DEACTIVE_ICON
    
    if filename == 'shutdown':
        fname = SHUTDOWN_ICON
    
    if filename == 'home':
        fname = HOME_ICON
    
    TEMPLATE_FOLDER = 'templates'

    if filename == 'bs-css':
        fname = os.path.join(TEMPLATE_FOLDER, 'css', 'bootstrap.min.css')
    
    if filename == 'logo':
        fname = logo_file_path
    
    if filename == 'bootstrap.min.css.map':
        fname = os.path.join(TEMPLATE_FOLDER, 'css', 'bootstrap.min.css.map')
    
    if filename == 'bs-js':
        fname = os.path.join(TEMPLATE_FOLDER, 'js', 'bootstrap.js')
    
    if filename == 'popper':
        fname = os.path.join(TEMPLATE_FOLDER, 'js', 'popper.min.js')
    
    if filename == 'jq':
        fname = os.path.join(TEMPLATE_FOLDER, 'js', 'jquery-3.2.1.slim.min.js')

    if filename == 'mjq':
        fname = os.path.join(TEMPLATE_FOLDER, 'js', 'jquery.multiselect.js')
    
    if filename == 'bootstrap.js.map':
        fname = os.path.join(TEMPLATE_FOLDER, 'bootstrap.js.map')

    if filename == 'mcss':
        fname = os.path.join(TEMPLATE_FOLDER, 'css', 'jquery.multiselect.css')


    if filename == 'jquery-3.3.1.js':
        fname = os.path.join(TEMPLATE_FOLDER, 'js', 'jquery-3.3.1.js')
    print(fname)
    
    return send_file(fname)

@app.route('/static/temp/img/<filename>')
def get_temp_img(filename):
    filename = os.path.join(app.config['TEMP_FOLDER'], filename)
    return send_file(filename)

@app.route('/static/sample/img/good/<fileid>')
def get_good_img(fileid):
    fname = os.path.join(CONFIG['SAMPLE']['sample_good_image_path'], f'{fileid}.jpg')
    return send_file(fname)

@app.route('/static/sample/img/bad/<fileid>')
def get_bad_img(fileid):
    fname = os.path.join(CONFIG['SAMPLE']['sample_bad_image_path'], f'{fileid}.jpg')
    return send_file(fname)

@app.route('/static/faces/<filename>')
def get_db_faces(filename):
    filename = os.path.join(CONFIG['DATA']['face_img_path'], filename)
    return send_file(filename)

@app.route('/static/files/logs/<filename>', methods=['POST', 'GET'])
def download_log(filename):
    fname = os.path.join(CONFIG['TEMP']['temp_processing_path'], filename)
    return send_file(fname)

@app.route('/static/temp/video/<filename>')
def get_video_file(filename):
    filename = os.path.join(CONFIG['TEMP']['temp_processing_path'], filename)
    return send_file(filename)

############# Webapp/views functions ###############################
    
def run_fetch_query(conn, query, values=(), fetch_type='all'):
    
    try:
        curr = conn.cursor()
        curr.execute(query, values)
        if fetch_type == 'all':
            rows = curr.fetchall()
        else:
            rows = curr.fetchone()
        return rows
    except Error as e:
        if DEVELOPER_MODE:
            print(f'[run_fetch_query]: {e}')
        else:
            print('An Error Occured')    

def encrypt(password):

    password = password.encode('utf-8')
    return md5(password).hexdigest()    

@app.route('/')
def details_roster():
    # operator = current_user
    roster_details = get_roster()
    print(roster_details)
    name = [(str(roster_details[i][1]).split(' ('))[0] for i in range(len(roster_details))]
    print(name)
    rname = json.dumps(name)
    return render_template('roster.html', name=rname)
                    

@app.route('/register', methods=['POST', 'GET'])
def add_roster_details():

    # operator = current_user
    roster_details = get_roster()
    static_num = [int((roster_details[i][0])) for i in range(len(roster_details)) if len((str(roster_details[i][1]).split(' ('))[1]) != 4] #getting number of static rosters ids
    print(static_num)
    dynamic_num = [((roster_details[i][0])[1:]) for i in range(len(roster_details)) if len((str(roster_details[i][1]).split(' ('))[1]) == 4]
    print(dynamic_num)
    rname = request.form['rname'].lower()
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    rwkly_off = request.form['wklyoff']
    
    if len(dynamic_num) == 0:
        ri = f'D'
        end_tim = 9
        start_tim = 0
        name = 'Dynamic'
        add_roster(ri, name, start_tim, end_tim)

    if len(static_num) == 0:
        rid = 1
    else:
        rid = static_num[-1]+1
    
    rid = str(rid).zfill(3)
    start_time = int(start_time)*3600
    end_time = (int(end_time))*3600
    if end_time==0:
        end_time=24*3600

    print(start_time, end_time) 

    x = add_roster(rid, rname, start_time, end_time) 

    if x==True:
        flash('Roster added successfully!!')
    elif x==False:
        flash('Roster addition failed.')
    elif x==-1:
        flash("Shift name already exists. Enter another name.")

    return details_roster()

#finished till here
@app.route('/reports', methods=['POST', 'GET'])
def print_reports():
    # if request.form.keys():
    keys = [k for k in request.form.keys()]
    print(keys)
    # shift = #fetch all of the shifts names from db
    # department = #fetch all of the department names from db
    if 'cam_log' in keys:
        return render_template('printCamLog.html')
    elif 'wrk_hrs_log' in keys:
        return render_template('printWorkHrsLog.html')
    elif 'dly_rprt' in keys:
        return render_template('printDailyLog.html')
    elif 'mnthly_rprt' in keys:
        return render_template('printMonthlyLog.html')
    else:
        return render_template('printReport.html')

@app.route('/reports/wrk_hr_logs', methods=['POST', 'GET'])
def print_wrk_hrs_log():
    if request.form.keys():
        dict_value = {k:request.form.getlist(k)for k in request.form.keys() if len(request.form[k])!=0}
        li = ['emp_id', 'cam_logs']
        for key in li:
            if key in dict_value.keys():
                del dict_value[key]
        print(dict_value)
        final_data_for_filter = dict()
        count = 0
        # print('here')
        final_data_for_filter = dict()
        count = 0
        print('here')
        if ('start_ent' in dict_value.keys() and 'end_ent' in dict_value.keys()):
            print('ss')
            count+=1
        if 'empid' in dict_value.keys():
            final_data_for_filter['emp_ids']=None
            final_data_for_filter['emp_ids'] = dict_value['empid'][0].split(';')
            count+=1
            print('yy')
        if 'empname' in dict_value.keys():
            final_data_for_filter['emp_name']=None
            final_data_for_filter['emp_name'] = dict_value['empname'][0].split(';')
            count+=1
        if 'shifts' in dict_value.keys():
            final_data_for_filter['shift']=None
            final_data_for_filter['shift'] = dict_value['shifts']
            count+=1
        if 'dpmts' in dict_value.keys():
            final_data_for_filter['dpmt']=None
            final_data_for_filter['dpmt'] = dict_value['dpmts']
            count+=1
        if 'from_date' in dict_value.keys() and 'to_date' in dict_value.keys():
            final_data_for_filter['from_date']=None
            final_data_for_filter['from_date'] = dict_value['from_date'][0]
            final_data_for_filter['to_date']=None
            final_data_for_filter['to_date'] = dict_value['to_date'][0]
            count+=1
        print(count)
    return details_roster()

@app.route('/reports/cam_logs', methods=['POST', 'GET'])
def print_cam_logs():
    if request.form.keys():
        dict_value = {k:request.form.getlist(k) for k in request.form.keys() if len(request.form[k])!=0}
        li = ['emp_id', 'cam_logs']
        for key in li:
            if key in dict_value.keys():
                del dict_value[key]
        print(dict_value)
        final_data_for_filter = dict()
        count = 0
        print('here')
        if ('start_ent' in dict_value.keys() and 'end_ent' in dict_value.keys()):
            print('ss')
            count+=1
        if 'empid' in dict_value.keys():
            final_data_for_filter['emp_ids']=None
            final_data_for_filter['emp_ids'] = dict_value['empid'][0].split(';')
            count+=1
            print('yy')
        if 'empname' in dict_value.keys():
            final_data_for_filter['emp_name']=None
            final_data_for_filter['emp_name'] = dict_value['empname'][0].split(';')
            count+=1
        if 'shifts' in dict_value.keys():
            final_data_for_filter['shift']=None
            final_data_for_filter['shift'] = dict_value['shifts']
            count+=1
        if 'dpmts' in dict_value.keys():
            final_data_for_filter['dpmt']=None
            final_data_for_filter['dpmt'] = dict_value['dpmts']
            count+=1
        if 'from_date' in dict_value.keys() and 'to_date' in dict_value.keys():
            final_data_for_filter['from_date']=None
            final_data_for_filter['from_date'] = dict_value['from_date'][0]
            final_data_for_filter['to_date']=None
            final_data_for_filter['to_date'] = dict_value['to_date'][0]
            count+=1
        print(count)
    return details_roster()

@app.route('/reports/daliy_logs', methods=['POST', 'GET'])
def print_dly_logs():
    if request.form.keys():
        dict_value = {k:request.form.getlist(k) for k in request.form.keys() if len(request.form[k])!=0}
        li = ['emp_id', 'cam_logs']
        for key in li:
            if key in dict_value.keys():
                del dict_value[key]
        print(dict_value)
        final_data_for_filter = dict()
        count = 0
        print('here')
        if ('start_ent' in dict_value.keys() and 'end_ent' in dict_value.keys()):
            print('ss')
            count+=1
        if 'empid' in dict_value.keys():
            final_data_for_filter['emp_ids']=None
            final_data_for_filter['emp_ids'] = dict_value['empid'][0].split(';')
            count+=1
            print('yy')
        if 'empname' in dict_value.keys():
            final_data_for_filter['emp_name']=None
            final_data_for_filter['emp_name'] = dict_value['empname'][0].split(';')
            count+=1
        if 'shifts' in dict_value.keys():
            final_data_for_filter['shift']=None
            final_data_for_filter['shift'] = dict_value['shifts']
            count+=1
        if 'dpmts' in dict_value.keys():
            final_data_for_filter['dpmt']=None
            final_data_for_filter['dpmt'] = dict_value['dpmts']
            count+=1
        if 'from_date' in dict_value.keys() and 'to_date' in dict_value.keys():
            final_data_for_filter['from_date']=None
            final_data_for_filter['from_date'] = dict_value['from_date'][0]
            final_data_for_filter['to_date']=None
            final_data_for_filter['to_date'] = dict_value['to_date'][0]
            count+=1
        print(count)

        li_key_report= ['lc', 'el', 'mp', 'absent', 'gw', 'present', 'hlf_day', 'full_day_leave',]
        li_specific_report = [dict_value[k] for k in dict_value.keys() if k in li_key_report]
        print(li_specific_report, final_data_for_filter)

    return details_roster()

@app.route('/reports/monthly_logs', methods=['POST', 'GET'])
def print_mnthly_logs():
    if request.form.keys():
        dict_value = {k:request.form.getlist(k) for k in request.form.keys() if len(request.form[k])!=0}
        li = ['emp_id', 'cam_logs']
        for key in li:
            if key in dict_value.keys():
                del dict_value[key]
        print(dict_value)
        final_data_for_filter = dict()
        count = 0
        print('here')
        if ('start_ent' in dict_value.keys() and 'end_ent' in dict_value.keys()):
            print('ss')
            count+=1
        if 'empid' in dict_value.keys():
            final_data_for_filter['emp_ids']=None
            final_data_for_filter['emp_ids'] = dict_value['empid'][0].split(';')
            count+=1
            print('yy')
        if 'empname' in dict_value.keys():
            final_data_for_filter['emp_name']=None
            final_data_for_filter['emp_name'] = dict_value['empname'][0].split(';')
            count+=1
        if 'shifts' in dict_value.keys():
            final_data_for_filter['shift']=None
            final_data_for_filter['shift'] = dict_value['shifts']
            count+=1
        if 'dpmts' in dict_value.keys():
            final_data_for_filter['dpmt']=None
            final_data_for_filter['dpmt'] = dict_value['dpmts']
            count+=1
        if 'from_date' in dict_value.keys() and 'to_date' in dict_value.keys():
            final_data_for_filter['from_date']=None
            final_data_for_filter['from_date'] = dict_value['from_date'][0]
            final_data_for_filter['to_date']=None
            final_data_for_filter['to_date'] = dict_value['to_date'][0]
            count+=1
        print(count)

        li_key_report= ['lc', 'el', 'mp', 'absent', 'gw', 'present', 'hlf_day', 'full_day_leave',]
        li_specific_report = [dict_value[k][i] for k in dict_value.keys() for i in range(len(dict_value[k])) if k in li_key_report]
        li_mon = ['month', 'year']
        selected_month = {k:dict_value[k][0] for k in dict_value.keys() if k in li_mon}
        print(li_specific_report, final_data_for_filter, selected_month)

    return details_roster()

@app.route('/dept')
def details_department():
    # operator = current_user
    department_details = get_roster()
    code = [(str(department_details[i][1]).split(' ('))[0] for i in range(len(department_details))]
    rcode = json.dumps(code)
    return render_template('department.html', name=rcode)
                    

@app.route('/add_dept', methods=['POST', 'GET'])
def add_dept_details():

    # operator = current_user
    dpmt_details = get_roster()

    rname = request.form['rname'].lower()
    rcode = request.form['rcode']
    rhod = request.form['rhod']
    rwkly_off = request.form['wklyoff']

    x = add_roster(rid, rname) #change to add department

    if x==True:
        flash('Department added successfully!!')
    elif x==False:
        flash('Department addition failed.')
    elif x==-1:
        flash("Department code already exists. Enter another code.")

    return details_department()


@app.route('/update',  methods=['POST', 'GET'])
def update_employee():
    dict_value = {k:request.form[k] for k in request.form.keys() if len(request.form[k])!=0}
    print(dict_value)
    return render_template('updateEmployee.html')

@app.route('/update_details',  methods=['POST', 'GET'])
def update_details_employee():
    dict_value = {k:request.form[k] for k in request.form.keys() if len(request.form[k])!=0}
    print(dict_value)
    empid=''
    empname=''  # will be a list if the user search on the basis of employee name. Need to handle over here such that in case of a single person it should
                # pass a string else it should pass a list.
    emp_dpmt=''
    empstatus=''
    img=''
    currshift=''
    location=''
    wklyoff=''
    return render_template('updateDetailsEmployee.html',empid=empid, 
                            empname=empname, 
                            emp_dpmt=emp_dpmt, 
                            empstatus=empstatus,  
                            currshift=currshift, 
                            location=location,  
                            wklyoff=wklyoff )

@app.route('/update_dpmt',  methods=['POST', 'GET'])
def update_dpmt():
    dict_value = {k:request.form[k] for k in request.form.keys() if len(request.form[k])!=0}
    # department =  #dictionary to get list of all departments, hod and corresponding weekly off in a tuple or list. {department: [Hod, weekly off]}
    #department_name_list =
    #department_dict =
    print(dict_value)
    return render_template('updateDepartment.html',
        # department_name_list = department_name_list,
        # department_dict = department_dict,
                )

@app.route('/update_dpmt_details',  methods=['POST', 'GET'])
def update_details_dpmt():
    dict_value = {k:request.form[k] for k in request.form.keys() if len(request.form[k])!=0} #in this you will find each and every non-empty inputs of the form
    print(dict_value)
    dpmt_name=''  # will be a list if the user search on the basis of employee name. Need to handle over here such that in case of a single person it should
                # pass a string else it should pass a list.
    wklyoff=''
    flash('Department Updated successfully!!')
    return render_template('updateDepartment.html',
        # department_name_list = department_name_list,
        # department_dict = department_dict,
                )

                        
if __name__ == "__main__":
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.run(host="127.0.0.1", port=8000, debug=True, threaded=True)
    #serving.run_simple("0.0.0.0",5000,app,ssl_context=("server.crt","server.key"))
    #print(list(request.form.keys()))
