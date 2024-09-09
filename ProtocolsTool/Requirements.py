import logging
import sys

import openpyxl
import os
import win32com

def resource_path(relative_path):
    # """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def excel_rearrangement(mr_name, macro_excel_file):
    logging.info(f'Start working on {mr_name}_Requirements.xlsx')
    logging.info(f'Open {mr_name}_Requirements.xlsx using Python')
    try:
        requirement_file = openpyxl.load_workbook(f'{os.getcwd()}\\Data\\{mr_name}\\{mr_name}_Requirements.xlsx')
    except Exception as err:
        logging.info(f'Failed to open {mr_name}_Requirements.xlsx.\nError: {err}')
        raise Exception(f'Failed to open {mr_name}_Requirements.xlsx.\nError: {err}')
    # Got a list of all sheets in the file and drove it into a variable
    sheets = requirement_file.sheetnames
    # Deleting first sheet
    logging.info(f'Removing 1st sheet from {mr_name}_Requirements.xlsx, sheet name: {requirement_file[f"{sheets[0]}"]}')
    requirement_file.remove(requirement_file[f'{sheets[0]}'])
    # Saved file with changes (deleted page)
    requirement_file.save(f'{os.getcwd()}\\Data\\{mr_name}\\{mr_name}_Requirements.xlsx')
    logging.info(f'Sheet removed and file {mr_name}_Requirements.xlsx saved')

    # macros
    try:
        excel = win32com.client.dynamic.Dispatch('Excel.Application')
    except Exception as err:
        logging.info(f'Failed to open Excel software.\nError: {err}')
        raise Exception(f'Failed to open Excel software.\nError: {err}')
    # open macro excel file, macros will run from it
    logging.info(f'Open macro excel file using Python, file: {macro_excel_file}')
    try:
        excel.workbooks.Open(Filename=resource_path(f"{macro_excel_file}"))
    except Exception as err:
        logging.info(f'Failed to open macro excel file: {macro_excel_file}.\nError: {err}')
        raise Exception(f'Failed to open macro excel file: {macro_excel_file}.\nError: {err}')
    # open the file to run macros on
    logging.info(f'Open {mr_name}_Requirements.xlsx for macros')
    try:
        requirement_file = excel.workbooks.Open(Filename=f"{os.getcwd()}\\Data\\{mr_name}\\{mr_name}_Requirements.xlsx")
    except Exception as err:
        logging.info(f'Failed to open excel file: {mr_name}_Requirements.xlsx.\nError: {err}')
        raise Exception(f'Failed to open macro excel file: {mr_name}_Requirements.xlsx.\nError: {err}')
    # run macro
    try:
        excel.Run(f"'{macro_excel_file}'!MakeReqDocForAllSheets")
        logging.info(f'Ran macro: MakeReqDocForAllSheets')
    except Exception as err:
        logging.info(f'Failed to run macro: MakeReqDocForAllSheets.\nError: {err}')
        raise Exception(f'Failed to run macro: MakeReqDocForAllSheets.\nError: {err}')
    try:
        excel.Run(f"'{macro_excel_file}'!EqualCellSizeForAllSheets")
        logging.info(f'Ran macro: EqualCellSizeForAllSheets')
    except Exception as err:
        logging.info(f'Failed to run macro: EqualCellSizeForAllSheets.\nError: {err}')
        raise Exception(f'Failed to run macro: EqualCellSizeForAllSheets.\nError: {err}')
    try:
        excel.Run(f"'{macro_excel_file}'!CenterForAllSheets")
        logging.info(f'Ran macro: CenterForAllSheets')
    except Exception as err:
        logging.info(f'Failed to run macro: CenterForAllSheets.\nError: {err}')
        raise Exception(f'Failed to run macro: CenterForAllSheets.\nError: {err}')

    # save the file after macros
    try:
        requirement_file.Close(SaveChanges=1)
        logging.info(f'{mr_name}_Requirements.xlsx Saved')
    except Exception as err:
        logging.info(f'Failed to save {mr_name}_Requirements.xlsx.\nError: {err}')
        raise Exception(f'Failed to save {mr_name}_Requirements.xlsx.\nError: {err}')
    excel.Quit()
    logging.info(f'All excel open files closed')