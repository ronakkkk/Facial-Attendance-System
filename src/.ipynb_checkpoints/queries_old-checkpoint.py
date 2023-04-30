from .dbutils import run_fetch_query, run_query_noreturn
from .global_vars import ONLINE_LOG_TABLE_FIELDS, OFFLINE_LOG_TABLE_FIELDS, \
                         ONLINE_LOG_TABLE, OFFLINE_LOG_TABLE, LOGIN_TABLE_FIELDS,\
                         USER_TABLE_FIELDS, VECTORS_TABLE_FIELDS, IDENTITY_TABLE_FIELDS,\
                         PEOPLE_TABLE_FIELDS, ALERT_TABLE, ALERT_TABLE_FIELDS,\
                         ROSTER_TABLE, ROSTER_TABLE_FIELDS
from .load_config import CONFIG
from pandas import to_datetime, DataFrame
from numpy import unique

def get_person_log(conn, identity, _date, _location=None, online=True):

    if online:
        query = f'SELECT * FROM {ONLINE_LOG_TABLE_FIELDS.table_name} WHERE {ONLINE_LOG_TABLE_FIELDS.field_identity}=? and {ONLINE_LOG_TABLE_FIELDS.field_date}=?'
        values = (identity, _date)
    else:
        query = f'SELECT * FROM {OFFLINE_LOG_TABLE_FIELDS.table_name} WHERE {OFFLINE_LOG_TABLE_FIELDS.field_identity}=? and {OFFLINE_LOG_TABLE_FIELDS.field_filename}=? and {OFFLINE_LOG_TABLE_FIELDS.field_date}=?'
        values = (identity, _location, _date)
    
    return run_fetch_query(conn, query, values)

def create_person_log(conn, identity, _date, in_time, out_time=None, first_location=None, last_seen_location=None, online=True):
    
    if out_time is None:
        out_time = in_time
    
    if first_location is None:
        first_location = ''

    if last_seen_location is None:
        last_seen_location = first_location

    if online:
        columns = [
            ONLINE_LOG_TABLE_FIELDS.field_identity,
            ONLINE_LOG_TABLE_FIELDS.field_in_time,
            ONLINE_LOG_TABLE_FIELDS.field_out_time,
            ONLINE_LOG_TABLE_FIELDS.field_date,
            ONLINE_LOG_TABLE_FIELDS.field_first_location,
            ONLINE_LOG_TABLE_FIELDS.field_last_seen_location
        ]

        column_order = ', '.join(columns)
        values_q = ', '.join(['?'] * len(columns))

        query = f'INSERT INTO {ONLINE_LOG_TABLE_FIELDS.table_name}({column_order}) VALUES({values_q})'
        values = (identity, in_time, out_time, _date, first_location, last_seen_location)
    else:

        columns = [
            OFFLINE_LOG_TABLE_FIELDS.field_identity,
            OFFLINE_LOG_TABLE_FIELDS.field_in_time,
            OFFLINE_LOG_TABLE_FIELDS.field_out_time,
            OFFLINE_LOG_TABLE_FIELDS.field_date,
            OFFLINE_LOG_TABLE_FIELDS.field_filename
        ]

        column_order = ', '.join(columns)
        values_q = ', '.join(['?'] * len(columns))

        query = f'INSERT INTO {OFFLINE_LOG_TABLE_FIELDS.table_name}({column_order}) VALUES({values_q})'
        values = (identity, in_time, out_time, _date, first_location)

    run_query_noreturn(conn, query, values)
    
def update_person_log(conn, fetched_result, identity, _date, _time, _location, online=True):

    if online:
        last_seen_time = to_datetime(fetched_result[ONLINE_LOG_TABLE.last_seen_time.value])
        if (_time - last_seen_time).seconds < int(CONFIG['RECOGNITION']['update_last_seen_sec']):
            return
        else:
            query = f'UPDATE {ONLINE_LOG_TABLE_FIELDS.table_name} SET {ONLINE_LOG_TABLE_FIELDS.field_out_time} = ?, {ONLINE_LOG_TABLE_FIELDS.field_last_seen_location} = ? WHERE {ONLINE_LOG_TABLE_FIELDS.field_identity} = ? AND {ONLINE_LOG_TABLE_FIELDS.field_date} = ?'
            values = (_time, _location, identity, _date)
    else:
        query = f'UPDATE {OFFLINE_LOG_TABLE_FIELDS.table_name} SET {OFFLINE_LOG_TABLE_FIELDS.field_out_time} = ? WHERE {OFFLINE_LOG_TABLE_FIELDS.field_identity} = ? AND {OFFLINE_LOG_TABLE_FIELDS.field_date} = ? AND {OFFLINE_LOG_TABLE_FIELDS.field_filename} = ?'
        values = (_time, identity, _date, _location)
    
    run_query_noreturn(conn, query, values)

def add_person_log(conn, fetched_result, identity, _date, _time, _location, online=True):

    last_seen_time = to_datetime(fetched_result[ONLINE_LOG_TABLE.last_seen_time.value])
#     print("last seen: ",last_seen_time,"\nnew time:",_time)
#     print("time diff:",(_time - last_seen_time).seconds)
    if (_time - last_seen_time).seconds < int(CONFIG['RECOGNITION']['update_last_seen_sec']):
        return
    else:
        create_person_log(conn, identity, _date, _time, out_time=_time, first_location=_location, last_seen_location=_location, online=online)

def get_threat_status(conn, identity):

    query = f'SELECT {PEOPLE_TABLE_FIELDS.field_threat} FROM {PEOPLE_TABLE_FIELDS.table_name} WHERE {PEOPLE_TABLE_FIELDS.field_identity} = ?'
    return run_fetch_query(conn, query, (identity,), fetch_type='one')

def get_previous_alert(conn, identity, _date):
    
    query = f'SELECT * FROM {ALERT_TABLE_FIELDS.table_name} WHERE {ALERT_TABLE_FIELDS.field_identity} = ? AND {ALERT_TABLE_FIELDS.field_date} = ? ORDER BY {ALERT_TABLE_FIELDS.field_datetime} DESC'
    res = run_fetch_query(conn, query, (identity, _date), fetch_type='one')
    
    if res:
        row_id = res[ALERT_TABLE.f_id.value]
        alert_time = to_datetime(res[ALERT_TABLE.datetime.value])
        location = res[ALERT_TABLE.location.value]

        return row_id, alert_time, location
    else:
        return None, None, None

def update_alert(conn, _time, row_id):
    
    query = f'UPDATE {ALERT_TABLE_FIELDS.table_name} SET {ALERT_TABLE_FIELDS.field_datetime} = ? WHERE {ALERT_TABLE_FIELDS.field_row_id} = ?'
    run_query_noreturn(conn, query, (_time, row_id))

def insert_alert(conn, identity, _time, _date, _location):
    
    query = f'INSERT INTO {ALERT_TABLE_FIELDS.table_name}({ALERT_TABLE_FIELDS.field_identity}, {ALERT_TABLE_FIELDS.field_datetime}, {ALERT_TABLE_FIELDS.field_date}, {ALERT_TABLE_FIELDS.field_location}) VALUES(?, ?, ?, ?)'
    run_query_noreturn(conn, query, (identity, _time, _date, _location))

def create_alert(conn, identity, _date, _time, _location):
    
    row_id, prev_alert_time, prev_location = get_previous_alert(conn, identity, _date)
    run_insert_alert = True

    if prev_alert_time:
        if prev_location == _location:
            if (_time - prev_alert_time).seconds > int(CONFIG['ALERTS']['alert_interval']):
                update_alert(conn, _time, row_id)
            run_insert_alert = False
    
    if run_insert_alert:
        insert_alert(conn, identity, _time, _date, _location)

def check_faces(conn, identity, _date, _time, _location, online):
    
    rows = get_person_log(conn, identity=identity, _date=_date, _location=_location, online=online)
    if not rows:
        create_person_log(conn, identity, _date=_date, in_time=_time, first_location=_location, online=online)
    else:
#         print("rows last: ",rows)
        #update_person_log(conn, rows[0], identity, _date, _time, _location, online=online)
        add_person_log(conn, rows[-1], identity, _date, _time, _location, online=online)
    
    # Check alert and then update
    if online:
        res=get_threat_status(conn, identity)
        if res==None:
            return 'welcome'
        threat_status = res[0]
        if threat_status == 'y':
            create_alert(conn, identity=identity, _date=_date, _time=_time, _location=_location)
            return 'guard'
        else:
            return 'welcome'

def update_fractions(conn, identity, value):
    
    query = f'UPDATE {OFFLINE_LOG_TABLE_FIELDS.table_name} SET {OFFLINE_LOG_TABLE_FIELDS.field_duration_seen} = ? WHERE {OFFLINE_LOG_TABLE_FIELDS.field_identity} = ?'
    values = (value, identity)
    run_query_noreturn(conn, query, values)

def check_username_for_login(conn, username):

    query = f'SELECT {USER_TABLE_FIELDS.field_username} FROM {USER_TABLE_FIELDS.table_name} WHERE {USER_TABLE_FIELDS.field_username} = ?'
    values = (username, )

    vals = run_fetch_query(conn, query, values, fetch_type='one')

    if vals is None:
        return False
    else:
        return True

def retrieve_user_info(conn, username):
    query = f'SELECT {USER_TABLE_FIELDS.field_password}, {USER_TABLE_FIELDS.field_role} FROM {USER_TABLE_FIELDS.table_name} WHERE {USER_TABLE_FIELDS.field_username} = ?'
    values = (username, )

    vals = run_fetch_query(conn, query, values, fetch_type='one')
    if vals:
        return vals[0], vals[1]
    else:
        return None, None

def register_person(face_db_connection, person_db_connection, user_id, user_name, threat, shift, basename, vector):
    
    person_detail_query = f'INSERT INTO {PEOPLE_TABLE_FIELDS.table_name}({PEOPLE_TABLE_FIELDS.field_identity}, {PEOPLE_TABLE_FIELDS.field_name}, {PEOPLE_TABLE_FIELDS.field_threat}, {PEOPLE_TABLE_FIELDS.field_shift}) VALUES(?, ?, ?, ?)'
    face_db_identity_query = f'INSERT INTO {IDENTITY_TABLE_FIELDS.table_name}({IDENTITY_TABLE_FIELDS.field_identity}, {IDENTITY_TABLE_FIELDS.field_entry}) VALUES(?, ?)'
    face_db_vectors_query = f'INSERT INTO {VECTORS_TABLE_FIELDS.table_name}({VECTORS_TABLE_FIELDS.field_label}, {VECTORS_TABLE_FIELDS.field_identity}, {VECTORS_TABLE_FIELDS.field_vector}) VALUES(?, ?, ?)'

    c1 = run_query_noreturn(person_db_connection, person_detail_query, (user_id, user_name, threat, shift))
    c2 = run_query_noreturn(face_db_connection, face_db_identity_query, (user_id, ''))

    c3 = False
    if c1 and c2:
        c3 = run_query_noreturn(face_db_connection, face_db_vectors_query, (basename, user_id, vector))

    return c3

def is_face_exists(person_db_connection, userid):

    query = f'SELECT {PEOPLE_TABLE_FIELDS.field_identity} FROM {PEOPLE_TABLE_FIELDS.table_name} WHERE {PEOPLE_TABLE_FIELDS.field_identity} = ?'
#     query = f'SELECT id FROM [{PEOPLE_TABLE_FIELDS.table_name}] WHERE {PEOPLE_TABLE_FIELDS.field_identity} = ?'

    row = run_fetch_query(person_db_connection, query, (userid,), fetch_type='all')
    #print(f'fetched users for query and value = {query} ------ {userid}', row)
    if row!=None:
        return len(row) > 0
    else:
        return True
    
def search_all(face_db_connection, person_db_connection):

    query = f'SELECT * FROM {PEOPLE_TABLE_FIELDS.table_name}'

    
    person_details = run_fetch_query(person_db_connection, query)
    fd = {}

    if person_details is not None:
        face_detail_query = f'SELECT {VECTORS_TABLE_FIELDS.field_label} FROM {VECTORS_TABLE_FIELDS.table_name} WHERE {VECTORS_TABLE_FIELDS.field_identity} = ?'
        for user_id, _, _, _ in person_details:
            face_details = run_fetch_query(face_db_connection, face_detail_query, (user_id,))
            fd[user_id] = face_details

    return person_details, fd

def search_by(face_db_connection, person_db_connection, colname, value, exact):
    if exact:
        query = f'SELECT * FROM {PEOPLE_TABLE_FIELDS.table_name} WHERE {colname} = ?'
        search_tuple = (value, )
    else:
        query = f'SELECT * FROM {PEOPLE_TABLE_FIELDS.table_name} WHERE {colname} LIKE ?'
        search_tuple = (f'%{value}%', )

    person_details = run_fetch_query(person_db_connection, query, search_tuple, fetch_type='all')
    fd = {}

    if person_details is not None:
        face_detail_query = f'SELECT {VECTORS_TABLE_FIELDS.field_label} FROM {VECTORS_TABLE_FIELDS.table_name} WHERE {VECTORS_TABLE_FIELDS.field_identity} = ?'

        for user_id, _, _, _ in person_details:
            face_details = run_fetch_query(face_db_connection, face_detail_query, (user_id,))
            fd[user_id] = face_details
        
    return person_details, fd

def search_by_id(face_db_connection, person_db_connection, value, exact):
    return search_by(face_db_connection, person_db_connection, PEOPLE_TABLE_FIELDS.field_identity, value, exact)


def search_by_name(face_db_connection, person_db_connection, value, exact):
    return search_by(face_db_connection, person_db_connection, PEOPLE_TABLE_FIELDS.field_name, value, exact)

def update_threat_status(person_db_connection, _id, status):

    query = f'UPDATE {PEOPLE_TABLE_FIELDS.table_name} SET {PEOPLE_TABLE_FIELDS.field_threat}=? WHERE {PEOPLE_TABLE_FIELDS.field_identity} = ?'
    run_query_noreturn(person_db_connection, query, (status, _id))

def update_shifts(person_db_connection, _id, shift):

    query = f'UPDATE {PEOPLE_TABLE_FIELDS.table_name} SET {PEOPLE_TABLE_FIELDS.field_shift}=? WHERE {PEOPLE_TABLE_FIELDS.field_identity} = ?'
    run_query_noreturn(person_db_connection, query, (shift, _id))

def delete_user(face_db_connection, person_db_connection, _id):
    
    person_detail_query = f'DELETE FROM {PEOPLE_TABLE_FIELDS.table_name} WHERE {PEOPLE_TABLE_FIELDS.field_identity} = ?'
    face_db_identity_query = f'DELETE FROM {IDENTITY_TABLE_FIELDS.table_name} WHERE {IDENTITY_TABLE_FIELDS.field_identity} = ?'
    face_db_vector_query = F'DELETE FROM {VECTORS_TABLE_FIELDS.table_name} WHERE {VECTORS_TABLE_FIELDS.field_identity} = ?'

    run_query_noreturn(person_db_connection, person_detail_query, (_id,))
    run_query_noreturn(face_db_connection, face_db_vector_query, (_id,))
    run_query_noreturn(face_db_connection, face_db_identity_query, (_id,))

def create_report_in_range(person_db_connection, for_user=None, user_name=None, start_date=None, end_date=None, location=None, recog_mode='online'):
    
    table2 = PEOPLE_TABLE_FIELDS.table_name

    if recog_mode == 'online':
        table1 = ONLINE_LOG_TABLE_FIELDS.table_name
        column_order = ['A.entry_no', 'B.name', 'B.threat', 'A.InTime', 'A.OutTime', 'A.FirstLocation', 'A.LastSeenLocation']

    elif recog_mode == 'offline':
        table1 = OFFLINE_LOG_TABLE_FIELDS.table_name
        column_order = ['A.entry_no', 'B.name', 'B.threat', 'A.InTime', 'A.OutTime', 'A.FileName', 'A.DurationSeen']

    partial_query = [
        'SELECT',
        ', '.join(column_order),
        'FROM', table1, 'AS A',
        'INNER JOIN', table2, 'AS B',
        'ON A.entry_no = B.entry_no'
    ]

    where_clause = []
    search_tuple = []

    if location:
        if recog_mode == 'online':
            where_clause.append('(A.FirstLocation LIKE ? B.LastSeenLocation LIKE ?)')
            search_tuple.append(f'%{location}%')
            search_tuple.append(f'%{location}%')
        
        if recog_mode == 'offline':
            where_clause.append('A.FileName LIKE ?')
            search_tuple.append(f'%{location}%')
    
    if start_date:
        if recog_mode == 'online':
            where_clause.append(f'A.Date >= ?')
        if recog_mode == 'offline':
            where_clause.append(f'A.RunDate >=?')
        search_tuple.append(start_date)

    if end_date:
        if recog_mode == 'online':
            where_clause.append(f'A.Date <= ?')
        if recog_mode == 'offline':
            where_clause.append(f'A.RunDate <= ?')
        search_tuple.append(end_date)

    if for_user:
        where_clause.append(f'A.entry_no = ?')
        search_tuple.append(for_user)

    if user_name:
        where_clause.append(f'B.name LIKE ?')
        search_tuple.append(f'%{user_name}%')

    where_clause_string = ' AND '.join(where_clause)
    query = ' '.join(partial_query + ['WHERE', where_clause_string])

    res = run_fetch_query(person_db_connection, query=query, values=tuple(search_tuple))
    column_names = ['.'.join(v.split('.')[1:]) for v in column_order]
    res = DataFrame(res, columns=column_names)

    return res

def fetch_alerts(person_db_connection, start_date, end_date, user_id=None):

    alert_query = f'SELECT * FROM {ALERT_TABLE_FIELDS.table_name} WHERE {ALERT_TABLE_FIELDS.field_date} >= ? AND {ALERT_TABLE_FIELDS.field_date} <= ?'
    condition_values = [start_date, end_date]

    if user_id:
        alert_query += f' AND {ALERT_TABLE_FIELDS.field_identity} = ?'
        condition_values.append(user_id)

    res = run_fetch_query(person_db_connection, alert_query, condition_values)

    if res:
        res_df = DataFrame(res, columns=['sid', 'user_id', 'datetime', 'date', 'location'])
        unique_user_ids = res_df['user_id'].unique()
    else:
        res_df = DataFrame([])
        unique_user_ids = []
    
    return res_df, unique_user_ids

def get_cameras_from_db(person_db_connection):

    result = []
    for colname in [ONLINE_LOG_TABLE_FIELDS.field_first_location, ONLINE_LOG_TABLE_FIELDS.field_last_seen_location]:
        query = f'SELECT DISTINCT {colname} FROM {ONLINE_LOG_TABLE_FIELDS.table_name}'
        res = run_fetch_query(person_db_connection, query)
        for v in res:
            result.append(v[0])
    
    return unique(result).tolist()

def get_videos_from_db(person_db_connection):
    
    query = f'SELECT DISTINCT {OFFLINE_LOG_TABLE_FIELDS.field_filename} FROM {OFFLINE_LOG_TABLE_FIELDS.table_name}'
    res = run_fetch_query(person_db_connection, query)
    result = [v[0] for v in res]

    return result

def get_roster_from_db(person_db_connection):

    query = f'SELECT * FROM {ROSTER_TABLE_FIELDS.table_name}'
    res = run_fetch_query(person_db_connection, query)
    return res

def get_shift_timing_from_db(person_db_connection, shift_id):

    query = f'SELECT * FROM {ROSTER_TABLE_FIELDS.table_name} WHERE {ROSTER_TABLE_FIELDS.field_row_id} = ?'
    res = run_fetch_query(person_db_connection, query, values=(shift_id,), fetch_type='one')
    return res

def insert_operator_info(auth_db_connection, operator_id, operator_pass, operator_name, operator_role):
    
    fetch_query = f'SELECT {USER_TABLE_FIELDS.field_username} FROM {USER_TABLE_FIELDS.table_name} where {USER_TABLE_FIELDS.field_username} = ?'
    res = run_fetch_query(auth_db_connection, fetch_query, (operator_id,), fetch_type='one')
    if res is None:

        query = f'INSERT INTO {USER_TABLE_FIELDS.table_name}({USER_TABLE_FIELDS.field_username}, {USER_TABLE_FIELDS.field_password}, {USER_TABLE_FIELDS.field_role}, {USER_TABLE_FIELDS.field_name}) VALUES(?, ?, ?, ?)'
        run_query_noreturn(auth_db_connection, query, (operator_id, operator_pass, operator_role, operator_name))
        return True

    return False

def search_operator_by_name(auth_db_connection, operator_name):
    
    fetch_query = f'SELECT * FROM {USER_TABLE_FIELDS.table_name} WHERE {USER_TABLE_FIELDS.field_name} LIKE ?'
    res = run_fetch_query(auth_db_connection, fetch_query, (f'%{operator_name}%',))
    return res

def search_operator_by_username(auth_db_connection, operator_username):
    
    fetch_query = f'SELECT * FROM {USER_TABLE_FIELDS.table_name} WHERE {USER_TABLE_FIELDS.field_username} LIKE ?'
    res = run_fetch_query(auth_db_connection, fetch_query, (f'%{operator_username}%',))
    return res

def update_operator(auth_db_connection, field_name, value_tuple):

    if field_name == 'role':
        query = f'UPDATE {USER_TABLE_FIELDS.table_name} SET {USER_TABLE_FIELDS.field_role} = ? WHERE {USER_TABLE_FIELDS.field_username} = ?'
        run_query_noreturn(auth_db_connection, query, value_tuple)

def delete_operator(auth_db_connection, opt):

    query = f'DELETE FROM {USER_TABLE_FIELDS.table_name} WHERE {USER_TABLE_FIELDS.field_username} = ?'
    return run_query_noreturn(auth_db_connection, query, (opt,))

def update_operator_password(auth_db_connection, operator_id, operator_passwd):

    query = f'UPDATE {USER_TABLE_FIELDS.table_name} SET {USER_TABLE_FIELDS.field_password} = ? WHERE {USER_TABLE_FIELDS.field_username} = ?'
    return run_query_noreturn(auth_db_connection, query, (operator_passwd, operator_id))

def add_roster_to_db(person_db_connection, rid, name, start_time, end_time):
    query=f'SELECT * FROM {ROSTER_TABLE_FIELDS.table_name} WHERE {ROSTER_TABLE_FIELDS.field_name} = ?'
    rows=run_fetch_query(person_db_connection, query,(name,))
    if len(rows)>0:
        return -1

    query = f'INSERT INTO {ROSTER_TABLE_FIELDS.table_name}({ROSTER_TABLE_FIELDS.field_row_id}, {ROSTER_TABLE_FIELDS.field_name}, {ROSTER_TABLE_FIELDS.field_starttime}, {ROSTER_TABLE_FIELDS.field_endtime}) VALUES(?, ?, ?, ?)'
    return run_query_noreturn(person_db_connection, query, (rid, name, start_time, end_time))

