from flask import Flask, request, render_template, send_file, redirect, session,\
                  url_for, send_from_directory, Response, make_response, jsonify, flash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from werkzeug.utils import secure_filename
import base64, os, sys, cv2, time, glob, cv2
import numpy as np, pandas as pd
from multidict import MultiDict
from .face_creation import crop_faces, create_descriptor
from .load_config import CONFIG
from .webapp_utils import User, memory_container, is_known_user, encrypt,\
                          get_user_info, allowed_file, register_user, search_by,\
                          update_status_details, delete_entries, get_alerts, get_camera_list, get_roster, add_operator, search_operator_from_db,\
                          update_role, delete_operators, update_password, get_all_registered_faces,\
                          get_shift_timing, update_employee_shift, add_roster, generate_action_tesa_report,if_face_enrolled, get_department, get_status_list, update_employee_department, get_weekdays, get_locations, add_department, get_dept_people, update_department, add_location, get_category, add_category,download_cam_logs_report, download_workhour_logs_report, download_daily_report, download_monthly_report



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
        fname = os.path.join(TEMPLATE_FOLDER, 'bootstrap.js.map')
        
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

# @app.route('/video_recog', methods=['POST', 'GET'])
# @login_required
# def show_video_recog_page():
#     operator = current_user
#     return render_template('upload_video.html',
#                            logged_in=True,
#                            operator_id=operator.id,
#                            is_admin=operator.is_admin)

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

@app.route('/operator/search', methods=['GET'])
@login_required
def search_operator():
    
    operator = current_user
    if request.method == 'GET':
        res = None
        if 'optuname' in request.args:
            operator_username = request.args['optuname']
            res = search_operator_from_db(operator_username, by_username=True, return_dc = True)
        if 'optname' in request.args:
            operator_name = request.args['optname']
            res = search_operator_from_db(operator_name, by_name=True, return_dc = True)
            

        header = ['Username', 'Name', 'Role']
        result = []
        if res:
            for r in res:
                if r.username != operator.id:
                    role = 'Receptionist'
                    if r.role == 'admin':
                        role = 'Admin'
                    result.append([r.username, r.name, role])

            if len(result) > 0:
                return render_template('show_operator_search_result.html',
                                        header=header,
                                        result=result,
                                        logged_in=True,
                                        operator_id=operator.id,
                                        is_admin=operator.is_admin)
            else:
                flash('Only current user is found, not allowed to update self status!!')
                return render_template('search_modify_operator.html',
                                        logged_in=True,
                                        operator_id=operator.id,
                                        is_admin=operator.is_admin)
        else:
            flash('No such operator found!!')
            return render_template('search_modify_operator.html',
                                    logged_in=True,
                                    operator_id=operator.id,
                                    is_admin=operator.is_admin)

@app.route('/operator/modify', methods=['POST'])
@login_required
def modify_operator():
    operator = current_user

    password = request.form['password']
    u_password, _ = get_user_info(operator.id)

    if u_password == encrypt(password):

        operators_to_change = []
        for k in request.form:
            v = k.split('_')[0]
            if v == 'chk':
                v1 = '_'.join(k.split('_')[1:])
                operators_to_change.append(v1)

        if len(operators_to_change) > 0 and 'update' in request.form:
            
            new_roles = []
            for opt in operators_to_change:
                role_name = f'newRole_{opt}'
                new_roles.append(request.form[role_name])

            update_role(operators_to_change, new_roles)
            flash('Updated successfully!!')
            

        elif len(operators_to_change) > 0 and 'delete' in request.form:
            delete_operators(operators_to_change)
            flash('deleted successfully!!')

        else:
            flash('Nothing was selected!!')

    else:
        flash('Provided password is wrong!!')
        return logout()

    return render_template('search_modify_operator.html',
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)

#################### webapp/user_enrollment functions #########

@app.route('/user/enroll', methods=['POST'])
@login_required
def enroll_user():

    operator = current_user
    #if not operator.is_admin:
    #    return redirect(url_for('logout'))

    user_id = request.form['rid']
    user_first_name = request.form['ufname']
    user_middle_name = request.form['umname']
    user_last_name = request.form['ulname']
    category = request.form['usercategory']
    shift = request.form['usershift']
    department = request.form['userdepartment']

    image_file = request.files['userimage']
	
    if image_file.filename == '':
        return render_template('camera.html', 
                                user_id=user_id, 
                                user_first_name=user_first_name, 
                                user_middle_name=user_middle_name, 
                                user_last_name=user_last_name, 
                                category = category,
                                shift=shift, department = department,
                                logged_in=True, 
                                operator_id=operator.id, 
                                is_admin=operator.is_admin)
    
    if allowed_file(image_file.filename):
        _filename = secure_filename(os.path.basename(image_file.filename))
        filename = os.path.join(app.config['TEMP_FOLDER'], _filename) # Create a unique file name
                                                                      # so that it does not conflict
        image_file.save(filename)

        crops = crop_faces(filename)
        disp_url = []
        roi_dict = {}

        # Need better way to do this
        basename, ext = os.path.splitext(_filename)
        
        disp_url.append([_filename, url_for('get_temp_img', filename=_filename)])
        roi_dict.update({'BASE_FILE': _filename, _filename:None})

        for i, crop in enumerate(crops):
            _filename_crop = f'{basename}-crop_{i}_{user_id}.{ext}'
            fpath = os.path.join(app.config['TEMP_FOLDER'], _filename_crop)
            cv2.imwrite(fpath, crop[0])
            disp_url.append([_filename_crop, url_for('get_temp_img', filename=_filename_crop)])
            roi_dict.update({_filename_crop: crop[1]})

        operator.add_work('register', roi_dict)
        return render_template('register.html',
                                user_id=user_id, 
                                user_first_name=user_first_name, 
                                user_middle_name=user_middle_name,
                                user_last_name=user_last_name, 
                                category = category,
                                shift=get_shift_timing(shift), department = get_department(department),
                                disp_url=disp_url,
                                logged_in=True,
                                operator_id=operator.id,
                                is_admin=operator.is_admin)

    return return_home_page(current_user)


@app.route('/user/enroll/capture', methods=['POST'])
@login_required
def capture_from_camera():
    
    operator = current_user

    user_id = request.form['rid']
    user_first_name = request.form['ufname']
    user_middle_name = request.form['umname']
    user_last_name = request.form['ulname']
    category = request.form['ucategory']
    shift = request.form['ushift']
    department = request.form['udepartment']

    img_data = request.form['imgData'].split(',')[1]
    binary = base64.b64decode(img_data)
    image_data = np.asarray(bytearray(binary), dtype='uint8')
    img_data = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

    _filename = f'capture-{user_id}.png'
    disp_image = os.path.join(app.config['TEMP_FOLDER'], _filename)
    cv2.imwrite(disp_image, img_data)

    crops = crop_faces(disp_image)

    disp_url = [[_filename, url_for('get_temp_img', filename=_filename)]]
    roi_dict = {'BASE_FILE': _filename, _filename:None}

    for i, crop in enumerate(crops):
        _filename_crop = f'capture-crop_{i}-{user_id}.png'
        fpath = os.path.join(app.config['TEMP_FOLDER'], _filename_crop)
        cv2.imwrite(fpath, crop[0])
        disp_url.append([_filename_crop, url_for('get_temp_img', filename=_filename_crop)])
        roi_dict.update({_filename_crop: crop[1]})
    
    operator.add_work('register', roi_dict)
    
    #TODO reset button functionality not added
    return render_template('register.html',
                            user_id=user_id,
                            user_first_name=user_first_name,
                            user_middle_name=user_middle_name,
                            user_last_name=user_last_name,
                            disp_url=disp_url,
                            category = category,
                            shift=get_shift_timing(shift), department = get_department(department),
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)


@app.route('/user/confirm', methods=['POST'])
@login_required
def confirm_details():
    
    operator = current_user

    if 'reset' in request.form:
        operator.remove_work('register')
        return return_home_page(operator)

    else:

        user_id = request.form['rid']
        user_first_name = request.form['ufname']
        user_middle_name = request.form['umname']
        user_last_name = request.form['ulname']
        filename = request.form['indiv']
        image_file = os.path.join(app.config['TEMP_FOLDER'], filename)
        category = request.form['category']
        shift = request.form['shift']
        department = request.form['department'] 

        roi_data = operator.remove_work('register')
        
        if if_face_enrolled(user_id):
            flash('User id already exists')
            return  show_enroll_user_page()

        name_part = []
        for u in [user_first_name, user_middle_name, user_last_name]:
            if len(u) > 0:
                name_part.append(u)
        
        user_name = ' '.join(name_part)
        base_file = os.path.join(app.config['TEMP_FOLDER'], roi_data['BASE_FILE'])
        roi = roi_data[filename]

        descriptor = create_descriptor(base_file, roi)
        
        if register_user(user_id, user_name, image_file, category, department, shift, descriptor):
            memory_container['control_panel'].set_update_cache()
            flash('User registration successful.')
        else:
            flash('User registration Failed!!')

        #return return_home_page(operator)

        return show_enroll_user_page()


#################### webapp/serach_user functions ##############

@app.route('/user/serach', methods=['POST', 'GET'])
@login_required
def search_user():

    operator = current_user

    today = datemodule.today()
    yesterday = today - timedelta(1)

    details_to_display = []
    if request.method == 'GET':
        #TODO search by rname and rid multiple values seaparated by ','
        #TODO also try to add exact option in UI
        if 'rname' in request.args:
            rnames = request.args['rname'].split(',')
            person_details, face_details = [],{}
            for rname in rnames:
                a, b = search_by(rname, user_name=True)
                if len(a) > 0:
                    person_details.extend(a)
                    face_details.update(b)

        if 'rid' in request.args:
            rids = request.args['rid'].split(',')
            person_details, face_details = [],{}
            for rid in rids:
                a, b = search_by(rid, user_id=True)
                if len(a) > 0:
                    person_details.extend(a)
                    face_details.update(b)

        
        if len(person_details) == 0:
            flash('No such face found!!')
            return show_search_modify_user_page()
        
        # print(person_details, face_details)
        details_to_display = get_details_for_display(person_details, face_details)
        operator.add_work('search', {d[0]:d for d in details_to_display})
        
        

        # print("DETAILS TO DISPLAY: ",details_to_display)
        

        return render_template('search_results.html', 
                                details=details_to_display, 
                                shift_list=get_roster(), status_list = get_status_list(), department_list = get_department(),
                                start_disp=yesterday, 
                                end_disp=today,
                                logged_in=True,
                                operator_id=operator.id,
                                is_admin=operator.is_admin)

    else:
        return return_home_page(operator)

@app.route('/search/confirm', methods=['POST'])
@login_required
def search_action_confirm():
    

    operator = current_user
    details_to_display = []
    mode = ''

    search_result = operator.remove_work('search')
    unique_keys = np.unique(list(search_result.keys()))

    password = request.form['password']
    u_password, _ = get_user_info(operator.id)
    
    # if password=='':
    #     flash('Password not entered!!')
    #     #return redirect(request.referrer)
    #     # return show_search_modify_user_page()
    #     today = datemodule.today()
    #     yesterday = today - timedelta(1)


    #     for u in unique_keys:
    #         if u in request.form:
    #             new_update_value = request.form[f'threat_{u}']
    #             # search_result[u][2]=new_update_value
    #             if len(search_result[u])<5:
    #                 search_result[u].append(new_update_value)
    #             else:
    #                 search_result[u][4]=new_update_value


    #     operator.add_work('search', search_result)

    #     print("DETAILS TO DISPLAY: ",search_result)
    #     return render_template('search_results.html', 
    #                             details=search_result.values(), 
    #                             start_disp=yesterday, 
    #                             end_disp=today,
    #                             logged_in=True,
    #                             operator_id=operator.id,
    #                             is_admin=operator.is_admin)
        
        
    if u_password != encrypt(password):
        flash('Provided password is wrong!!')
        return show_search_modify_user_page()

    if 'reset' in request.form:
        #return return_home_page(operator)
        return show_search_modify_user_page()
    
    #TODO: remove show logs from here search and modify
    elif 'show' in request.form:
        
        download_logs_for = []
        for u in unique_keys:
            if u in request.form:
                download_logs_for.append(u)
        
        user_name = [None] * len(download_logs_for)
        start_date = request.form['startdate']
        end_date = request.form['enddate']
        recog_mode = 'all'#request.form['recog_mode']

        # path, online_data, offline_data = generate_report(user_list=download_logs_for,
        #                                                   user_name=user_name,
        #                                                   start_date=start_date,
        #                                                   end_date=end_date,
        #                                                   mode=recog_mode)
        path, online_data = generate_action_tesa_report(user_list=download_logs_for, user_name=user_name, start_date=start_date, end_date=end_date, info='home_')
        online_columns = online_data.columns.tolist()
        online_values = online_data.values.astype(np.str)
        offline_columns = offline_data.columns.tolist()
        offline_values = offline_data.values.astype(np.str)

        file_basename = os.path.basename(path)

        if online_values.shape[0] > MAX_DISPLAY_ROWS:
            online_values = online_values[:MAX_DISPLAY_ROWS]
            flash(f'[Online Logs]: Displaying {MAX_DISPLAY_ROWS} only. For full logs, download logs.')

        if offline_values.shape[0] > MAX_DISPLAY_ROWS:
            offline_values = offline_values[:MAX_DISPLAY_ROWS]
            flash(f'[Video Recognition Logs]: Displaying {MAX_DISPLAY_ROWS} only. For full logs, download logs.')

        return render_template('show_log_report.html',
                                online_columns=online_columns,
                                online_values=online_values,
                                offline_columns=offline_columns,
                                offline_values=offline_values,
                                mode=recog_mode,
                                download_file=file_basename,
                                logged_in=True,
                                operator_id=operator.id,
                                is_admin=operator.is_admin)

    elif 'update' in request.form:
        mode = 'update'

        for u in unique_keys:
            if u in request.form:
                new_update_value = request.form[f'upuserstatus_{u}']
                new_shift = request.form[f'upusershift_{u}']
                new_dept = request.form[f'upuserdept_{u}']
                # details_for_display.append([user_id, user_name, threat_type, get_shift_timing(shift_id), images,get_department(deptid)])
                vals = search_result.pop(u)
                shift_updated = 'n'
                if new_shift != vals[3][0]:
                    shift_updated = 'y'
                dept_updated = 'n'    
                if new_dept != vals[5][0]:
                    dept_updated = 'y'
                vals.append(new_update_value)
                vals.append(shift_updated)
                vals.append(dept_updated)
                if shift_updated == 'y':
                    vals.append(get_shift_timing(new_shift))
                else:
                    vals.append("")
                if dept_updated == 'y':
                    vals.append(get_department(new_dept))
                else:
                    vals.append("")

                details_to_display.append(vals)
        # print(details_to_display)

    elif 'delete' in request.form:
        mode = 'delete'
        for u in unique_keys:
            if u in request.form:
                vals = search_result.pop(u)
                details_to_display.append(vals)
    
    operator.add_work('search', {d[0]:d for d in details_to_display})

    return render_template('confirm_search_result.html', 
                            mode=mode, 
                            details=details_to_display,
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)

@app.route('/search/execute', methods=['POST'])
@login_required
def execute_search_action():

    operator = current_user

    search_result = operator.remove_work('search')
    mode = request.form['search_action']
    
    # print(search_result)
    # return
    
    # details_for_display.append([user_id, user_name, threat_type, get_shift_timing(shift_id), images,get_department(deptid)])+ for update (new_status, shift updated, dept updated, shit new details , dept new details

    if 'confirm' in request.form:

        if mode == 'update':
            categories_to_update = []
            shifts_to_update = []
            departments_to_update = []
            for k in search_result.keys():
                
                if isinstance(search_result[k][-1], tuple):
                    if search_result[k][2] == search_result[k][6]:
                        departments_to_update.append([k, search_result[k][-1][0], search_result[k][2], search_result[k][5][0], None])
                    else:
                        departments_to_update.append([k, search_result[k][-1][0], search_result[k][2], search_result[k][5][0], search_result[k][6]])
                    # if search_result[k][2] == search_result[k][6]:
                    #     departments_to_update.append([k, search_result[k][-1][0], True])
                    # else:
                    #     departments_to_update.append([k, search_result[k][-1][0], False])

                if search_result[k][2] != search_result[k][6]:
                    if isinstance(search_result[k][-1], tuple):
                        #dept changed
                        categories_to_update.append([k, search_result[k][6], search_result[k][2], search_result[k][5][0], search_result[k][-1][0]])
                    else:
                        categories_to_update.append([k, search_result[k][6], search_result[k][2], search_result[k][5][0], None])
                    
                if isinstance(search_result[k][-2], tuple):
                    shifts_to_update.append([k, search_result[k][-2][0]])
                    
                    
            #TODO CHECK FOR CASE HOD STATUS  
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
                res = update_employee_shift(*list(zip(*shifts_to_update)))
                if res:
                    flash('Shift has been successfully modified.')
                else:
                    flash('Shift modification failed.')
                    
                    
            
        status = None
        if mode == 'delete':
            #TODO dont delete employee from db instead change status to non-employee
            user_to_delete = []
            for k in search_result.keys():
                user_to_delete.append([k, search_result[k]])
            
            if len(user_to_delete) > 0:
                status = delete_entries(*list(zip(*user_to_delete)))
                if status:
                    flash('Face has been deleted.')
                else:
                    flash('Face deletion failed.')
        
        if status:
            memory_container['control_panel'].set_update_cache()
    
    return show_search_modify_user_page()

@app.route('/show/all/faces', methods=['POST'])
@login_required
def show_all():

    operator = current_user

    today = datemodule.today()
    yesterday = today - timedelta(1)

    person_details, face_details = get_all_registered_faces()

    if len(person_details) == 0:
        flash('No face found!!')
        return show_search_modify_user_page()

    details_to_display = get_details_for_display(person_details, face_details)
    operator.add_work('search', {d[0]:d for d in details_to_display})

#     if not memory_container['webapp_dict'].add_work(session['_tracker_id'], 'search', {d[0]:d for d in details_to_display}):
#         flash('Stale Session, Please login again.')
#         return logout()

    
    return render_template('search_results.html', 
                            details=details_to_display,
                            shift_list=get_roster(), status_list = get_status_list(), department_list = get_department(),
                            start_disp=yesterday, 
                            end_disp=today,
                            logged_in=True,
                            operator_id=operator.id,
                            is_admin=operator.is_admin)


        


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
    values = all_records.values.astype(np.str)
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

            all_records.drop('sid', axis=1, inplace=True)

            colnames = all_records.columns.tolist()
            data = all_records.values.astype(np.str)
            basepath = os.path.basename(path)
            values.append(details_to_display[0] + [latest_time, last_location, basepath, colnames, data])
    
    return render_template('show_indiv_alerts.html',
                           values=values,
                           logged_in=True,
                           operator_id=operator.id,
                           is_admin=operator.is_admin)

#################### webapp/videofeed functions #################

def get_frame():
    
    webdisplay_memory = memory_container['webdisplay']
    while True:
        prop = webdisplay_memory.get_frame()
        if prop:
            frame = prop[1]
        else:
            frame = np.random.randint(0, 255, size=(int(CONFIG['MONITOR']['height']), int(CONFIG['MONITOR']['width']), 3), dtype=np.uint8)
        
        (flag, encoded_image) = cv2.imencode('.jpg', frame)

        if not flag:
            continue

        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n'+ bytearray(encoded_image) + b'\r\n')


@app.route('/video/feed')
@login_required
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)

    operator = current_user
    if not operator.is_admin:
        return render_template('login.html', 
                                logged_in=False)

    return Response(get_frame(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

#################### webapp/offline recognition functions #########

@app.route('/video/upload', methods=['POST'])
def upload_video():
    
    video = request.files['file']
    disp_name = os.path.basename(video.filename)
    save_name = os.path.join(app.config['TEMP_FOLDER'], secure_filename(video.filename))
    video.save(save_name)
    current_user.add_work('video_filename', save_name)
    return make_response(jsonify({"message": "File uploaded", "savedfilename":disp_name}), 200)

# @app.route('/video/recogserver', methods=['POST'])
# @login_required
# def run_recog_video():
    
#     operator = current_user

#     video_filename = current_user.remove_work('video_filename')
#     rotation = int(request.form['rotation'])
    
#     recog_process_id, recog_process_obj, output_path = run_video_recognition(video_filename, rotation)
#     operator.add_work('video_recog', (recog_process_id, recog_process_obj))

#     return render_template('recognition_progress.html',
#                            identifier=recog_process_id,
#                            filename=os.path.basename(video_filename),
#                            processed_video=os.path.basename(output_path),
#                            log_location='#'.join([recog_process_id, os.path.basename(video_filename)]),
#                            logged_in=True,
#                            operator_id=operator.id,
#                            is_admin=operator.is_admin)


@app.route('/progress/<identifier>')
@login_required
def recog_progress(identifier):
    
    operator = current_user
    recog_process_id, recog_process_obj = operator.remove_work('video_recog')

    progress = memory_container['progress_bar']

    def generate(recog_process_obj):

        x = 0
        while x <= 100:
            yield "data:" + str(x) + "\n\n"
            if x == 100:
                break
            time.sleep(1)
            frame_count = progress.get_frame_count(recog_process_id)
            curr_count = progress.get_count(recog_process_id)
            if frame_count == 0:
                continue
            x = int(100*((curr_count+1)/frame_count))
    
        recog_process_obj.join()

    return Response(generate(recog_process_obj), mimetype='text/event-stream')


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
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    
    #TODO integrate namans template code
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
    
    #TODO ADD OFFDAY
    print(rid, rname, start_time, end_time, rwkly_off)
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
    path, online_data=download_workhour_logs_report( user_list = emp_ids, user_name = emp_names, shifts = shifts, departments = departments, start_date= start_date, end_date = end_date, total_rows = int(end_ent[0])-int(start_ent[0]))
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
    path, online_data=download_cam_logs_report( user_list = emp_ids, user_name = emp_names, shifts = shifts, departments = departments, start_date= start_date, end_date = end_date, total_rows = int(end_ent[0])-int(start_ent[0]))
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

    li_key_report= ['lc', 'el', 'mp', 'absent', 'gw', 'present', 'hlf_day', 'full_day_leave','weeklyoff','comp_hldy','dept_hldy']
    li_specific_report=[]
    for k in dict_value.keys():
        if k in li_key_report:
            li_specific_report.append(dict_value[k][0])
    # li_specific_report = [dict_value[k] for k in dict_value.keys() if k in li_key_report]
    # print("lispeficreport",li_specific_report)
    
    path, online_data=download_daily_report( user_list = emp_ids, user_name = emp_names, shifts = shifts, departments = departments, start_date= start_date, end_date = end_date, total_rows = int(end_ent[0])-int(start_ent[0]),status_list = li_specific_report)
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

@app.route('/reports/monthly_logs', methods=['POST', 'GET'])
def print_mnthly_logs():
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
        # if 'from_date' in dict_value.keys() and 'to_date' in dict_value.keys():
        #     final_data_for_filter['from_date']=None
        #     final_data_for_filter['from_date'] = dict_value['from_date'][0]
        #     final_data_for_filter['to_date']=None
        #     final_data_for_filter['to_date'] = dict_value['to_date'][0]
            # count+=1
        # print(count)
     
    print("final data", final_data_for_filter)
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
    print("year and month",selected_year, selected_month)
    
    path, online_data=download_monthly_report( user_list = emp_ids, user_name = emp_names, shifts = shifts, departments = departments, month= selected_month, year = selected_year, total_rows = int(end_ent[0])-int(start_ent[0]))
    
    if path == -1:
        flash(f'No log found')
        return print_reports()
    

    online_columns = []#online_data.columns.tolist()
    online_values = []#online_data.values.astype(np.str)
    #offline_columns = offline_data.columns.tolist()
    #offline_values = offline_data.values.astype(np.str)

    file_basename = os.path.basename(path)

    if len(online_values) > MAX_DISPLAY_ROWS:
        online_values = online_values[:MAX_DISPLAY_ROWS]
        flash(f'[Online Logs]: Displaying {MAX_DISPLAY_ROWS} only. For full logs, download logs.')

    name = 'MONTHLY REPORT'
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



@app.route('/dept')
def details_department():
    operator = current_user
    department_details = get_department()
    code = [(str(department_details[i][1]).split(' ('))[0] for i in range(len(department_details))]
    
    locations = [i[1] for i in get_locations()]
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

    rname = request.form['rname'].lower()
    # rcode = request.form['rcode']
    
    #TODO: ADD CATEGORY HOD to CATEGORY TABLE AND ADD A DROPDOWN LISTING ONLY HODS. ALSO SHOULD CHANGE CHECK CONDITION WHILE SHOWING DETAILS IN ENROLL FACE AND SEARCH AND MODIFY FACE
    rhod = ""#request.form['rhod'].lower()
    rlocation = request.form['locationdropdown'].lower()
    
    #TODO add home button and automatic length check
    if not rname:
        flash('Enter Department Name!!')
        return details_department()

    x = add_department(rname, rhod, location = rlocation) #change to add department

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
    print("search option", search_option)    

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
        print("dict values/new details",dict_value)
        #{'eid': '1', 'empname': 'Sanjay Singh', 'shifts': '2', 'location': 'HAUZ KHAZ', 'status': 'Non-Employee', 'dpmts': changed to id #'operations2 (HAUZ KHAZ) (-)'}
        emp_id  = dict_value.get('eid',None)
        new_name = dict_value.get('empname',None)
        new_shiftid = dict_value.get('shifts',None)
        # new_location = dict_value.get('location',None)
        new_status = dict_value.get('status',None)
        new_deptid = dict_value.get('dpmts',None)
        
        
        #emp dict {'1': {'empname': 'sanjay singh', 'emp_dpmt': 'Department1 ', 'empstatus': 'Employee', 'currshift': 'D', 'location': 'punjab'}
        curr_details = emp_details_dict.get(emp_id)
        #TODO ADD NAME CHANGE UTIL IN WEBAPP UTILS
        name = curr_details['empname']
        shift = curr_details['currshift']
        status = curr_details['empstatus']
        deptid = curr_details['deptid']
        print("old details", curr_details)
        
        departments_to_update = []
        shifts_to_update = []
        categories_to_update = []
        
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

        if shift!=new_shiftid:#isinstance(search_result[k][-2], tuple):
            # shifts_to_update.append([k, search_result[k][-2][0]])
            shifts_to_update.append([emp_id, new_shiftid])
    
    
        # final_data_for_filter = dict()
        # count = 0
        # print('here')
        # if ('start_ent' in dict_value.keys() and 'end_ent' in dict_value.keys()):
        #     print('ss')
        #     count+=1
        # if 'location' in dict_value.keys():
        #     final_data_for_filter['location']=None
        #     final_data_for_filter['location'] = dict_value['location'][0].split(';')
        #     count+=1
        #     print('yy')
        # if 'empname' in dict_value.keys():
        #     final_data_for_filter['emp_name']=None
        #     final_data_for_filter['emp_name'] = dict_value['empname'][0].split(';')
        #     count+=1
        # if 'shifts' in dict_value.keys():
        #     final_data_for_filter['shift']=None
        #     final_data_for_filter['shift'] = dict_value['shifts']
        #     shifts_to_update = shifts_to_update.append(final_data_for_filter['shift'])
        #     count+=1
        # if 'dpmts' in dict_value.keys():
        #     final_data_for_filter['dpmt']=None
        #     final_data_for_filter['dpmt'] = dict_value['dpmts']
        #     departments_to_update = departments_to_update.append(final_data_for_filter['dpmt'])
        #     count+=1
        # if 'status' in dict_value.keys():
        #     final_data_for_filter['status']=None
        #     final_data_for_filter['status'] = dict_value['status']
        #     categories_to_update = categories_to_update.append(final_data_for_filter['status'])
        #     count+=1
        # print("final data",count, final_data_for_filter)
        # return update_details_employee()
    
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
            res = update_employee_shift(*list(zip(*shifts_to_update)))
            if res:
                flash('Shift has been successfully modified.')
            else:
                flash('Shift modification failed.')

        #return return_home_page(operator)

        return update_details_employee()

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
    department_dict = {f'{i[1]}({i[2]})': [f'({i[-2]}{i[-1]})',i[2],i[0]] for i in  get_department(raw= True)}
    
    operator.add_work('updt_dept',department_dict)
    
    
    #TODO Add drop down to select hod - list of people of that department
    dept_hod_list = []#get_dept_people(deptid)
    return render_template('updateDepartment.html', 
                           department_dict = department_dict,
                           department_names = list(department_dict.keys()),
                           locations = [i[0] for i in get_locations()],
                           hod_list = dept_hod_list,
                           logged_in=True,
                           operator_id=operator.id,
                           is_admin=operator.is_admin)

@app.route('/update_dpmt_details',  methods=['POST', 'GET'])
def update_details_dpmt():
    
    operator = current_user
    
    dict_value = {k:request.form[k] for k in request.form.keys() if len(request.form[k])!=0} #in this you will find each and every non-empty inputs of the form
    print("dictvalue",dict_value)
    # dpmt_name=''  # will be a list if the user search on the basis of employee name. Need to handle over here such that in case of a single person it should
    #             # pass a string else it should pass a list.
    # wklyoff=''
    print("location", request.form["dlocations"])
    department = dict_value.get("dpmts",None)
    new_location = dict_value.get("dlocations",None)
    new_name = dict_value.get("dname",None)
    hod = None#request.form("hods")
    
    
    department_dict = operator.remove_work('updt_dept')

    if not new_location:
        new_location = None
        
    if not new_name:
        new_name = None
    
    location, deptid = None, None
    if department:
        # department = department
        # name, curloc = department[0], department[1]
        department_details = department_dict[department]#get_dept_id(name, curloc)
        deptid, location = department_details[-1], department_details[-2]
        # print("deptid", deptid)
        
    print("details",department,location,hod, deptid, new_name, new_location)
    
    
    res = None
        
    if not department or (not new_name and not new_location):
        res= -1
    else:
        res = update_department([deptid], [new_name], [new_location], [hod])
        
    print(res)
    
    if res == -1:
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
    print(category_details)
    cname = [(category_details[i][0]) for i in range(len(category_details))]
    # ctype = set([(category_details[i][1]) for i in range(len(category_details))])
    # print(cname, ctype)
    return render_template('category.html', name=cname, lname=cname)#, ctype=ctype)
                    

@app.route('/add_cat', methods=['POST', 'GET'])
def add_category_details():
    
    operator = current_user
    
    lname = request.form['lname'].lower().capitalize()
    # lname = lname.upper()
    
    # print(lname, lid)
    
    # x=True
    print(lname)
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
    print(location_details)
    lname = [(location_details[i][1]) for i in range(len(location_details))]
    print(lname)
    return render_template('location.html', name=lname, lname=lname)
                    

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
 