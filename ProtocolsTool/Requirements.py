import glob
import logging
import shutil
import subprocess
import sys
from datetime import datetime
import openpyxl
import os
import win32com


def resource_path(relative_path):
    # """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class Requirements:
    def __init__(self, parameters):
        logging.info(f'***** Make Requirement *****')
        try:
            self.parameters = parameters
            #self.prepare_folders_for_make_req()
            if 'ProtocolExtractor' not in os.listdir('Data'):
                logging.info(f'Protocol Extractor tool not exist in {os.getcwd()}\\Data')
                self.prepare_protocol_extractor_for_make_req()
            logging.info(f'Creating requirements for: {parameters.mr_name}...')
            self.mr = parameters.mr_name
            self.activate_protocol_extractor()
            self.move_protocol_extractor_output()
            self.excel_rearrangement(parameters)
            logging.info(f'***** Make Requirement Done *****')
        except Exception as err:
            logging.error(f'Error during making requirements process: {err}.')
            sys.exit(1)

    def prepare_folders_for_make_req(self):
        logging.info(f'Start to create folders')
        self.parameters.protocol_selection_list = []
        for inside_tab_list_box in self.parameters.inside_tab_list_box_list:
            temp_selection_list = []
            for item in inside_tab_list_box.selection():
                temp_selection_list.append(inside_tab_list_box.item(item, "text"))
            self.parameters.protocol_selection_list.append(temp_selection_list)

        for i in range(0, self.parameters.number_of_mrs):
            logging.info(
                f'MR: {self.parameters.mrs_list[i]}, selected protocols: {self.parameters.protocol_selection_list[i]}')
            try:
                os.mkdir(f'Data\\{self.parameters.mrs_list[i]}')
                logging.info(f'Folder named: {self.parameters.mrs_list[i]} created')
            except FileExistsError:
                logging.info(
                    f'Folder with the name: {self.parameters.mrs_list[i]} already exists in {os.getcwd()}\\Data, please remove or rename it')
                raise Exception(
                    f'Folder with the name: {self.parameters.mrs_list[i]} already exists in {os.getcwd()}\\Data, please remove or rename it')

            for folder in self.parameters.protocol_selection_list[i]:
                shutil.copytree(f'{os.getcwd()}\\Data\\temp\\MakeRequirement\\{self.parameters.mrs_list[i]}\\{folder}',
                                f'Data\\{self.parameters.mrs_list[i]}\\{folder}')
                logging.info(f'Copy protocol: {folder} to folder: {os.getcwd()}\\Data\\{self.parameters.mrs_list[i]}')

    def prepare_protocol_extractor_for_make_req(self):
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
            logging.info(f'All .xlsx files were removed from Protocol Extractor folder.')
        except Exception as err:
            logging.info(f'Failed to remove all .xlsx files from Protocol Extractor folder.\nError: {err}')
            raise Exception(f'Failed to remove all .xlsx files from Protocol Extractor folder.\nError: {err}')

        try:
            logging.info(
                f'Running Protocol Extractor tool, command: {os.getcwd()}\\Data\\ProtocolExtractor\\ProtocolExtractor'
                f'.exe -f {os.getcwd()}\\Data\\TempTarExtract -m '
                f'{os.getcwd()}\\Data\\ProtocolExtractor\\fields_map.ini')
            subprocess.run(
                f'{os.getcwd()}\\Data\\ProtocolExtractor\\ProtocolExtractor.exe -f {os.getcwd()}\\Data\\TempTarExtract -m {os.getcwd()}\\Data\\ProtocolExtractor\\fields_map.ini',
                cwd=f'{os.getcwd()}\\Data\\ProtocolExtractor')
            logging.info(f'Protocol Extractor tool was executed successfully.')
        except Exception as err:
            logging.info(f'Failed to run Protocol Extractor tool.\nError: {err}')
            raise Exception(f'Failed to run Protocol Extractor tool.\nError: {err}')

    def move_protocol_extractor_output(self):
        for file in os.listdir(f'{os.getcwd()}\\Data\\ProtocolExtractor.'):
            if file.startswith('protocols_'):
                logging.info(f'Copying Protocol Extractor tool output...')
                try:
                    logging.info(f'Copying: {os.getcwd()}\\Data\\ProtocolExtractor\\{file} to: {os.getcwd()}\\Data'
                                 f'\\Requirements...')
                    shutil.copy2(f'{os.getcwd()}\\Data\\ProtocolExtractor\\{file}',
                                 f'{os.getcwd()}\\Data\\Requirements')
                    logging.info('File was copied successfully.')
                except Exception as err:
                    logging.info(f'Failed to move Protocol Extractor tool output.\nError: {err}')
                    raise Exception(f'Failed to move Protocol Extractor tool output.\nError: {err}')
                try:
                    logging.info(f'Renaming: {os.getcwd()}\\Data\\Requirements\\{file} to: {os.getcwd()}\\Data'
                                 f'\\Requirements\\{self.mr}_Requirements.xlsx...')
                    os.rename(f'{os.getcwd()}\\Data\\Requirements\\{file}',
                              f'{os.getcwd()}\\Data\\Requirements\\{self.mr}_Requirements.xlsx')
                    logging.info(f'{file} renamed to {self.mr}_Requirements.xlsx')
                except FileExistsError:
                    try:
                        logging.info(f'{os.getcwd()}\\Data\\Requirements\\{self.mr}_Requirements.xlsx already exists.')
                        logging.info(
                            f'Copying: {os.getcwd()}\\Data\\Requirements\\{self.mr}_Requirements.xlsx to: {os.getcwd()}\\Data\\Requirements\\{self.mr}_{datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}_Requirements.xlsx...')
                        shutil.copy2(src=f'{os.getcwd()}\\Data\\Requirements\\{self.mr}_Requirements.xlsx',
                                     dst=f'{os.getcwd()}\\Data\\Requirements\\{self.mr}_Requirements_{datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.xlsx')
                        logging.info(
                            f'File copied successfully. Removing: {os.getcwd()}\\Data\\Requirements\\{self.mr}_Requirements.xlsx...')
                        os.remove(f'{os.getcwd()}\\Data\\Requirements\\{self.mr}_Requirements.xlsx')
                        logging.info('Removal was successful.')
                        logging.info(f'Renaming: {os.getcwd()}\\Data\\Requirements\\{file} to: {os.getcwd()}\\Data'
                                     f'\\Requirements\\{self.mr}_Requirements.xlsx...')
                        os.rename(f'{os.getcwd()}\\Data\\Requirements\\{file}',
                                  f'{os.getcwd()}\\Data\\Requirements\\{self.mr}_Requirements.xlsx')
                        logging.info(f'{file} renamed to {self.mr}_Requirements.xlsx')
                    except Exception as err:
                        logging.error(f'Handling with identical requirements file was failed. {err}.')

    def excel_rearrangement(self, parameters):
        logging.info(f'Working on {self.mr}_Requirements.xlsx...')
        try:
            logging.info(f'Opening {self.mr}_Requirements.xlsx using Python...')
            requirement_file = openpyxl.load_workbook(
                f'{os.getcwd()}\\Data\\Requirements\\{self.mr}_Requirements.xlsx')
        except Exception as err:
            logging.info(f'Failed to open {self.mr}_Requirements.xlsx.\nError: {err}')
            raise Exception(f'Failed to open {self.mr}_Requirements.xlsx.\nError: {err}')
        # Got a list of all sheets in the file and drove it into a variable
        sheets = requirement_file.sheetnames
        logging.info(f'Retried sheet names from {requirement_file}: {sheets}.')
        # Deleting first sheet
        logging.info(
            f'Removing 1st sheet from {self.mr}_Requirements.xlsx, sheet name: {requirement_file[f"{sheets[0]}"]}')
        requirement_file.remove(requirement_file[f'{sheets[0]}'])

        # Deleting unwanted sheets
        try:
            logging.info(f'The following sheets are found in file: {requirement_file.sheetnames}')
            for sheet in requirement_file.sheetnames:
                logging.info(f'Checking if sheet {sheet} was selected...')
                if sheet not in parameters.protocol_elements:
                    logging.info(f'{sheet} was not found in {parameters.protocol_elements}. Deleting: {sheet}...')
                    del requirement_file[sheet]
                    logging.info('Deleted sheet.')
        except Exception as err:
            logging.info(f'Failed to delete the following sheet: {sheet}. {err}')
            raise Exception(f'Failed to delete the following sheet: {sheet}. {err}')

        # Saved file with changes (deleted page)
        requirement_file.save(f'{os.getcwd()}\\Data\\Requirements\\{self.mr}_Requirements.xlsx')
        logging.info(f'Sheet removed and file {self.mr}_Requirements.xlsx saved')

        # macros
        try:
            logging.info('Opening Excel...')
            excel = win32com.client.dynamic.Dispatch('Excel.Application')
            logging.info('Excel opened successfully.')
        except Exception as err:
            logging.info(f'Failed to open Excel software.\nError: {err}')
            raise Exception(f'Failed to open Excel software.\nError: {err}')
        # open macro excel file, macros will run from it
        try:
            logging.info(f'Opening macro excel file using Python, file: {self.parameters.macro_excel_file}...')
            excel.workbooks.Open(Filename=resource_path(f"{self.parameters.macro_excel_file}"))
            logging.info('Opened file successfully.')
        except Exception as err:
            logging.info(f'Failed to open macro excel file: {self.parameters.macro_excel_file}.\nError: {err}')
            raise Exception(f'Failed to open macro excel file: {self.parameters.macro_excel_file}.\nError: {err}')
        # open the file to run macros on
        try:
            logging.info(f'Opening {self.mr}_Requirements.xlsx for macros...')
            requirement_file = excel.workbooks.Open(
                Filename=f"{os.getcwd()}\\Data\\Requirements\\{self.mr}_Requirements.xlsx")
        except Exception as err:
            logging.info(f'Failed to open excel file: {self.mr}_Requirements.xlsx.\nError: {err}')
            raise Exception(f'Failed to open macro excel file: {self.mr}_Requirements.xlsx.\nError: {err}')
        # run macro
        try:
            logging.info(f'Running macro: MakeReqDocForAllSheets...')
            excel.Run(f"'{self.parameters.macro_excel_file}'!MakeReqDocForAllSheets")
            logging.info(f'Running macro MakeReqDocForAllSheets ended successfully.')
        except Exception as err:
            logging.info(f'Failed to run macro: MakeReqDocForAllSheets.\nError: {err}')
            raise Exception(f'Failed to run macro: MakeReqDocForAllSheets.\nError: {err}')
        try:
            logging.info(f'Running macro: EqualCellSizeForAllSheets...')
            excel.Run(f"'{self.parameters.macro_excel_file}'!EqualCellSizeForAllSheets")
            logging.info(f'Running macro EqualCellSizeForAllSheets ended successfully.')
        except Exception as err:
            logging.info(f'Failed to run macro: EqualCellSizeForAllSheets.\nError: {err}')
            raise Exception(f'Failed to run macro: EqualCellSizeForAllSheets.\nError: {err}')
        try:
            logging.info(f'Running macro: CenterForAllSheets...')
            excel.Run(f"'{self.parameters.macro_excel_file}'!CenterForAllSheets")
            logging.info(f'Ran macro: CenterForAllSheets')
            logging.info(f'Running macro CenterForAllSheets ended successfully.')
        except Exception as err:
            logging.info(f'Failed to run macro: CenterForAllSheets.\nError: {err}')
            raise Exception(f'Failed to run macro: CenterForAllSheets.\nError: {err}')

        # save the file after macros
        try:
            logging.info(f'Saving: {requirement_file}...')
            requirement_file.Close(SaveChanges=1)
            logging.info(f'{self.mr}_Requirements.xlsx saved. Quitting Excel...')
            excel.Quit()
        except Exception as err:
            logging.info(f'Failed to save {self.mr}_Requirements.xlsx.\nError: {err}')
            raise Exception(f'Failed to save {self.mr}_Requirements.xlsx.\nError: {err}')
