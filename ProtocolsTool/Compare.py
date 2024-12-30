import logging
import os
import shutil
import subprocess
import glob
import openpyxl
import win32com.client
import sys
import tarfile
from pathlib import Path
import re


def resource_path(relative_path):
    # """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class Compare:
    def __init__(self, parameters):
        logging.info(f'***** Compare *****')
        try:
            self.parameters = parameters
            self.mr_name = Path(self.parameters.path_for_req).name.replace('_Requirements.xlsx', '')
            logging.info(f'MR: {self.mr_name}')
            self.extract_tar()
            self.move_relevant_protocols()
            if 'ProtocolExtractor' not in os.listdir('Data'):
                logging.info(f'Protocol Extractor tool does not exist in {os.getcwd()}\\Data.')
                self.prepare_protocol_extractor_for_compare()
            self.activate_protocol_extractor()
            self.move_protocol_extractor_output()
            self.prepare_for_comparison()
            self.compare()
            logging.info(f'***** Compare Done *****')
            sys.exit()
        except Exception as err:
            logging.error(f'Error during comparison: {err}.')
            sys.exit(1)

    def extract_tar(self):
        # Reset temp\Compare folder
        compare_folder_path = f'{os.getcwd()}\\Data\\temp\\Compare\\{self.mr_name}'
        if os.path.exists(compare_folder_path):
            logging.info(f'The folder: {compare_folder_path} already exists. Deleting the folder...')
            try:
                shutil.rmtree(compare_folder_path)
                logging.info(f"Deleted {compare_folder_path} successfully. Creating new folder under the same path...")
                os.mkdir(compare_folder_path)
                logging.info(f'Successfully created a new folder: {compare_folder_path}')
            except Exception as err:
                logging.error(f'Failed to reset folder: {compare_folder_path}. error: {err}.')
                raise Exception(f'Failed to reset folder: {compare_folder_path}. error: {err}.')

        # Extracting TAR
        try:
            logging.info('Start to open TAR file...')
            my_tar = tarfile.open(self.parameters.path_for_tar)
        except Exception as err:
            logging.info(f'Could not open TAR file.\nError: {err}.')
            raise Exception(f'Could not open TAR file.\nError: {err}.')
        try:
            logging.info(f'Start to extract TAR file to: {os.getcwd()}\\Data\\temp\\Compare\\{self.mr_name}...')
            my_tar.extractall(f'{os.getcwd()}\\Data\\temp\\Compare\\{self.mr_name}')
            logging.info(f'TAR file was extracted successfully. Closing file.')
            my_tar.close()
        except Exception as err:
            logging.info(
                f'Could not extract TAR file to: {os.getcwd()}\\Data\\temp\\Compare\\{self.mr_name}.\nError: {err}.')
            raise Exception(
                f'Could not extract TAR file to: {os.getcwd()}\\Data\\temp\\Compare\\{self.mr_name}.\nError: {err}.')

    def move_relevant_protocols(self):
        logging.info(
            f'Start moving only the relevant protocols to folder {os.path.dirname(self.parameters.path_for_req)}\\ForCompare...')
        try:
            logging.info(f'Try to open: {self.parameters.path_for_req}...')
            requirement_file = openpyxl.load_workbook(self.parameters.path_for_req)
        except Exception as err:
            logging.info(f'Could not open Excel file.\nError: {err}.')
            raise Exception(f'Could not open Excel file.\nError: {err}.')
        try:
            logging.info('Retrieving sheet names from file...')
            list_of_all_sheets = requirement_file.sheetnames
            logging.info(f'Retrieved the following sheets names: {list_of_all_sheets}.')
        except Exception as err:
            logging.info(f'Could not retrieve sheets name from Excel file.\nError: {err}.')
            raise Exception(f'Could not receive sheets name from Excel file.\nError: {err}.')


        # Get a list of all protocols found in the TAR file
        list_of_all_protocols = os.listdir(f'{os.getcwd()}\\Data\\temp\\Compare\\{self.mr_name}')
        logging.info(
            f'List of all extracted protocols in {os.getcwd()}\\Data\\temp\\Compare\\{self.mr_name}: {list_of_all_protocols}')

        if f'ForCompare' in os.listdir(f'{os.path.dirname(self.parameters.path_for_req)}'):
            logging.info(f'ForCompare folder already exists in {os.path.dirname(self.parameters.path_for_req)}')
            try:
                logging.info(f'Trying to delete: {os.path.dirname(self.parameters.path_for_req)}\\ForCompare...')
                shutil.rmtree(f'{os.path.dirname(self.parameters.path_for_req)}\\ForCompare')
                logging.info('Successfully deleted the folder.')
            except Exception as err:
                logging.info(
                    f'Could not delete ForCompare folder from {os.path.dirname(self.parameters.path_for_req)}.\nError: {err}.')
                raise Exception(
                    f'Could not delete ForCompare folder from {os.path.dirname(self.parameters.path_for_req)}.\nError: {err}.')

        logging.info(
            f'Start moving relevant protocols to: {os.path.dirname(self.parameters.path_for_req)}\\ForCompare...')
        for sheet_name in list_of_all_sheets:
            for protocol_name in list_of_all_protocols:
                if sheet_name == re.match("^adult_other_(.+?)_\d+_\d+$", str(protocol_name)).group(1):
                    try:
                        logging.info(f'Copying: {os.getcwd()}\\Data\\temp\\Compare\\{self.mr_name}\\{protocol_name} '
                                     f'to: {os.path.dirname(self.parameters.path_for_req)}\\ForCompare\\{protocol_name}...')
                        shutil.copytree(f'{os.getcwd()}\\Data\\temp\\Compare\\{self.mr_name}\\{protocol_name}',
                                        f'{os.path.dirname(self.parameters.path_for_req)}\\ForCompare\\{protocol_name}')
                        logging.info('File was copied.')
                    except Exception as err:
                        logging.info(
                            f'Failed to copy protocol folder {protocol_name} to {os.path.dirname(self.parameters.path_for_req)}\\ForCompare.\nError: {err}')
                        raise Exception(
                            f'Failed to copy protocol folder {protocol_name} to {os.path.dirname(self.parameters.path_for_req)}\\ForCompare.\nError: {err}')
        logging.info(f'All relevant protocols for MR {self.mr_name} moved successfully.')

    def prepare_protocol_extractor_for_compare(self):
        logging.info(f'Starting to move Protocol Extractor tool to {os.getcwd()}\\Data...')
        try:
            temp_folder_list = os.listdir('\\\\192.100.100.116\\Public\\Testing\\Tools\\ProtocolExtractor\\bin\\V1.3')
            logging.info(
                f'Copying from: \\\\192.100.100.116\\Public\\Testing\\Tools\\ProtocolExtractor\\bin\\V1.3\\{temp_folder_list[len(temp_folder_list) - 1]}'
                f'to: {os.getcwd()}\\Data\\ProtocolExtractor.')
            shutil.copytree(
                f'\\\\192.100.100.116\\Public\\Testing\\Tools\\ProtocolExtractor\\bin\\V1.3\\{temp_folder_list[len(temp_folder_list) - 1]}',
                f'{os.getcwd()}\\Data\\ProtocolExtractor')
            logging.info(f'Protocol Extractor tool moved to {os.getcwd()}\\Data successfully.')
        except Exception as err:
            logging.info(f'Could not move Protocol Extractor tool to {os.getcwd()}\\Data.\nError: {err}.')
            raise Exception(f'Could not move Protocol Extractor tool to {os.getcwd()}\\Data.\nError: {err}.')

    def activate_protocol_extractor(self):
        # remove all xls files from extractor folder
        logging.info(f'Removing all .xlsx files from Protocol Extractor folder...')
        try:
            list_of_xls_files = glob.glob(f'{os.getcwd()}\\Data\\ProtocolExtractor\\*.xlsx')
            logging.info(f'Files found in ProtocolExtractor folder: {list_of_xls_files}.')
            for xls_file in list_of_xls_files:
                logging.info(f'Removing: {xls_file}...')
                os.remove(xls_file)
                logging.info('File was removed successfully.')
            logging.info(f'All .xlsx files were removed from ProtocolExtractor folder.')
        except Exception as err:
            logging.info(f'Failed to remove all .xlsx files from Protocol Extractor folder.\nError: {err}.')
            raise Exception(f'Failed to remove all .xlsx files from Protocol Extractor folder.\nError: {err}.')

        try:
            logging.info(
                f'Running Protocol Extractor tool, command: {os.getcwd()}\\Data\\ProtocolExtractor\\ProtocolExtractor'
                f'.exe'
                f'-f {os.getcwd()}\\Data\\{self.mr_name}\\ForCompare -m '
                f'{os.getcwd()}\\Data\\ProtocolExtractor\\fields_map.ini...')
            subprocess.run(
                f'{os.getcwd()}\\Data\\ProtocolExtractor\\ProtocolExtractor.exe -f {os.getcwd()}\\Data\\{self.mr_name}\\ForCompare -m {os.getcwd()}\\Data\\ProtocolExtractor\\fields_map.ini',
                cwd=f'{os.getcwd()}\\Data\\ProtocolExtractor')
            logging.info(f'Protocol Extractor tool was executed successfully.')
        except Exception as err:
            logging.info(f'failed to run Protocol Extractor tool.\nError: {err}.')
            raise Exception(f'failed to run Protocol Extractor tool.\nError: {err}.')

    def move_protocol_extractor_output(self):
        for file in os.listdir(f'{os.getcwd()}\\Data\\ProtocolExtractor'):
            if file.startswith('protocols_'):
                logging.info(f'Copying Protocol Extractor tool output...')
                try:
                    logging.info(
                        f'Start to copy: {os.getcwd()}\\Data\\ProtocolExtractor\\{file} to: {os.getcwd()}\\Data\\{self.mr_name}\\ForCompare...')
                    shutil.copy2(f'{os.getcwd()}\\Data\\ProtocolExtractor\\{file}',
                                 f'{os.getcwd()}\\Data\\{self.mr_name}\\ForCompare')
                    logging.info('File copied successfully.')
                except Exception as err:
                    logging.info(f'Failed to move Protocol Extractor tool output.\nError: {err}.')
                    raise Exception(f'Failed to move Protocol Extractor tool output.\nError: {err}.')
                try:
                    logging.info(
                        f'Try to rename: {os.getcwd()}\\Data\\{self.mr_name}\\ForCompare\\{file} to: {os.getcwd()}\\Data\\{self.mr_name}\\ForCompare\\{self.mr_name}_ForCompare.xlsx')
                    os.rename(f'{os.getcwd()}\\Data\\{self.mr_name}\\ForCompare\\{file}',
                              f'{os.getcwd()}\\Data\\{self.mr_name}\\ForCompare\\{self.mr_name}_ForCompare.xlsx')
                    logging.info('Renaming succeeded.')
                except Exception as err:
                    logging.info(f'Failed to rename Protocol Extractor tool output.\nError: {err}.')
                    raise Exception(f'Failed to rename Protocol Extractor tool output.\nError: {err}.')

    def prepare_for_comparison(self):
        logging.info(f'Preparing for comparison...')
        try:
            logging.info(
                f'Creating comparison file: copying {self.mr_name}_Requirements.xlsx and saving as {self.mr_name}_Comparison'
                f'.xlsx')
            shutil.copy2(f'{os.getcwd()}\\Data\\{self.mr_name}\\{self.mr_name}_Requirements.xlsx',
                         f'{os.getcwd()}\\Data\\{self.mr_name}\\{self.mr_name}_Comparison.xlsx')
        except Exception as err:
            logging.info(f'Failed to copy {self.mr_name}_Requirements.xlsx file.\nError: {err}.')
            raise Exception(f'Failed to copy {self.mr_name}_Requirements.xlsx file.\nError: {err}.')
        try:
            logging.info(f'Opening {self.mr_name}_ForCompare.xlsx using Python...')
            for_compare_file = openpyxl.load_workbook(
                f'{os.getcwd()}\\Data\\{self.mr_name}\\ForCompare\\{self.mr_name}_ForCompare.xlsx')
        except Exception as err:
            logging.info(f'Failed to open {self.mr_name}_ForCompare.xlsx.\nError: {err}.')
            raise Exception(f'Failed to open {self.mr_name}_ForCompare.xlsx.\nError: {err}.')
        # Got a list of all sheets in the file and drove it into a variable
        sheets = for_compare_file.sheetnames
        logging.info(f'Sheets names in file: {for_compare_file} are: {sheets}.')
        # Deleting first sheet
        logging.info(
            f'Removing 1st sheet from {self.mr_name}_ForCompare.xlsx, sheet name: {for_compare_file[f"{sheets[0]}"]}...')
        for_compare_file.remove(for_compare_file[f'{sheets[0]}'])
        # Saved file with changes (deleted page)
        for_compare_file.save(f'{os.getcwd()}\\Data\\{self.mr_name}\\ForCompare\\{self.mr_name}_ForCompare.xlsx')
        logging.info(f'Sheet removed and file {self.mr_name}_ForCompare.xlsx saved')

        # macros
        try:
            logging.info('Opening Excel...')
            excel = win32com.client.dynamic.Dispatch('Excel.Application')
            logging.info('Excel opened successfully.')
        except Exception as err:
            logging.info(f'Failed to open Excel software.\nError: {err}')
            raise Exception(f'Failed to open Excel software.\nError: {err}')
        # open macro excel file, macros will run from it
        logging.info(f'Opening macro excel file using Python, file: {self.parameters.macro_excel_file}...')
        try:
            excel.workbooks.Open(Filename=resource_path(f"{self.parameters.macro_excel_file}"))
        except Exception as err:
            logging.info(f'Failed to open macro excel file: {self.parameters.macro_excel_file}.\nError: {err}')
            raise Exception(f'Failed to open macro excel file: {self.parameters.macro_excel_file}.\nError: {err}')
        # open the file to run macros on
        try:
            logging.info(f'Opening {self.mr_name}_ForCompare.xlsx for macros...')
            for_compare_file = excel.workbooks.Open(
                Filename=f'{os.getcwd()}\\Data\\{self.mr_name}\\ForCompare\\{self.mr_name}_ForCompare.xlsx')
        except Exception as err:
            logging.info(f'Failed to open excel file: {self.mr_name}_ForCompare.\nError: {err}')
            raise Exception(f'Failed to open macro excel file: {self.mr_name}_ForCompare.xlsx.\nError: {err}')
        # run macro
        try:
            logging.info(f'Running macro: EqualCellSizeForAllSheets...')
            excel.Run(f"'{self.parameters.macro_excel_file}'!EqualCellSizeForAllSheets")
            logging.info(f'Running macro EqualCellSizeForAllSheets ended successfully.')
        except Exception as err:
            logging.info(f'Failed to run macro: EqualCellSizeForAllSheets.\nError: {err}.')
            raise Exception(f'Failed to run macro: EqualCellSizeForAllSheets.\nError: {err}.')
        try:
            logging.info(f'Running macro: CenterForAllSheets...')
            excel.Run(f"'{self.parameters.macro_excel_file}'!CenterForAllSheets")
            logging.info(f'Running macro CenterForAllSheets ended successfully.')
        except Exception as err:
            logging.info(f'Failed to run macro: CenterForAllSheets.\nError: {err}.')
            raise Exception(f'Failed to run macro: CenterForAllSheets.\nError: {err}.')
        # save the file after macros
        try:
            logging.info(f'Saving: {os.getcwd()}\\Data\\{self.mr_name}\\ForCompare\\{self.mr_name}_ForCompare.xlsx...')
            for_compare_file.Close(SaveChanges=1)
            logging.info('File was saved successfully. Quitting excel.')
        except Exception as err:
            logging.info(f'Failed to save {self.mr_name}_ForCompare.xlsx.\nError: {err}.')
            raise Exception(f'Failed to save {self.mr_name}_ForCompare.xlsx.\nError: {err}.')
        excel.Quit()

    def compare(self):
        # macros
        try:
            logging.info('Opening Excel...')
            excel = win32com.client.dynamic.Dispatch('Excel.Application')
        except Exception as err:
            logging.info(f'Failed to open Excel software.\nError: {err}')
            raise Exception(f'Failed to open Excel software.\nError: {err}')
        # open macro excel file, macros will run from it
        try:
            logging.info(f'Opening macro excel file using Python, file: {self.parameters.macro_excel_file}...')
            excel.workbooks.Open(Filename=resource_path(f"{self.parameters.macro_excel_file}"))
        except Exception as err:
            logging.info(f'Failed to open macro excel file: {self.parameters.macro_excel_file}.\nError: {err}.')
            raise Exception(f'Failed to open macro excel file: {self.parameters.macro_excel_file}.\nError: {err}.')
        # open the file to run macros on
        try:
            logging.info(f'Opening {self.mr_name}_Comparison.xlsx to run macros on...')
            comparison_file = excel.workbooks.Open(
                Filename=f'{os.getcwd()}\\Data\\{self.mr_name}\\{self.mr_name}_Comparison.xlsx')
        except Exception as err:
            logging.info(f'Failed to open excel file: {self.mr_name}_Comparison.\nError: {err}.')
            raise Exception(f'Failed to open macro excel file: {self.mr_name}_Comparison.xlsx.\nError: {err}.')
        # run macro
        try:
            logging.info(f'Running macro: ReqToTestDocForAllSheets...')
            excel.Run(f"'{self.parameters.macro_excel_file}'!ReqToTestDocForAllSheets")
            logging.info(f'Running macro ReqToTestDocForAllSheets ended successfully.')
        except Exception as err:
            logging.info(f'Failed to run macro: ReqToTestDocForAllSheets.\nError: {err}.')
            raise Exception(f'Failed to run macro: ReqToTestDocForAllSheets.\nError: {err}.')
        try:
            logging.info(f'Running macro: PythonAutomaticCopyPasteToAllSheets...')
            excel.Run(f"'{self.parameters.macro_excel_file}'!PythonAutomaticCopyPasteToAllSheets",
                      str(f'{os.getcwd()}\\Data\\{self.mr_name}\\ForCompare\\{self.mr_name}_ForCompare.xlsx'),
                      str(f'{os.getcwd()}\\Data\\{self.mr_name}\\{self.mr_name}_Comparison.xlsx'))
            logging.info(f'Running macro PythonAutomaticCopyPasteToAllSheets ended successfully.')
        except Exception as err:
            logging.info(f'Failed to run macro: PythonAutomaticCopyPasteToAllSheets.\nError: {err}.')
            raise Exception(f'Failed to run macro: PythonAutomaticCopyPasteToAllSheets.\nError: {err}.')
        try:
            logging.info(f'Running macro: CompareForAllSheets...')
            excel.Run(f"'{self.parameters.macro_excel_file}'!CompareForAllSheets")
            logging.info(f'Running macro CompareForAllSheets ended successfully.')
        except Exception as err:
            logging.info(f'Failed to run macro: CompareForAllSheets.\nError: {err}.')
            raise Exception(f'Failed to run macro: CompareForAllSheets.\nError: {err}.')

        # save the file after macros
        try:
            logging.info(f'Saving {self.mr_name}_Comparison.xlsx...')
            comparison_file.Close(SaveChanges=1)
            logging.info('File was saved. Quitting Excel.')
            excel.Quit()
        except Exception as err:
            logging.info(f'Failed to save {self.mr_name}_Comparison.xlsx.\nError: {err}')
            raise Exception(f'Failed to save {self.mr_name}_Comparison.xlsx.\nError: {err}')
