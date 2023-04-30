from .load_config import CONFIG
from .dbutils import run_query
# from .global_vars import ONLINE_LOG_TABLE_FIELDS, PEOPLE_TABLE_FIELDS
from datetime import date as datemodule, timedelta
import pandas as pd
import numpy as np
import xlsxwriter
import os

def write_report(report, path, sheet_name=None, banner_suffix=''):
    #report.to_excel(path)

    if sheet_name is None:
        sheet_name = os.path.splitext(os.path.basename(path))[0]

    workbook = xlsxwriter.Workbook(path)
    worksheet = workbook.add_worksheet(sheet_name)

    label_format = workbook.add_format({'bold': True, 'bg_color': 'yellow','align':'center','border_color':'black','border':1})
    entry_format = workbook.add_format({'indent':1,'align':'center','num_format':'General'})
    number_entry_format = workbook.add_format({'indent':1,'align':'center','num_format':'dd/mm/yy hh:mm AM/PM'})
    entry_format_warning = workbook.add_format({'indent':1,'align':'center','num_format':'General', 'bg_color': 'red', 'font_color': 'white'})
    number_entry_format_warning = workbook.add_format({'indent':1,'align':'center','num_format':'General', 'bg_color': 'red', 'font_color': 'white'})

    worksheet.set_column(0, 6, 30)

    worksheet.insert_image('D1', CONFIG['REPORT']['report_logo'], {'x_offset': -105, 'y_offset': 0})

    banner = CONFIG['REPORT']['report_banner']
    if banner_suffix != '':
        banner = f'{banner} {banner_suffix}'

    worksheet.write('C4', banner)

    headings_row = 5
    headings_col = 0
    headings = report.columns

    threat_ind = np.where(headings == 'threat')[0]

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
            nb_format = number_entry_format
            ef = entry_format

        entry_col = 0
        for index, i in enumerate(row):
            if(index in [3, 4]):
                worksheet.write(entry_row, entry_col, i, nb_format)
            else:
                worksheet.write(entry_row, entry_col, i, ef)
            entry_col+=1
        entry_row += 1
    workbook.close()

def write_alerts(report, path, sheet_name=None, banner_suffix=''):

    if sheet_name is None:
        sheet_name = os.path.splitext(os.path.basename(path))[0]

    workbook = xlsxwriter.Workbook(path)
    worksheet = workbook.add_worksheet(sheet_name)

    label_format = workbook.add_format({'bold': True, 'bg_color': 'yellow','align':'center','border_color':'black','border':1})
    entry_format = workbook.add_format({'indent':1,'align':'center','num_format':'General'})
    number_entry_format = workbook.add_format({'indent':1,'align':'center','num_format':'dd/mm/yy hh:mm AM/PM'})
    worksheet.set_column(0, 6, 30)

    worksheet.insert_image('D1', CONFIG['REPORT']['report_logo'], {'x_offset': -105, 'y_offset': 0})

    banner = CONFIG['ALERTS']['alert_banner']
    if banner_suffix != '':
        banner = f'{banner} {banner_suffix}'

    worksheet.write('C4', banner)

    headings_row = 5
    headings_col = 0
    headings = report.columns

    for name in headings:
        worksheet.write(headings_row, headings_col, name, label_format)
        headings_col += 1
    entry_row = 6

    data = report.values
    for row in data:
        entry_col = 0
        for index, i in enumerate(row):
            if(index in [3, 4]):
                worksheet.write(entry_row, entry_col, i, number_entry_format)
            else:
                worksheet.write(entry_row, entry_col, i, entry_format)
            entry_col+=1
        entry_row += 1
    workbook.close()

# def create_report(store=False):
    
#     db_file = CONFIG['DB']['person_db']
#     report_type = CONFIG['REPORT']['type']

#     if report_type == 'history':
#         date = datemodule.today() - timedelta(int(CONFIG['REPORT']['history']))
#     if report_type == 'date':
#         date = CONFIG['REPORT']['date']
    
#     table1 = ONLINE_LOG_TABLE_FIELDS.table_name
#     table2 = PEOPLE_TABLE_FIELDS.table_name

#     column_order = ['A.entry_no', 'B.name', 'B.threat', 'A.InTime', 'A.OutTime', 'A.FirstLocation', 'A.LastSeenLocation']

#     query = ' '.join([
#        'SELECT', ', '.join(column_order),
#        'FROM', table1, 'AS A',
#        'INNER JOIN', table2, 'AS B',
#        'ON A.entry_no = B.entry_no',
#        'WHERE A.Date = ?'
#     ])

#     res = run_query(db_file=db_file, query=query, query_type='fetch', values=(date,))
#     column_names = ['.'.join(v.split('.')[1:]) for v in column_order]
#     res = pd.DataFrame(res, columns=column_names)

#     if store:
#         report_folder = CONFIG['REPORT']['report_path']
#         filename = os.path.join(report_folder, f'report_{date}.xlsx')
#         write_report(res, filename, sheet_name=f'report_{date}')

#     return res


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



