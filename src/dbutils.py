#Make sure UTILS file never imports CONFIG

from hashlib import md5

import sqlite3
from sqlite3 import Error

from .global_vars import DEVELOPER_MODE, DEBUG_MODE
from .messages import DB_CONNECT_FAILED_STRING

def create_connection(db_file, check_same_thread=True):

    conn = None
    try:
        conn = sqlite3.connect(db_file, check_same_thread=check_same_thread)
    except Error as e:
        if DEVELOPER_MODE:
            print(f'[create_connection] {e}')
        else:
            print(f'{DB_CONNECT_FAILED_STRING} {db_file}')

    return conn


def run_query(db_file, query, query_type='', values=(), fetch_type='all'):

    conn = create_connection(db_file)
    if conn:
        if query_type == 'fetch':
            ret = run_fetch_query(conn, query, values, fetch_type=fetch_type)
        else:
            ret = run_query_noreturn(conn, query, values)
        conn.close()
        return ret
    else:
        return None
    

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

def run_query_noreturn(conn, query, values=()):

    try:
        curr = conn.cursor()
        curr.execute(query, values)
        conn.commit()
        return True
    except Exception as e:
        if DEVELOPER_MODE:
            print(f'[run_query_noreturn]: {e}')
        else:
            print('An Error Occured')
        
        conn.rollback()
        return False


def encrypt(password):

    password = password.encode('utf-8')
    return md5(password).hexdigest()