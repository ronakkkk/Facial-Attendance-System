import pandas as pd
import numpy as np
from .dbutils import create_connection
from .load_config import CONFIG
from .dbutils import run_fetch_query, run_query_noreturn

import random, string, os
from .report import write_report

from datetime import datetime,timedelta,date
from calendar import monthrange
import xlsxwriter


def write_report_all_logs(df, path, filename='report.xlsx', query='' , banner_suffix=''):
    '''
    @param- 
    df: takes a df with properly defined datatypes for number, dates and string
    path: xls file path
    filename: xls file name
    query: string of values of a query in case of a conditional query search
    banner_suffix: duration of log collected and passed in df

    '''
    path = os.path.join(path,filename)
    # print("path",path)
    writer_object = pd.ExcelWriter(path, engine ='xlsxwriter')
    df.to_excel(writer_object, sheet_name ='logs', startrow = 6, startcol = 0, index = False)

    workbook_object = writer_object.book #for formatting
    worksheet  = writer_object.sheets['logs']

    worksheet.set_column(0, 12, 30)
    worksheet.insert_image('D1', CONFIG['REPORT']['report_logo'], {'x_offset': -105, 'y_offset': 0})

    banner = CONFIG['REPORT']['report_banner_all_logs']
    # if query != '':
    #     banner = f'{banner} {banner_suffix} {query}'
    # else:
    banner = f'{banner} {banner_suffix}'
    worksheet.write('C4', banner)
    if query!='':
        worksheet.write('C5', query)

    header_format_object = workbook_object.add_format({ 'bold': True,
                                                        'bg_color': 'yellow',
                                                        'align':'center',
                                                        'border_color':'black',
                                                        'border': 1})
    
    entry_format = workbook_object.add_format({ 'indent':1,
                                                'align':'center',
                                                'num_format':'General'})
    number_entry_format = workbook_object.add_format({ 'indent':1,
                                                        'align':'center',
                                                        'num_format':'dd/mm/yy hh:mm AM/PM'})
    
    entry_format_warning = workbook_object.add_format({ 'indent':1,
                                                        'align':'center',
                                                        'num_format':'General',
                                                        'bg_color': 'red',
                                                        'font_color': 'white'})
    
    number_entry_format_warning = workbook_object.add_format({'indent':1,
                                                            'align':'center',
                                                            'num_format':'General',
                                                            'bg_color': 'red',
                                                            'font_color': 'white'})
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(6, col_num, value, header_format_object)

    writer_object.save()
    writer_object.close()

def write_report_working_hours(df, path, filename='report.xlsx', query='' , banner_suffix=''):
    '''
    @param- 
    df: takes a df with properly defined datatypes for number, dates and string
    path: xls file path
    filename: xls file name
    query: string of values of a query in case of a conditional query search
    banner_suffix: duration of log collected and passed in df

    '''
    path = os.path.join(path,filename)
    # print("workhourpath",path)
    writer_object = pd.ExcelWriter(path, engine ='xlsxwriter')
    df.to_excel(writer_object, sheet_name ='working_hours_log', startrow = 6, startcol = 0, index = False)
    workbook_object = writer_object.book #for formatting
    worksheet  = writer_object.sheets['working_hours_log']

    worksheet.set_column(0, 12, 30)
    worksheet.insert_image('D1', CONFIG['REPORT']['report_logo'], {'x_offset': -105, 'y_offset': 0})
    
    banner = CONFIG['REPORT']['report_banner_work_hour_log']
    # if query != '':
    #     banner = f'{banner} {banner_suffix} {query}'
    # else:
    #     banner_suffix = f'{banner} {banner_suffix}'
    # worksheet.write('C4', banner)
    banner = f'{banner} {banner_suffix}'
    worksheet.write('C4', banner)
    if query!='':
        worksheet.write('C5', query)

    
    header_format_object = workbook_object.add_format({ 'bold': True,
                                                        'bg_color': 'yellow',
                                                        'align':'center',
                                                        'border_color':'black',
                                                        'border': 1})
    
    entry_format = workbook_object.add_format({ 'indent':1,
                                                'align':'center',
                                                'num_format':'General'})
    
    number_entry_format = workbook_object.add_format({ 'indent':1,
                                                        'align':'center',
                                                        'num_format':'dd/mm/yy hh:mm AM/PM'})
    
    entry_format_warning = workbook_object.add_format({ 'indent':1,
                                                        'align':'center',
                                                        'num_format':'General',
                                                        'bg_color': 'red', 
                                                        'font_color': 'white'})
    
    number_entry_format_warning = workbook_object.add_format({'indent':1,
                                                            'align':'center',
                                                            'num_format':'General', 
                                                            'bg_color': 'red',
                                                            'font_color': 'white'})
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(6, col_num, value, header_format_object)

    writer_object.save()
    writer_object.close()

def write_report_daily(df, path, filename='report.xlsx', query='', banner_suffix=''):
    '''
    @param- 
    df: takes a df with properly defined datatypes for number, dates and string
    path: xls file path
    filename: xls file name
    query: string of values of a query in case of a conditional query search
    banner_suffix: duration of log collected and passed in df

    '''
    path = os.path.join(path,filename)
    print("daily report path",path)
    writer_object = pd.ExcelWriter(path, engine ='xlsxwriter')
    df.to_excel(writer_object, sheet_name ='daily_report', startrow = 6, startcol = 0, index = False)

    number_rows = len(df.index) + 7
    no_of_columns = df.shape[1]
    last_col = chr(ord('@')+no_of_columns)

    workbook_object = writer_object.book #for formatting
    worksheet  = writer_object.sheets['daily_report']

    worksheet.set_column(0, 12, 30)
    worksheet.insert_image('D1', CONFIG['REPORT']['report_logo'], {'x_offset': -105, 'y_offset': 0})

    banner = CONFIG['REPORT']['report_banner_daily_work_hour_log']
    # if query != '':
    #     banner = f'{banner} {banner_suffix} {query}'
    # else:
    #     banner_suffix = f'{banner} {banner_suffix}'
    # worksheet.write('C4', banner)
    banner = f'{banner} {banner_suffix}'
    worksheet.write('C4', banner)
    if query!='':
        worksheet.write('C5', query)


    header_format_object = workbook_object.add_format({ 'bold': True,
                                                        'bg_color': 'yellow',
                                                        'align':'center',
                                                        'border_color':'black',
                                                        'border': 1})
    
    entry_format = workbook_object.add_format({ 'indent':1,
                                                'align':'center',
                                                'num_format':'General'})
    
    number_entry_format = workbook_object.add_format({ 'indent':1,
                                                        'align':'center',
                                                        'num_format':'dd/mm/yy hh:mm AM/PM'})
    
    entry_format_warning = workbook_object.add_format({ 'indent':1,
                                                        'align':'center',
                                                        'num_format':'General',
                                                        'bg_color': 'red',
                                                        'font_color': 'white'})
    
    number_entry_format_warning = workbook_object.add_format({'indent':1,
                                                                'align':'center',
                                                                'num_format':'General',
                                                                'bg_color': 'red',
                                                                'font_color': 'white'})

    late_format = workbook_object.add_format({'indent':1,
                                                'align':'center',
                                                'num_format':'General',
                                                'bg_color': '#FF0066',#,'#ff1493',
                                                'font_color': 'white',
                                                'border_color':'black',
                                                'border': 1,})

    status_col_num = df.columns.tolist().index('STATUS')+1
    status_col = chr(ord('@')+status_col_num)
    x = 7
    worksheet.conditional_format("$A$7:$%s$%d" % (last_col,number_rows), {'type': 'formula',
                                       'criteria': f'=LEFT($L{str(x)}, 10)="Late Comer"',
                                       'format': late_format})

    early_leaver_format = workbook_object.add_format({'indent':1,
                                                'border_color':'black',
                                                'align':'center',
                                                'border': 1,
                                                'num_format':'General',
                                                'bg_color': '#002060',#'#012060',
                                                'font_color': 'white'})

    worksheet.conditional_format("$A$7:$%s$%d" % (last_col,number_rows), {'type': 'formula',
                                       'criteria': f'=LEFT($L{str(x)}, 12)="Early Leaver"',
                                       'format': early_leaver_format})

    mispunched_format = workbook_object.add_format({'indent':1,
                                                    'border_color':'black',
                                                    'align':'center',
                                                    'border': 1,
                                                    'num_format':'General',
                                                    'bg_color': '#0D0D0D',
                                                    'font_color': 'white'})

    worksheet.conditional_format("$A$7:$%s$%d" % (last_col,number_rows), {'type': 'formula',
                                       'criteria': f'=LEFT($L{str(x)}, 10)="Mispunched"',
                                       'format': mispunched_format})

    present_format = workbook_object.add_format({'indent':1,
                                                    'border_color':'black',
                                                    'align':'center',
                                                    'border': 1,
                                                    'num_format':'General',
                                                    'bg_color': '#92D050',
                                                    'font_color': 'black'})

    worksheet.conditional_format("$A$7:$%s$%d" % (last_col,number_rows), {'type': 'formula',
                                       'criteria': f'=LEFT($L{str(x)}, 7)="Present"',
                                       'format': present_format})

    full_day_leave_format = workbook_object.add_format({'indent':1,
                                                'border_color':'black',
                                                'align':'center',
                                                'border': 1,
                                                'num_format':'General',
                                                'bg_color': '#7030A0',
                                                'font_color': '#FFC000'})#'#ffc87c'})

    worksheet.conditional_format("$A$7:$%s$%d" % (last_col,number_rows), {'type': 'formula',
                                       'criteria': f'=LEFT($L{str(x)}, 14)="Full Day Leave"',
                                       'format': full_day_leave_format})

    half_day_leave_format = workbook_object.add_format({'indent':1,
                                                        'border_color':'black',
                                                        'align':'center',
                                                        'border': 1,
                                                        'num_format':'General', 
                                                        'bg_color': '#FFC000',#ffc87c', 
                                                        'font_color': '#7030A0'})

    worksheet.conditional_format("$A$7:$%s$%d" % (last_col,number_rows), {'type': 'formula',
                                       'criteria': f'=LEFT($L{str(x)}, 14)="Half Day Leave"',
                                       'format': half_day_leave_format})

    full_day_absent_format = workbook_object.add_format({'indent':1,
                                                        'border_color':'black',
                                                        'align':'center',
                                                        'border': 1,
                                                        'num_format':'General',
                                                        'bg_color': '#ff0000',
                                                        'font_color': 'white'})

    worksheet.conditional_format("$A$7:$%s$%d" % (last_col,number_rows), {'type': 'formula',
                                       'criteria': f'=LEFT($L{str(x)}, 15)="Full Day Absent"',
                                       'format': full_day_absent_format})

    good_work_format = workbook_object.add_format({'indent':1,
                                                    'border_color':'black',
                                                    'align':'center',
                                                    'border': 1,
                                                    'num_format':'General', 
                                                    'bg_color': '#00FFFF',#'#01FFFF', 
                                                    'font_color': 'black'})

    worksheet.conditional_format("$A$7:$%s$%d" % (last_col,number_rows), {'type': 'formula',
                                       'criteria': f'=LEFT($L{str(x)}, 12)="Good Working"',
                                       'format': good_work_format})
    
    weekly_off_format = workbook_object.add_format({'indent':1,
                                                'border_color':'black',
                                                'align':'center',
                                                'border': 1,
                                                'num_format':'General',
                                                'bg_color': '#FFFF00',#'#ffff66',
                                                'font_color': 'black'})

    worksheet.conditional_format("$A$7:$%s$%d" % (last_col,number_rows), {'type': 'formula',
                                       'criteria': f'=LEFT($L{str(x)}, 12)="Weekly Off"',
                                       'format': weekly_off_format})

    department_holiday_format = workbook_object.add_format({'indent':1,
                                                    'border_color':'black',
                                                    'align':'center',
                                                    'border': 1,
                                                    'num_format':'General',
                                                    'bg_color': '#EAEAEA',
                                                    'font_color': 'black'})

    worksheet.conditional_format("$A$7:$%s$%d" % (last_col,number_rows), {'type': 'formula',
                                       'criteria': f'=LEFTd($L{str(x)}, 12)="Department Holiday"',
                                       'format': department_holiday_format})
    
    company_holiday_format = workbook_object.add_format({'indent':1,
                                                    'border_color':'black',
                                                    'align':'center',
                                                    'border': 1,
                                                    'num_format':'General',
                                                    'bg_color': '#FFFFFF',
                                                    'font_color': 'black'})

    worksheet.conditional_format("$A$7:$%s$%d" % (last_col,number_rows), {'type': 'formula',
                                       'criteria': f'=LEFTd($L{str(x)}, 12)="Company Holiday"',
                                       'format': company_holiday_format})


    for col_num, value in enumerate(df.columns.values):
        worksheet.write(6, col_num, value, header_format_object)

    writer_object.save()
    writer_object.close()    

def write_report_monthly(df, path, filename='report.xlsx', query='', banner_suffix=''):
    '''
    @param- 
    df: takes a df with properly defined datatypes for number, dates and string
    path: xls file path
    filename: xls file name
    query: string of values of a query in case of a conditional query search
    banner_suffix: duration of log collected and passed in df

    '''
    legend_df_1 = pd.DataFrame({'Key':['P','HDL', 'FDL', 'A'],
        'Value': ['Present', 'Half Day Leave', 'Full Day Leave', 'Absent']})

    legend_df_2 = pd.DataFrame({'Key':['WO','CHO','DHO', 'GWD'],
        'Value': ['Weekly Off','Company Holiday', 'Department Holiday', 'Good Working Day']})
    
    legend_df_3 = pd.DataFrame({'Key':['LC', 'EL', 'MP'],
        'Value': ['Late Comer', 'Early Leaver', 'Mispunched']})
    
    path = os.path.join(path,filename)
    print("monthly report path",path)
    writer_object = pd.ExcelWriter(path, engine ='xlsxwriter')
    df.to_excel(writer_object, sheet_name ='monthly_report', startrow = 9, startcol = 0, index = False)
    legend_df_1.to_excel(writer_object, sheet_name ='monthly_report', startrow = 2, startcol = 13, header = False, index = False)
    legend_df_2.to_excel(writer_object, sheet_name ='monthly_report', startrow = 2, startcol = 18, header = False, index = False)
    legend_df_3.to_excel(writer_object, sheet_name ='monthly_report', startrow = 2, startcol = 23, header = False, index = False)

    number_rows = len(df.index) + 10
    no_of_columns = df.shape[1]
    first_letter_of_last_col = int(no_of_columns/26)
    last_letter_of_last_col = int(no_of_columns%26)
    last_col = chr(ord('@')+first_letter_of_last_col)+chr(ord('@')+last_letter_of_last_col)

    workbook_object = writer_object.book #for formatting
    worksheet  = writer_object.sheets['monthly_report']

    # To be used in case auto-width of columns are in dire need. 
    # def get_col_widths(dataframe):
       #  # First we find the maximum length of the index column   
       #  idx_max = max([len(str(s)) for s in dataframe.index.values] + [len(str(dataframe.index.name))])
       #  # Then, we concatenate this to the max of the lengths of column name and its values for each column, left to right
       #  return [idx_max] + [max([len(str(s)) for s in dataframe[col].values] + [len(col)]) for col in dataframe.columns]

    # for i, width in enumerate(get_col_widths(df)):
    #   worksheet.set_column(i, i, width)

    worksheet.set_column(0, 4, 20)
    worksheet.set_column(len(df.columns)-12, len(df.columns)-1, 20)
    
    worksheet.insert_image('D1', CONFIG['REPORT']['report_logo'], {'x_offset': -105, 'y_offset': 0})

    banner = CONFIG['REPORT']['report_banner_monthly_logs']
    # if query != '':
    #     banner = f'{banner} {banner_suffix} {query}'
    # else:
    #     banner_suffix = f'{banner} {banner_suffix}'
    # worksheet.write('C4', banner)
    banner = f'{banner} {banner_suffix}'
    worksheet.write('C4', banner)
    if query!='':
        worksheet.write('C5', query)


    header_format_object = workbook_object.add_format({ 'bold': True,
                                                        'bg_color': 'yellow',
                                                        'align':'center',
                                                        'border_color':'black',
                                                        'border': 1})
    
    entry_format = workbook_object.add_format({ 'indent':1,
                                                'align':'center',
                                                'num_format':'General',
                                                'bg_color': '#D9D9D9',#'#d3d3d3',
                                                'align':'center',
                                                'border_color':'black',
                                                'border': 1})
    # print(df.index, number_rows)

    worksheet.conditional_format("$A$10:$E$%d" % (number_rows),{'type': 'no_blanks','format': entry_format})
    
    worksheet.conditional_format("$A$10:$E$%d" % (number_rows),{'type': 'blanks','format': entry_format})

    late_format = workbook_object.add_format({'indent':1,
                                                'align':'center',
                                                'num_format':'General',
                                                'bg_color': '#FF0066',#'#ff1493',
                                                'font_color': 'white',
                                                'border_color':'black',
                                                'border': 1,})

    worksheet.conditional_format("$A$3:$%s$%d" % (last_col,number_rows), {'type': 'text',
                                       'criteria':'containing',
                                       'value': 'LC',
                                       'format': late_format})

    early_leaver_format = workbook_object.add_format({'indent':1,
                                                'border_color':'black',
                                                'align':'center',
                                                'border': 1,
                                                'num_format':'General',
                                                'bg_color': '#002060',#'#012060',
                                                'font_color': 'white'})

    worksheet.conditional_format("$A$3:$%s$%d" % (last_col,number_rows), {'type': 'text',
                                       'criteria':'containing',
                                       'value': 'EL',
                                       'format': early_leaver_format})


    present_format = workbook_object.add_format({'indent':1,
                                                'border_color':'black',
                                                'align':'center',
                                                'border': 1,
                                                'num_format':'General',
                                                'bg_color': '#92D050',
                                                'font_color': 'black'})

    worksheet.conditional_format("$A$3:$%s$%d" % (last_col,number_rows), {'type': 'cell',
                                       'criteria':'equal to',
                                       'value': '"P"',
                                       'format': present_format})

    full_day_leave_format = workbook_object.add_format({'indent':1,
                                                    'border_color':'black',
                                                    'align':'center',
                                                    'border': 1,
                                                    'num_format':'General',
                                                    'bg_color': '#7030A0',
                                                    'font_color': '#FFC000'})#'#ffc87c'})

    worksheet.conditional_format("$A$3:$%s$%d" % (last_col,number_rows), {'type': 'text',
                                       'criteria':'containing',
                                       'value': 'FDL',
                                       'format': full_day_leave_format})

    half_day_leave_format = workbook_object.add_format({'indent':1,
                                                'border_color':'black',
                                                'align':'center',
                                                'border': 1,
                                                'num_format':'General',
                                                'bg_color': '#FFC000',#'#ffc87c',
                                                'font_color': '#7030A0'})

    worksheet.conditional_format("$A$3:$%s$%d" % (last_col,number_rows), {'type': 'text',
                                       'criteria':'containing',
                                       'value': 'HDL',
                                       'format': half_day_leave_format})

    full_day_absent_format = workbook_object.add_format({'indent':1,
                                                'border_color':'black',
                                                'align':'center',
                                                'border': 1,
                                                'num_format':'General',
                                                'bg_color': '#ff0000',
                                                'font_color': 'white'})

    worksheet.conditional_format("$A$3:$%s$%d" % (last_col,number_rows), {'type': 'cell',
                                       'criteria':'==',
                                       'value': '"A"',
                                       'format': full_day_absent_format})

    good_work_format = workbook_object.add_format({'indent':1,
                                                'border_color':'black',
                                                'align':'center',
                                                'border': 1,
                                                'num_format':'General',
                                                'bg_color': '#00FFFF',#'#01FFFF',
                                                'font_color': 'black'})

    worksheet.conditional_format("$A$3:$%s$%d" % (last_col,number_rows), {'type': 'text',
                                       'criteria':'containing',
                                       'value': 'GWD',
                                       'format': good_work_format})

    weekly_off_format = workbook_object.add_format({'indent':1,
                                                'border_color':'black',
                                                'align':'center',
                                                'border': 1,
                                                'num_format':'General',
                                                'bg_color': '#FFFF00',#'#ffff66',
                                                'font_color': 'black'})

    worksheet.conditional_format("$A$3:$%s$%d" % (last_col,number_rows), {'type': 'text',
                                       'criteria':'begins with',#'containing',
                                       'value': 'WO',
                                       'format': weekly_off_format})

    department_holiday_format = workbook_object.add_format({'indent':1,
                                                    'border_color':'black',
                                                    'align':'center',
                                                    'border': 1,
                                                    'num_format':'General',
                                                    'bg_color': '#EAEAEA',
                                                    'font_color': 'black'})

    worksheet.conditional_format("$A$3:$%s$%d" % (last_col,number_rows), {'type': 'text',
                                       'criteria':'containing',
                                       'value': 'DHO',
                                       'format': department_holiday_format})
    
    company_holiday_format = workbook_object.add_format({'indent':1,
                                                    'border_color':'black',
                                                    'align':'center',
                                                    'border': 1,
                                                    'num_format':'General',
                                                    'bg_color': '#FFFFFF',
                                                    'font_color': 'black'})

    worksheet.conditional_format("$A$3:$%s$%d" % (last_col,number_rows), {'type': 'text',
                                       'criteria':'containing',
                                       'value': 'CHO',
                                       'format': company_holiday_format})
    
    mispunched_format = workbook_object.add_format({'indent':1,
                                                    'border_color':'black',
                                                    'align':'center',
                                                    'border': 1,
                                                    'num_format':'General',
                                                    'bg_color': '#0D0D0D',
                                                    'font_color': 'white'})
    
    worksheet.conditional_format("$A$3:$%s$%d" % (last_col,number_rows), {'type': 'text',
                                       'criteria':'begins with',#'containing',
                                       'value': 'MP',
                                       'format': mispunched_format})


    for col_num, value in enumerate(df.columns.values):
        worksheet.write(9, col_num, value, header_format_object)

    writer_object.save()
    writer_object.close()