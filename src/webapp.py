from flask import Flask, request, render_template, send_file, redirect, session,\
                  url_for, send_from_directory, Response, make_response, jsonify, flash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from werkzeug.utils import secure_filename
import base64, os, sys, cv2, time, glob, cv2
import numpy as np, pandas as pd
from multidict import MultiDict
# from .face_creation import crop_faces, create_descriptor
from .load_config import CONFIG
from .webapp_utils import User, memory_container, is_known_user, encrypt,\
                          get_user_info,   search_by,\
                          update_status_details,  get_alerts, get_camera_list, get_roster, add_operator,\
                            update_password,\
                          get_shift_timing, update_employee_shift, add_roster, generate_action_tesa_report, get_department, get_status_list, update_employee_department, get_weekdays, get_locations, add_department, get_dept_people, update_department, add_location, get_category, add_category,download_cam_logs_report, download_workhour_logs_report, download_daily_report, download_monthly_report, update_employee_name



#run_video_recognition,generate_report,get_video_list\
from datetime import datetime, date as datemodule, timedelta
import inspect
import sys, json
sys.setrecursionlimit(10000) # remove dependency on flask-login and remove this line.

TEMPLATE_FOLDER = CONFIG['GUI']['gui_template_path']
FAV_ICON = CONFIG['GUI']['fav_icon']
ACTIVE_ICON = CONFIG['GUI']['active_icon']
DEACTIVE_ICON = CONFIG['GUI']['deactive_icon']
SHUTDOWN_ICON = CONFIG['GUI']['shutdown_icon']
HOME_ICON = CONFIG['GUI']['home_icon']
FACE_IMG_FOLDER = CONFIG['DATA']['face_img_path']
MAX_DISPLAY_ROWS = 100


FACE_DB_PATH = CONFIG['DB']['face_db']
app = Flask(__name__, template_folder=TEMPLATE_FOLDER, root_path=CONFIG['COMMON']['base_path'])

login_manager = LoginManager()
login_manager.init_app(app)

user_container = dict()

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
    for dc in person_details:
        user_id, user_name, threat_type, shift_id, deptid= dc.empid, dc.name,dc.empstatus,dc.currshift, dc.currdept
        image_partial_name = face_details[user_id]

        images = []
        for i in image_partial_name:
            search_path = os.path.join(CONFIG['DATA']['face_img_path'], f'{i}.*')
            fnames = glob.glob(search_path)

            if len(fnames) > 0:
                ext = fnames[0].split('.')[-1]
                images.append(f'{i}.{ext}')
        details_for_display.append([user_id, user_name, threat_type, get_shift_timing(shift_id), images,get_department(deptid)])
    
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
    
    if filename == 'bs-css':
        fname = os.path.join(TEMPLATE_FOLDER, 'css', 'bootstrap.min.css')
    
    if filename == 'logo':
        fname = CONFIG['RECOGNITION']['display_logo']
    
    if filename == 'bootstrap.min.css.map':
        fname = os.path.join(TEMPLATE_FOLDER, 'css', 'bootstrap.min.css.map')
    
    if filename == 'bs-js':
        fname = os.path.join(TEMPLATE_FOLDER, 'js', 'bootstrap.js')
    
    if filename == 'popper':
        fname = os.path.join(TEMPLATE_FOLDER, 'js', 'popper.min.js')
    
    if filename == 'jq':
        fname = os.path.join(TEMPLATE_FOLDER, 'js', 'jquery-3.2.1.slim.min.js')
    
    if filename == 'bootstrap.js.map':
        fname = os.path.join(TEMPLATE_FOLDER, 'js','bootstrap.js.map')
        
    if filename == 'mjq':
        fname = os.path.join(TEMPLATE_FOLDER, 'js', 'jquery.multiselect.js')
    
    if filename == 'mcss':
        fname = os.path.join(TEMPLATE_FOLDER, 'css', 'jquery.multiselect.css')


    if filename == 'jquery-3.3.1.js':
        fname = os.path.join(TEMPLATE_FOLDER, 'js', 'jquery-3.3.1.js')
    
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

@app.route('/home', methods=['POST', 'GET'])
@login_required
def go_home():
	return return_home_page(current_user)


@app.route('/enroll_operator')
@login_required
def show_enroll_operator_page():
    operator = current_user
    return render_template('enroll_operator.html',
                           logged_in=True,
                           operator_id=operator.id,
                           is_admin=operator.is_admin)

@app.route('/search_modify_operator')
@login_required
def search_modify_operator_page():
    operator = current_user
    return render_template('search_modify_operator.html',
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)

@app.route('/enroll_user')
@login_required
def show_enroll_user_page():
    operator = current_user
    return render_template('enroll_user.html',
                           logged_in=True,
                           operator_id=operator.id,
                           is_admin=operator.is_admin,
                           rosters=get_roster(), categories = get_status_list(), departments = get_department())

@app.route('/search_modify_user')
@login_required
def show_search_modify_user_page():
    operator = current_user
    return render_template('search_modify_user.html',
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)

#CHANGED
@app.route('/show_logs')
@login_required
def show_logs_page():
    operator = current_user
    
    return render_template('printReport.html',
                           logged_in=True,
                           operator_id=operator.id,
                           is_admin=operator.is_admin)

#     end_date = datemodule.today()
#     start_date = end_date
#     camera_list = get_camera_list()

#     return render_template('show_logs_form.html',
#                             start_date=start_date,
#                             end_date=end_date,
#                             camera_list=get_processed_tuple(camera_list),
#                             logged_in=True,
#                             operator_id=operator.id,
#                             is_admin=operator.is_admin)

# @app.route('/show_video_logs')
# @login_required
# def show_video_logs_page():
#     operator = current_user

#     end_date = datemodule.today()
#     start_date = end_date
#     video_list = get_video_list()

#     return render_template('show_video_logs_form.html',
#                             start_date=start_date,
#                             end_date=end_date,
#                             video_list=get_processed_tuple(video_list),
#                             logged_in=True,
#                             operator_id=operator.id,
#                             is_admin=operator.is_admin)

@app.route('/show_alerts')
@login_required
def show_alert_page():
    operator = current_user
    end_date = datemodule.today()
    start_date = end_date

    return render_template('show_alerts_form.html',
                            start_date=start_date,
                            end_date=end_date,
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)

@app.route('/show_roster')
@login_required
def show_roster_page():
    operator = current_user
    roster_details = get_roster()
    name = [(str(roster_details[i][1]).split(' ('))[0] for i in range(len(roster_details))]
    weekdays_list = get_weekdays()
    rname = json.dumps(name)
    return render_template('roster.html',
                            name=rname,weekdays_list = weekdays_list,
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)

############# Webapp/login Functions ###############################

@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form.get('operatorid')
        password = request.form.get('password')
        user_password, user_role = get_user_info(username)
        if user_password is None:
            flash('User not registered!!')
            return render_template('login.html', logged_in=False)
        elif (encrypt(password) == user_password):
            user = User()
            user.id = username
            user.set_authenticated(True)
            user.set_admin(user_role == CONFIG['USERTYPE']['admin'])
            login_user(user)
            return return_home_page(user, add=True)
        else:
            flash('Authentication Failed!!')
            return render_template('login.html', logged_in=False)

@login_manager.user_loader
def user_loader(username):
    if not is_known_user(username):
        return
    
    if '_tracker_id' in session:
        if session['_tracker_id'] in user_container:
            return user_container[session['_tracker_id']]

    return

@login_manager.request_loader
def request_loader(request):

    username = request.form.get('username')

    if not is_known_user(username):
        return
    
    password = request.form.get('password')
    user_password, user_role = get_user_info(username)
    
    user = User()
    user.id = username
    user.set_authenticated(encrypt(password) == user_password)
    user.set_admin(user_role == CONFIG['USERTYPE']['admin'])

    return user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'

@app.route('/logout')
def logout():

    logout_user()
    
    if '_tracker_id' in session:
        tid = session.pop('_tracker_id')
        user_container.pop(tid)

    return render_template('login.html', logged_in=False)

#################### webapp/operator action functions #####

@app.route('/operator/enroll', methods=['POST'])
@login_required
def enroll_operator():
    
    operator = current_user
    # print('Operator entry: ', operator.is_admin)

    if operator.is_admin:
        
        new_operator_id = request.form['oid']
        new_operator_pass = request.form['opass']
        new_operator_confirm_pass = request.form['ocpass']
        operator_first_name = request.form['ofname']
        operator_second_name = request.form['osname']
        operator_last_name = request.form['olname']
        operator_role = request.form['orole']

        if new_operator_pass == new_operator_confirm_pass:
            
            operator_name_part = []

            for name_part in [operator_first_name, operator_second_name, operator_last_name]:
                if len(name_part) > 0:
                    operator_name_part.append(name_part)

            operator_name = ' '.join(operator_name_part)

            encrypted_password = encrypt(new_operator_pass)
            val = add_operator(new_operator_id, encrypted_password, operator_name, operator_role)
            if val:
                flash('Operator enrolled successfully!!')
            else:
                flash('Operator id exists!!')
        else:
            flash('Password did not match!!')

        return show_enroll_operator_page()
    else:
        return logout()

@app.route('/operator/change/password', methods=['POST', 'GET'])
@login_required
def change_password():
    operator = current_user

    if request.method == 'POST':
        old_passwd = request.form['oldpasswd']
        new_passwd = request.form['newpasswd']
        cnf_passwd = request.form['cnfpasswd']

        if new_passwd == cnf_passwd:
            user_password, _ = get_user_info(operator.id)
            if user_password == encrypt(old_passwd):
                status = update_password(operator.id, encrypt(new_passwd))
                if status:
                    flash('Password change successful.')
                    return logout()
                else:
                    flash('Password change failed!!')
            else:
                flash('Old password is wrong!!')
        else:
            flash('Confirm password did not matched!!')

    return render_template('change_password.html',
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)


#################### webapp/user_enrollment functions #########

#################### webapp/serach_user functions ##############

##################### webapp/logs_and_alerts functions #########

@app.route('/show/logs', methods=['POST'])
@login_required
def show_logs():

    operator = current_user

    user_id = request.form['lrid']
    user_name = request.form['lrname']

    if user_id == '':
        user_id = None
    
    if user_name == '':
        user_name = None
    
    start_date = request.form['startdate']
    end_date = request.form['enddate']
    location = request.form['location'].replace('|', ' ')
    recog_mode = 'online'#request.form['recog_mode']

    if location == 'ALL':
        location = None
    
    #path, online_data, offline_data = generate_report(user_list=user_id,
    #                                                  user_name=user_name,
    #                                                  start_date=start_date,
    #                                                  end_date=end_date,
    #                                                  location=location,
    #                                                  info='home_',
    #                                                  mode=recog_mode)

    path, online_data = generate_action_tesa_report(user_list=user_id,
                                                    user_name=user_name,
                                                    start_date=start_date,
                                                    end_date=end_date,
                                                    location=location,
                                                    info='home_')

    online_columns = online_data.columns.tolist()
    online_values = online_data.values.astype(np.str)
    #offline_columns = offline_data.columns.tolist()
    #offline_values = offline_data.values.astype(np.str)

    file_basename = os.path.basename(path)

    if online_values.shape[0] > MAX_DISPLAY_ROWS:
        online_values = online_values[:MAX_DISPLAY_ROWS]
        flash(f'[Online Logs]: Displaying {MAX_DISPLAY_ROWS} only. For full logs, download logs.')

    #if offline_values.shape[0] > MAX_DISPLAY_ROWS:
    #    offline_values = offline_values[:MAX_DISPLAY_ROWS]
    #    flash(f'[Video Recognition Logs]: Displaying {MAX_DISPLAY_ROWS} only. For full logs, download logs.')

    return render_template('show_log_report.html',
                            online_columns=online_columns,
                            online_values=online_values,
                            #offline_columns=offline_columns,
                            #offline_values=offline_values,
                            mode=recog_mode,
                            download_file=file_basename,
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)
    


@app.route('/show/alerts', methods=['POST'])
@login_required
def show_alerts():
    
    operator = current_user

    start_date = request.form['startdate']
    end_date = request.form['enddate']

    path, all_records, unique_user_ids = get_alerts(start_date, end_date)

    columns = all_records.columns.tolist()
    values = all_records.values.astype(str)
    file_basename = os.path.basename(path)

    _unique_user_ids = []
    _uids = []
    colsize = 4

    for i in range(len(unique_user_ids)):
        if (i+1)%colsize == 0:
            _unique_user_ids.append(_uids)
            _uids = []
        else:
            _uids.append(unique_user_ids[i])
    
    if len(_uids) > 0:
        _unique_user_ids.append(_uids)
    
    return render_template('show_alerts.html',
                            start_date=start_date,
                            end_date=end_date,
                            columns=columns,
                            values=values,
                            download_file=file_basename,
                            unique_user_ids=_unique_user_ids,
                            colsize=colsize,
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)


@app.route('/show/alerts/users', methods=['POST'])
@login_required
def indiv_alert():
    
    operator = current_user

    start_date = request.form['startdate']
    end_date = request.form['enddate']

    values = []
    for u in request.form:
        if u not in ['startdate', 'enddate']:
            person_details, face_details = search_by(u, user_id=True, exact=True)
            details_to_display = get_details_for_display(person_details, face_details)
            path, all_records, _ = get_alerts(start_date, end_date, user_id=u)
            top_index = all_records['datetime'].map(pd.to_datetime).sort_values(ascending=False).index[0]

            latest_time = '.'.join(str(all_records.loc[top_index, 'datetime']).split('.')[:-1])
            last_location = all_records.loc[top_index, 'location']

            all_records.drop('alertid', axis=1, inplace=True)

            colnames = all_records.columns.tolist()
            data = all_records.values.astype(np.str)
            basepath = os.path.basename(path)
            values.append(details_to_display[0] + [latest_time, last_location, basepath, colnames, data])
            
    # print(colnames, values)
    
    return render_template('show_indiv_alerts.html',
                           values=values,
                           logged_in=True,
                           operator_id=operator.id,
                           is_admin=operator.is_admin)



##################### webapp/control panel functions ##################
@app.route('/shutdown', methods=['POST', 'GET'])
@login_required
def shutdown():
    memory_container['control_panel'].stop_webapp()
    return logout()

@app.route('/control', methods=['POST', 'GET'])
@login_required
def show_control_panel():
    
    operator = current_user
    control_panel = memory_container['control_panel']
    camera_ids = memory_container['camera_ids']

    if 'update' in request.form:
        
        # print(request.form)
        if request.form['shutdown_system'] == 'y':
            if not control_panel.is_close_all():
                control_panel.set_close_all()
                for cam_id in camera_ids:
                    control_panel.stop_display(cam_id)
                    control_panel.stop_recognition(cam_id)
                    control_panel.stop_monitor()
            else:
                control_panel.unset_close_all()
                for cam_id in camera_ids:
                    control_panel.start_recognition(cam_id)

        if request.form['all_display'] == 'y':

            any_display = False
            for cam_id in camera_ids:
                any_display = any_display or control_panel.should_display(cam_id)
            
            if any_display:
                control_panel.stop_all_display()
            else:
                control_panel.start_all_display()
        
        if request.form['monitor'] == 'y':
            if control_panel.should_display_monitor():
                control_panel.stop_monitor()
            else:
                control_panel.start_monitor()
        
        else:
            for cam_id in camera_ids:
                camera_name = control_panel.get_camera_name(cam_id)
                if request.form[f'{camera_name}_display'] == 'y':
                    if control_panel.should_display(cam_id):
                        control_panel.stop_display(cam_id)
                    else:
                        control_panel.start_display(cam_id)
                        
        if request.form['announcement'] == 'y':
            if control_panel.get_announcement():
                control_panel.reset_announcement()
            else:
                control_panel.set_announcement()
    
            
        if request.form['all_recognize'] == 'y':

            any_recognition = False
            for cam_id in camera_ids:
                any_recognition = any_recognition or control_panel.should_recognize(cam_id)

            if any_recognition:
                control_panel.stop_all_recognition()
            else:
                control_panel.start_all_recognition()
        else:
            for cam_id in camera_ids:
                camera_name = control_panel.get_camera_name(cam_id)
                if request.form[f'{camera_name}_recognition'] == 'y':
                    if control_panel.should_recognize(cam_id):
                        control_panel.stop_recognition(cam_id)
                    else:
                        control_panel.start_recognition(cam_id)

    camera_states = []
    any_display = False
    any_recognition = False
    for cam_id in camera_ids:
        any_display = any_display or control_panel.should_display(cam_id)
        any_recognition = any_recognition or control_panel.should_recognize(cam_id)
        camera_state = [
            control_panel.get_camera_name(cam_id),
            control_panel.should_display(cam_id),
            control_panel.should_recognize(cam_id)
        ]
        camera_states.append(camera_state)

    return render_template('control_panel.html',
                            shutdown_system=control_panel.is_close_all(),
                            any_display=any_display,
                            any_recognize=any_recognition,
                            monitor_state=control_panel.should_display_monitor(),announcement_state=control_panel.get_announcement(),
                            camera_states=camera_states,
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)


######################## webapp/roster ##########################################

@app.route('/roster', methods=['POST'])
@login_required
def add_roster_details():

    roster_details = get_roster()
    #static_num = [int((roster_details[i][0])) for i in range(len(roster_details)) if len((str(roster_details[i][1]).split(' ('))[1]) != 4] #getting number of static rosters ids
    # dynamic_num = [((roster_details[i][0])[1:]) for i in range(len(roster_details)) if len((str(roster_details[i][1]).split(' ('))[1]) == 4]

    static_num = []
    for _res in roster_details:
        if _res[0] != 'D':
            static_num.append(int(_res[0]))

    rname = request.form['rname'].lower()
    # start_time = request.form['start_time']
    # end_time = request.form['end_time']
    s_time = request.form['start_time'].split(":")
    e_time = request.form['end_time'].split(":")
    start_time = int(s_time[0])+(int(s_time[1])/60)
    end_time = int(e_time[0])+(int(e_time[1])/60)

    
    rwkly_off = request.form['weekdaydropdown']
    
    # if len(dynamic_num) == 0:
    #     ri = f'D'
    #     end_tim = 9
    #     start_tim = 0
    #     name = 'Dynamic'
    #     add_roster(ri, name, start_tim, end_tim)
    
    if len(static_num) == 0:
        rid = 1
    else:
        rid = static_num[-1]+1

    rid = str(rid)#.zfill(3)
    start_time = int(start_time)*3600
    end_time = (int(end_time))*3600
    if end_time==0:
        end_time=24*3600
    
    # print(rid, rname, start_time, end_time, rwkly_off)
    x = add_roster(rid, rname, start_time, end_time, rwkly_off) 

    if x==True:
        flash('Roster added successfully!!')
    elif x==False:
        flash('Roster addition failed.')
    elif x==-1:
        flash("Shift name already exists. Enter another name.")
    return show_roster_page()


#######################ADDITIONAL FEATURES ACTION TESA#########################
#finished till here
@app.route('/reports', methods=['POST', 'GET'])
def print_reports():
    
    operator = current_user
    # if request.form.keys():
    keys = [k for k in request.form.keys()]
    # print(keys)
    # shift = #fetch all of the shifts names from db
    # department = #fetch all of the department names from db
    shift_list = get_roster()
    department_list = get_department()
    if 'cam_log' in keys:
        return render_template('printCamLog.html',
                               logged_in=True,
                               shifts = shift_list,
                               departments = department_list,
                               operator_id=operator.id,
                               is_admin=operator.is_admin)
    elif 'wrk_hrs_log' in keys:
        return render_template('printWorkHrsLog.html',
                               logged_in=True,
                               shifts = shift_list,
                               departments = department_list,
                               operator_id=operator.id,
                               is_admin=operator.is_admin)
    elif 'dly_rprt' in keys:
        return render_template('printDailyLog.html',
                               logged_in=True,
                               shifts = shift_list,
                               departments = department_list,
                               operator_id=operator.id,
                               is_admin=operator.is_admin)
    elif 'mnthly_rprt' in keys:
        return render_template('printMonthlyLog.html',
                               logged_in=True,
                               shifts = shift_list,
                               departments = department_list,
                               operator_id=operator.id,
                               is_admin=operator.is_admin)
    else:
        return render_template('printReport.html',
                               logged_in=True,
                               operator_id=operator.id,
                               is_admin=operator.is_admin)

@app.route('/reports/wrk_hr_logs', methods=['POST', 'GET'])
def print_wrk_hrs_log():
    
    operator = current_user
    
    final_data_for_filter = dict()
    if request.form.keys():
        dict_value = {k:request.form.getlist(k) for k in request.form.keys() if len(request.form[k])!=0}
        # print("printcamdict",dict_value)
        li = ['emp_id', 'cam_logs']
        for key in li:
            if key in dict_value.keys():
                del dict_value[key]
        # print("printcamdict",dict_value)
        count = 0
        if ('start_ent' in dict_value.keys() and 'end_ent' in dict_value.keys()):
            # print('ss')
            count+=1
            final_data_for_filter["start_ent"] = dict_value["start_ent"]
            final_data_for_filter["end_ent"] = dict_value["end_ent"]
            
        if 'empid' in dict_value.keys():
            final_data_for_filter['emp_ids']=None
            final_data_for_filter['emp_ids'] = dict_value['empid'][0].split(';')
            count+=1
            # print('yy')
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
        # print(count)
     
    # print("final data", final_data_for_filter)
    data = final_data_for_filter
    res = None
    start_ent =  data.get("start_ent", None)
    end_ent = data.get('end_ent', None)
    start_date = data.get('from_date',None)
    end_date = data.get('to_date', None)
    emp_ids = data.get('emp_ids', None)
    emp_names = data.get('emp_name', None)
    shifts = data.get('shift', None)
    departments = data.get('dpmt', None)
    
    if shifts:
        shifts=[i.split(" (")[0] for i in shifts]
        
    if departments:
        departments=[i.split(" (")[0] for i in departments]
    
    #final data {'start_ent': ['0'], 'end_ent': ['100'], 'shift': ['D', '2'], 'dpmt': ['1', '4'],'from_date': '2022-01-06', 'to_date': '2022-01-01'}
    
    #{'start_ent': ['0'], 'end_ent': ['100'], 'emp_ids': ['1', '2', '3'], 'emp_name': ['ab', 'poojith']}
    path, online_data= None, None
    
    try:
        path, online_data=download_workhour_logs_report( user_list = emp_ids, user_name = emp_names, shifts = shifts, departments = departments, start_date= start_date, end_date = end_date, total_rows = -1)
    except Exception as e:
        print(e)
        flash('Error')
        return print_reports()
    
    if path == -1:
        flash(f'End Time is before Start time')
        return print_reports()
    elif path==-2:
        flash(f'No log found')
        return print_reports()

    online_columns = online_data.columns.tolist()
    online_values = online_data.values.astype(np.str)
    #offline_columns = offline_data.columns.tolist()
    #offline_values = offline_data.values.astype(np.str)

    file_basename = os.path.basename(path)

    if online_values.shape[0] > MAX_DISPLAY_ROWS:
        online_values = online_values[:MAX_DISPLAY_ROWS]
        flash(f'[Online Logs]: Displaying {MAX_DISPLAY_ROWS} only. For full logs, download logs.')

    name = 'WORK HOUR LOGS'
    return render_template('show_log_report.html',
                            online_columns=online_columns,
                            online_values=online_values,
                            #offline_columns=offline_columns,
                            #offline_values=offline_values,
                            mode='online',name = name,
                            download_file=file_basename,
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)
        
    
    
    return print_reports()

@app.route('/reports/cam_logs', methods=['POST', 'GET'])
def print_cam_logs():
    
    operator = current_user
    
    final_data_for_filter = dict()
    if request.form.keys():
        dict_value = {k:request.form.getlist(k) for k in request.form.keys() if len(request.form[k])!=0}
        # print("printcamdict",dict_value)
        li = ['emp_id', 'cam_logs']
        for key in li:
            if key in dict_value.keys():
                del dict_value[key]
        # print("printcamdict",dict_value)
        count = 0
        if ('start_ent' in dict_value.keys() and 'end_ent' in dict_value.keys()):
            # print('ss')
            count+=1
            final_data_for_filter["start_ent"] = dict_value["start_ent"]
            final_data_for_filter["end_ent"] = dict_value["end_ent"]
            
        if 'empid' in dict_value.keys():
            final_data_for_filter['emp_ids']=None
            final_data_for_filter['emp_ids'] = dict_value['empid'][0].split(';')
            count+=1
            # print('yy')
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
        # print(count)
     
    # print("final data", final_data_for_filter)
    data = final_data_for_filter
    res = None
    start_ent =  data.get("start_ent", None)
    end_ent = data.get('end_ent', None)
    start_date = data.get('from_date',None)
    end_date = data.get('to_date', None)
    emp_ids = data.get('emp_ids', None)
    emp_names = data.get('emp_name', None)
    shifts = data.get('shift', None)
    departments = data.get('dpmt', None)
    
    if shifts:
        shifts=[i.split(" (")[0] for i in shifts]
        
    if departments:
        departments=[i.split(" (")[0] for i in departments]
    
    #final data {'start_ent': ['0'], 'end_ent': ['100'], 'shift': ['D', '2'], 'dpmt': ['1', '4'],'from_date': '2022-01-06', 'to_date': '2022-01-01'}
    
    #{'start_ent': ['0'], 'end_ent': ['100'], 'emp_ids': ['1', '2', '3'], 'emp_name': ['ab', 'poojith']}
    path, online_data=None,None
    try:
        path, online_data=download_cam_logs_report( user_list = emp_ids, user_name = emp_names, shifts = shifts, departments = departments, start_date= start_date, end_date = end_date, total_rows = -1)
    except Exception as e:
        print(e)
        flash('Error')
        return print_reports()
    
    if path == -1:
        flash(f'End Time is before Start time')
        return print_reports()
    elif path==-2:
        flash(f'No log found')
        return print_reports()

    online_columns = online_data.columns.tolist()
    online_values = online_data.values.astype(np.str)
    #offline_columns = offline_data.columns.tolist()
    #offline_values = offline_data.values.astype(np.str)

    file_basename = os.path.basename(path)

    if online_values.shape[0] > MAX_DISPLAY_ROWS:
        online_values = online_values[:MAX_DISPLAY_ROWS]
        flash(f'[Online Logs]: Displaying {MAX_DISPLAY_ROWS} only. For full logs, download logs.')

    name = 'CAMERA LOGS'
    return render_template('show_log_report.html',
                            online_columns=online_columns,
                            online_values=online_values,
                            #offline_columns=offline_columns,
                            #offline_values=offline_values,
                            mode='online',name = name,
                            download_file=file_basename,
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)

@app.route('/reports/daliy_logs', methods=['POST', 'GET'])
def print_dly_logs():
    operator = current_user
    
    final_data_for_filter = dict()
    dict_value= None
    if request.form.keys():
        dict_value = {k:request.form.getlist(k) for k in request.form.keys() if len(request.form[k])!=0}
        # print("printcamdict",dict_value)
        li = ['emp_id', 'cam_logs']
        for key in li:
            if key in dict_value.keys():
                del dict_value[key]
        # print("printcamdict",dict_value)
        count = 0
        if ('start_ent' in dict_value.keys() and 'end_ent' in dict_value.keys()):
            # print('ss')
            count+=1
            final_data_for_filter["start_ent"] = dict_value["start_ent"]
            final_data_for_filter["end_ent"] = dict_value["end_ent"]
            
        if 'empid' in dict_value.keys():
            final_data_for_filter['emp_ids']=None
            final_data_for_filter['emp_ids'] = dict_value['empid'][0].split(';')
            count+=1
            # print('yy')
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

    # print("final data", final_data_for_filter)
    data = final_data_for_filter
    res = None
    start_ent =  data.get("start_ent", None)
    end_ent = data.get('end_ent', None)
    start_date = data.get('from_date',None)
    end_date = data.get('to_date', None)
    emp_ids = data.get('emp_ids', None)
    emp_names = data.get('emp_name', None)
    shifts = data.get('shift', None)
    departments = data.get('dpmt', None)

    if 'fi_lo' in dict_value.keys():
        first_in_last_out = True
    else:
        first_in_last_out = False 

    # print("first_in_last_out daily: ", first_in_last_out)

    if shifts:
        shifts=[i.split(" (")[0] for i in shifts]
        
    if departments:
        departments=[i.split(" (")[0] for i in departments]

    li_key_report= ['lc', 'el', 'mp', 'absent', 'gw', 'present', 'hlf_day', 'full_day_leave','weeklyoff','comp_hldy','dept_hldy']
    li_specific_report=[]
    for k in dict_value.keys():
        if k in li_key_report:
            li_specific_report.append(dict_value[k][0])
    # li_specific_report = [dict_value[k] for k in dict_value.keys() if k in li_key_report]
    # print("lispeficreport",li_specific_report)
    path, online_data=None,None
    try:
        path, online_data=download_daily_report( user_list = emp_ids, user_name = emp_names, shifts = shifts, departments = departments, start_date= start_date, end_date = end_date, total_rows = -1,status_list = li_specific_report, first_in_last_out = first_in_last_out)
    except Exception as e:
        print(e)
        flash('Error')
        return print_reports()
    
    if path == -1:
        flash(f'End Time is before Start time')
        return print_reports()
    elif path==-2:
        flash(f'No log found')
        return print_reports()

    online_columns = online_data.columns.tolist()
    online_values = online_data.values.astype(np.str)
    #offline_columns = offline_data.columns.tolist()
    #offline_values = offline_data.values.astype(np.str)

    file_basename = os.path.basename(path)

    if online_values.shape[0] > MAX_DISPLAY_ROWS:
        online_values = online_values[:MAX_DISPLAY_ROWS]
        flash(f'[Online Logs]: Displaying {MAX_DISPLAY_ROWS} only. For full logs, download logs.')

    name = 'DAILY REPORT'
    return render_template('show_log_report.html',
                            online_columns=online_columns,
                            online_values=online_values,
                            #offline_columns=offline_columns,
                            #offline_values=offline_values,
                            mode='online',name = name,
                            download_file=file_basename,
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)

    return print_reports()

@app.route('/reports/display', methods=["POST", "GET"])
def monthly_table_display():

    operator = current_user
    # session_id = session['_id']
    # limit_cols	= 50 #configurable. Can be included in config file if required
    # send_rows = [] #data to be displayed goes in a list
    # column_name_map_send = [] name of the columns to be displayed
    # for row in df.values:
    # 	send_rows.append(list(zip(column_name_map_send, row[:limit_cols]))) 
    # print("table display")
    
    data = operator.remove_work("monthly_report")
    # online_columns, online_values = data[0], data[1]

    return render_template('table_display.html', 
                           online_columns = data[0],
                           online_values = data[1],
                           logged_in=True, 
                           operator_id=operator.id, 
                           is_admin=operator.is_admin)

@app.route('/reports/monthly_logs', methods=['POST', 'GET'])
def print_mnthly_logs():
    operator = current_user
    
    final_data_for_filter = dict()
    dict_value= None
    if request.form.keys():
        dict_value = {k:request.form.getlist(k) for k in request.form.keys() if len(request.form[k])!=0}
        # print("printcam dict monthly",dict_value)
        li = ['emp_id', 'cam_logs']
        for key in li:
            if key in dict_value.keys():
                del dict_value[key]
        # print("printcamdict",dict_value)
        count = 0
        if ('start_ent' in dict_value.keys() and 'end_ent' in dict_value.keys()):
            # print('ss')
            count+=1
            final_data_for_filter["start_ent"] = dict_value["start_ent"]
            final_data_for_filter["end_ent"] = dict_value["end_ent"]
            
        if 'empid' in dict_value.keys():
            final_data_for_filter['emp_ids']=None
            final_data_for_filter['emp_ids'] = dict_value['empid'][0].split(';')
            count+=1
            # print('yy')
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
        # if 'from_date' in dict_value.keys() and 'to_date' in dict_value.keys():
        #     final_data_for_filter['from_date']=None
        #     final_data_for_filter['from_date'] = dict_value['from_date'][0]
        #     final_data_for_filter['to_date']=None
        #     final_data_for_filter['to_date'] = dict_value['to_date'][0]
            # count+=1
        # print(count)
     
    # print("final data", final_data_for_filter)
    data = final_data_for_filter
    res = None
    start_ent =  data.get("start_ent", None)
    end_ent = data.get('end_ent', None)
    # start_date = data.get('from_date',None)
    # end_date = data.get('to_date', None)
    emp_ids = data.get('emp_ids', None)
    emp_names = data.get('emp_name', None)
    shifts = data.get('shift', None)
    departments = data.get('dpmt', None)
    
    if shifts:
        shifts=[i.split(" (")[0] for i in shifts]
        
    if departments:
        departments=[i.split(" (")[0] for i in departments]


    if 'fi_lo' in dict_value.keys():
        first_in_last_out = True
    else:
        first_in_last_out = False 

    # print("first_in_last_out monthly: ", first_in_last_out)

    # li_key_report= ['lc', 'el', 'mp', 'absent', 'gw', 'present', 'hlf_day', 'full_day_leave','weeklyoff','comp_hldy','dept_hldy']
    # li_specific_report=[]
    # for k in dict_value.keys():
    #     if k in li_key_report:
    #         li_specific_report.append(dict_value[k][0])
    # print("lispeficreport",li_specific_report)
    
    li_mon = ['month', 'year']
    selected_month = dict_value.get('month',None)
    selected_year = dict_value.get('year',None)
    #{k:dict_value[k][0] for k in dict_value.keys() if k in li_mon}
    # print("year and month",selected_year, selected_month)
    if not selected_year:
        selected_year = datemodule.now().year
    else:
        selected_year = int(selected_year[0])
    if not selected_month:
        selected_month = datemodule.now().month
    else:
        selected_month = int(selected_month[0])+1
    # print("year and month",selected_year, selected_month)
    path, online_data=None,None
    try:
        path, online_data=download_monthly_report( user_list = emp_ids, user_name = emp_names, shifts = shifts, departments = departments, month= selected_month, year = selected_year, total_rows = -1, first_in_last_out = first_in_last_out)
    except Exception as e:
        print(e)
        flash('Error')
        return print_reports()
    
    
    # print("path",path)
    if path == -1:
        flash(f'No log found')
        return print_reports()
    

    # online_columns = []#online_data.columns.tolist()
    # online_values = []#online_data.values.astype(np.str)
    online_columns = online_data.columns.tolist()
    online_values = online_data.values.astype(np.str)
    #offline_columns = offline_data.columns.tolist()
    #offline_values = offline_data.values.astype(np.str)

    file_basename = os.path.basename(path)

    if len(online_values) > MAX_DISPLAY_ROWS:
        online_values = online_values[:MAX_DISPLAY_ROWS]
        flash(f'[Online Logs]: Displaying {MAX_DISPLAY_ROWS} only. For full logs, download logs.')
        
    operator.add_work("monthly_report",[online_columns, online_values])

    name = 'MONTHLY REPORT'
    return render_template('show_monthly_log_report.html',
                            # online_columns=online_columns,
                            # online_values=online_values,
                            #offline_columns=offline_columns,
                            #offline_values=offline_values,
                            mode='online',name = name,
                            download_file=file_basename,
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)


@app.route('/dept')
def details_department():
    operator = current_user
    department_details = get_department()
    code = [(str(department_details[i][1]).split(' ('))[0] for i in range(len(department_details))]
    
    locations = [i[0] for i in get_locations()]
    rcode = json.dumps(code)
    return render_template('department.html', 
                           name=rcode, 
                           locations = locations, 
                           logged_in=True, 
                           operator_id=operator.id, 
                           is_admin=operator.is_admin)
                    

@app.route('/add_dept', methods=['POST', 'GET'])
def add_dept_details():

    # operator = current_user
    dpmt_details = get_roster()

    rname = request.form['rname']
    # rcode = request.form['rcode']
    
    #TODO: ADD CATEGORY HOD to CATEGORY TABLE AND ADD A DROPDOWN LISTING ONLY HODS. ALSO SHOULD CHANGE CHECK CONDITION WHILE SHOWING DETAILS IN ENROLL FACE AND SEARCH AND MODIFY FACE
    rhod = ""#request.form['rhod'].lower()
    rlocation = request.form['locationdropdown']
    # rlocation2 = request.form['locationdropdown'].lower()

    rpushflag = request.form['push_flag']

    # print("add_dept_details: - push_flag = ", rpushflag)
    
    if rname:
        rname = rname.lower().capitalize()
    
    # print("add_dept_details",rname, rlocation, rlocation2)
    
    if not rname:
        flash('Enter Department Name!!')
        return details_department()

    x = add_department(rname, rhod, location = rlocation, pushdata = rpushflag) #change to add department
    # x = add_department(rname, rhod, location = rlocation2)

    if x==True:
        flash('Department added successfully!!')
    elif x==False:
        flash('Department addition failed.')
    elif x==-1:
        flash("Department Name and Location already exists. Choose different Department Name and Location.")

    return details_department()


@app.route('/update',  methods=['POST', 'GET'])
def update_employee():
    # dict_value = {k:request.form[k] for k in request.form.keys() if len(request.form[k])!=0}
    # print(dict_value)
    operator = current_user
    return render_template('updateEmployee.html',
                           logged_in=True,
                           operator_id=operator.id,
                           is_admin=operator.is_admin)

@app.route('/update_details',  methods=['POST', 'GET'])
def update_details_employee():
    operator = current_user
    
    dict_value = {k:request.form[k] for k in request.form.keys()}# if len(request.form[k])!=0}
    separator = ';'
    # print("dict value",dict_value)
    rids =dict_value.get('empid',None)
    rnames=dict_value.get('empname',None) # will be a list if the user search on the basis of employee name. Need to handle over here such that in case of a single person it should
                # pass a string else it should pass a list.
    if not rids:
        rids = []
    else:
        rids = rids.split(separator)
        
    if not rnames:
        rnames = []
    else:
        rnames = rnames.split(separator)
    
    # print("ids, names",rids, rnames)
    
    search_option = dict_value.get('option', None)
    if not search_option:
        search_option = False
    else:
        if search_option == 'exact':
            search_option = True
        else:
            search_option = False
    # print("search option", search_option)    

    person_details, face_details = [],{}

    if len(rnames)>0:
        # person_details, face_details = [],{}
        for rname in rnames:
            a, b = search_by(rname, user_name=True,exact= search_option)
            if len(a) > 0:
                person_details.extend(a)
                face_details.update(b)

    if len(rids)>0:
        # person_details, face_details = [],{}
        for rid in rids:
            a, b = search_by(rid, user_id=True,exact= search_option)
            if len(a) > 0:
                person_details.extend(a)
                face_details.update(b)


    if len(person_details) == 0:
        flash('No such Employee found!!')
        return update_employee()
        
    # print(1,person_details, face_details)
    details_to_display = get_details_for_display(person_details, face_details)
    # operator.add_work('search', {d[0]:d for d in details_to_display})
    ## details_for_display.append([user_id, user_name, threat_type, get_shift_timing(shift_id), images,get_department(deptid)])
    # print(2,details_to_display)
    
    emp_dict = {i[0]:dict() for i in details_to_display}
    for i, key in zip(details_to_display, list(emp_dict.keys())):
        emp_dict[key]['empname'] = i[1]
        emp_dict[key]['emp_dpmt'] = i[5][1].split('(')[0]
        emp_dict[key]['empstatus'] = i[2]
        emp_dict[key]['currshift'] = i[3][0]
        emp_dict[key]['location'] = i[5][1].split('(')[1].split(')')[0]
        emp_dict[key]['deptid'] = i[5][0]

    # print("emp_dict",emp_dict)

    final_emp_dict = dict()

    if search_option == True:
        if len(rids)>0:
            for rid in rids:
                if rid in emp_dict.keys():
                    final_emp_dict[rid] = dict()
                    final_emp_dict[rid] = emp_dict[rid]
        if len(rnames)>0:
            for rname in rnames:
                for rid in emp_dict.keys():
                    if rname.lower() == emp_dict[key]['empname'].lower():
                        final_emp_dict[rid] = dict()
                        final_emp_dict[rid] = emp_dict[rid]
        emp_dict_to_pass = final_emp_dict 
    else:
        emp_dict_to_pass = emp_dict

    # print("dicts final",final_emp_dict, emp_dict_to_pass)
    department_details = get_department()
    status_details = get_status_list()
    location_details = get_locations()
    shift_details = get_roster()

    department = get_department()
    status = [i for i in status_details]
    loc = [i[0] for i in location_details]
    shifts = [(shift_details[i][0]," ".join([(str(shift_details[i][1]).split(' '))[0], (str(shift_details[i][1]).split(' '))[1]])) for i in range(len(shift_details))]

    # print(department,'\n', status, '\n', loc, '\n', shifts)
    # print("emp dict", emp_dict_to_pass)
    operator.add_work('search', emp_dict_to_pass)


    return render_template('updateDetailsEmployee.html',
                           empid=list(emp_dict_to_pass.keys()),
                           department=department,
                           emp_dict=emp_dict_to_pass,
                           status=status,
                           loc=loc,
                           shifts=shifts,
                           logged_in=True,
                           operator_id=operator.id,
                           is_admin=operator.is_admin)

@app.route('/update_details/confirm', methods=['POST'])
@login_required
def confirm_emp_details():
    
    operator = current_user

    if 'reset' in request.form:
        operator.remove_work('register')
        return return_home_page(operator)

    else:
        emp_details_dict = operator.remove_work('search')
        dict_value = {k:request.form[k] for k in request.form.keys() if len(request.form[k])!=0}
        li = ['emp_id', 'cam_logs']
        for key in li:
            if key in dict_value.keys():
                del dict_value[key]
        # print("dict values/new details",dict_value)
        #{'eid': '1', 'empname': 'Sanjay Singh', 'shifts': '2', 'location': 'HAUZ KHAZ', 'status': 'Non-Employee', 'dpmts': changed to id #'operations2 (HAUZ KHAZ) (-)'}
        emp_id  = dict_value.get('eid',None)
        new_name = dict_value.get('empname',None)
        new_shiftid = dict_value.get('shifts',None)
        # new_location = dict_value.get('location',None)
        new_status = dict_value.get('status',None)
        new_deptid = dict_value.get('dpmts',None)
        if new_deptid:
            new_deptid= new_deptid[0]
        
        #emp dict {'1': {'empname': 'sanjay singh', 'emp_dpmt': 'Department1 ', 'empstatus': 'Employee', 'currshift': 'D', 'location': 'punjab'}
        curr_details = emp_details_dict.get(emp_id)
        #TODO ADD NAME CHANGE UTIL IN WEBAPP UTILS
        name = curr_details['empname']
        shift = curr_details['currshift']
        status = curr_details['empstatus']
        deptid = curr_details['deptid']
        # print("old details", curr_details)
        
        departments_to_update = []
        shifts_to_update = []
        categories_to_update = []
        names_to_update = []
        
        # print(status, new_status)
        # print(deptid, new_deptid)
        # print(shift, new_shiftid)
        # print(name, new_name)
        
        #TODO ADD UPDATE NAME FUNCTIONALITY
         # details_for_display.append([user_id, user_name, threat_type, get_shift_timing(shift_id), images,get_department(deptid)])+ for update (new_status, shift updated, dept updated, shit new details , dept new details
        if new_deptid:#isinstance(search_result[k][-1], tuple):
            if status==new_status:#search_result[k][2] == search_result[k][6]:
                # departments_to_update.append([k, search_result[k][-1][0], search_result[k][2], search_result[k][5][0], None])
                departments_to_update.append([emp_id, new_deptid, status, deptid, None])
            else:
                # departments_to_update.append([k, search_result[k][-1][0], search_result[k][2], search_result[k][5][0], search_result[k][6]])
                departments_to_update.append([emp_id, new_deptid, status, deptid, new_status])
            # if search_result[k][2] == search_result[k][6]:
            #     departments_to_update.append([k, search_result[k][-1][0], True])
            # else:
            #     departments_to_update.append([k, search_result[k][-1][0], False])

        if new_status and status!= new_status:#search_result[k][2] != search_result[k][6]:
            if new_deptid:#isinstance(search_result[k][-1], tuple):
                #dept changed
                # categories_to_update.append([k, search_result[k][6], search_result[k][2], search_result[k][5][0], search_result[k][-1][0]])
                categories_to_update.append([emp_id, new_status, status, deptid, new_deptid])
            else:
                # categories_to_update.append([k, search_result[k][6], search_result[k][2], search_result[k][5][0], None])
                categories_to_update.append([emp_id, new_status, status, deptid, None])
        
        if new_shiftid and shift!=new_shiftid:#isinstance(search_result[k][-2], tuple):
            # shifts_to_update.append([k, search_result[k][-2][0]])
            # print(shift,new_shiftid)
            shifts_to_update.append([emp_id, new_shiftid])
            
        if isinstance(new_name,str):
            if len(new_name)>0 and name!=new_name:
                names_to_update.append([emp_id, new_name])
    
        if len(categories_to_update)> 0:
            res = update_status_details(*list(zip(*categories_to_update)))
            if res:
                flash('Category has been successfully modified.')
            else:
                flash('Category modification failed.')
                    
                    
        if len(departments_to_update) > 0:
            res = update_employee_department(*list(zip(*departments_to_update)))
            if res:
                flash('Department has been successfully modified.')
            else:
                flash('Department modification failed.')
          
        if len(shifts_to_update) > 0:
            # print(shifts_to_update) 
            res = update_employee_shift(*list(zip(*shifts_to_update)))
            if res:
                flash('Shift has been successfully modified.')
            else:
                flash('Shift modification failed.')
        
        if len(names_to_update) > 0:
            # print(shifts_to_update) 
            res = update_employee_name(*list(zip(*names_to_update)))
            if res:
                flash('Name has been successfully modified.')
            else:
                flash('Name modification failed.')

        #return return_home_page(operator)

        return update_employee()

@app.route('/update_dpmt',  methods=['POST', 'GET'])
def update_dpmt():
    # dict_value = {k:request.form[k] for k in request.form.keys() if len(request.form[k])!=0}
    # department =  #dictionary to get list of all departments, hod and corresponding weekly off in a tuple or list. {department: [Hod, weekly off]}
    #department_name_list =
    #department_dict =
    # print(dict_value)
    # return render_template('updateDepartment.html',
        # department_name_list = department_name_list,
        # department_dict = department_dict,
                # )
            
    operator = current_user
    # department_dict = {f'{i[0]}-{i[1]}': [f'({i[-2]}-{i[-1]})',i[2]] for i in  get_department(raw= True)}
    department_dict = {f'{i[1]}({i[2]})': [f'({i[-2]}{i[-1]})',i[2],i[0], i[5]] for i in  get_department(raw= True, include_flag = True)}

    department_dict_keys = list(department_dict.keys())
    operator.add_work('updt_dept',department_dict)
    # dict_dept_dict_keys = {i:department_dict_keys[i] for i in range(len(department_dict_keys))}
    dict_dept_dict_keys = {str(i):department_dict_keys[i] for i in range(len(department_dict_keys))}
    operator.add_work('key_dept_dict_key',dict_dept_dict_keys)
    
    print("deparmtent dict", department_dict)
    
    #TODO Add drop down to select hod - list of people of that department
    dept_hod_list = []#get_dept_people(deptid)
    return render_template('updateDepartment.html', 
                           department_dict = department_dict,
                           # department_names = list(department_dict.keys()),
                           department_names = [(i,j) for i,j in dict_dept_dict_keys.items()],
                           department_names_dict = dict_dept_dict_keys,
                           locations = [i[0] for i in get_locations()],
                           hod_list = dept_hod_list,
                           logged_in=True,
                           operator_id=operator.id,
                           is_admin=operator.is_admin)

@app.route('/update_dpmt_details',  methods=['POST', 'GET'])
def update_details_dpmt():
    
    operator = current_user
    
    dict_value = {k:request.form[k] for k in request.form.keys() if len(request.form[k])!=0} #in this you will find each and every non-empty inputs of the form
    # print("dictvalue",dict_value)
    # dpmt_name=''  # will be a list if the user search on the basis of employee name. Need to handle over here such that in case of a single person it should
    #             # pass a string else it should pass a list.
    # wklyoff=''
    # print("location", request.form["dlocations"])
    department = dict_value.get("dpmts",None)
    new_location = dict_value.get("dlocations",None)
    new_name = dict_value.get("dname",None)
    hod = None#request.form("hods")
    pushdata = dict_value.get("push_flag")


    print("update_details_dpmt: - pushdata ", pushdata)
    
    # print(1, request.form["dpmts"])
    
    # print("dict value", dict_value)
    
    department_dict = operator.remove_work('updt_dept')
    dict_dept_dict_keys = operator.remove_work('key_dept_dict_key')
    
    if department:
        # department = dict_dept_dict_keys[int(department)]
        department = dict_dept_dict_keys[str(department)]

    if not new_location:
        new_location = None
        
    if not new_name:
        new_name = None
    else:
        new_name=new_name.lower().capitalize()
    
    location, deptid = None, None
    if department:
        # department = department
        # name, curloc = department[0], department[1]
        department_details = department_dict[department]#get_dept_id(name, curloc)
        deptid, location = department_details[-2], department_details[-3]
        # print("deptid", deptid)
        
    print("details",department,location,hod, deptid, new_name, new_location)
    
    
    res = None
        
    if not department or (not new_name and not new_location and not pushdata):#get better logic for push flag
        res= -2
    else:
        res = update_department([deptid], [new_name], [new_location], [hod], check_for_update=True, pushdata = (True, pushdata))
        
    # if department and (not new_name and not new_location):
    #     if pushdata == "y":
    #         flash("Data will be pushed to HRMS DB for this department")
    #     else:
    #         flash("Data will NOT be pushed to HRMS DB for this department")

    # print(res)
    if res==-1:
        flash('Department Name and Location Already exists. Try Another Name and Location')
    elif res == -2:
        flash('Update info provided is not sufficient!!')
    elif res:
        flash('Department Updated successfully!!')
    else:
        flash('Department Update failed!!')
        
    return update_dpmt()


@app.route('/cat')
def details_category():
    operator = current_user
    category_details = get_category()
    # print(category_details)
    cname = [(category_details[i][0]) for i in range(len(category_details))]
    # ctype = set([(category_details[i][1]) for i in range(len(category_details))])
    # print(cname, ctype)
    return render_template('category.html', name=cname, lname=cname, logged_in=True, operator_id=operator.id, is_admin=operator.is_admin)#, ctype=ctype)
                    

@app.route('/add_cat', methods=['POST', 'GET'])
def add_category_details():
    
    operator = current_user
    
    lname = request.form['lname'].lower().capitalize()
    # lname = lname.upper()
    
    # print(lname, lid)
    
    # x=True
    # print(lname)
    x= add_category(lname)
#     operator = current_user
    
#     cname = request.form['cname'].lower()
#     cat_new_name = request.form['catname'].lower()
#     # ctype = request.form['ctype'].lower()
#     # cat_new_type = request.form['cattype'].lower()
    
#     keys = [k for k in request.form.keys()]
#     print(keys)
#     print(1,cname)
#     x=True
#     if cname=='new':
#         # if ctype=='new':
#         #     print('x') #x=add_category(cat_new_name, cat_new_type)
#         # else:
#             print('y') #x=add_category(cat_new_name, cat_type)
#     # else:
#     #     if ctype=='new':
#     #         print('z') #x=add_category(cname, cat_new_type)
#     #     else:
#     #         print('w') #x=add_category(cname, cat_type)

    if x==True:
        flash('Category added successfully!!')
    elif x==False:
        flash('Category addition failed.')
    elif x==-1:
        flash("Category name already exists. Enter another name.")

    return details_category()

@app.route('/loc')
def details_location():
    operator = current_user
    location_details = get_locations()
    # print(location_details)
    lname = [(location_details[i][1]) for i in range(len(location_details))]
    # print(lname)
    return render_template('location.html', name=lname, lname=lname, logged_in=True,operator_id=operator.id, is_admin=operator.is_admin)
                    

@app.route('/add_loc', methods=['POST', 'GET'])
def add_loc_details():

    operator = current_user
    
    lname = request.form['lname']
    lname = lname.lower().capitalize()
    # print(lname, lid)
    
    x=add_location(lname, lname)

    if x==True:
        flash('Location added successfully!!')
    elif x==False:
        flash('Location addition failed.')
    elif x==-1:
        flash("Location name already exists. Enter another name.")

    return details_location()

