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
            self.mr = parameters.mr_name
            self.mr_vendor = parameters.mr_vendor
            logging.info(f'Creating requirements for: {self.mr}...')
            self.remove_xlsx_files()
            self.activate_protocol_extractor(self.mr_vendor)
            self.process_protocol_extractor_file()
            self.excel_rearrangement()
            logging.info(f'***** Make Requirement Done *****')
        except Exception as err:
            logging.error(f'Error during making requirements process: {err}.')
            sys.exit(1)

    def process_protocol_extractor_file(self):
        """
        Searches for protocol extractor output and handles it.
        """
        protocol_extractor_folder = os.path.join(os.getcwd(), 'Data', 'ProtocolExtractor')
        requirements_folder = os.path.join(os.getcwd(), 'Data', 'Requirements')
        logging.info('Searching for Protocol Extractor output...')
        for file in os.listdir(protocol_extractor_folder):
            if file.startswith('protocols_'):
                self.process_file(file, protocol_extractor_folder, requirements_folder)

    def process_file(self, file, protocol_extractor_folder, requirements_folder):
        """
        Copies input file to requirements folder and renames it.
        :param file: Input file.
        :param protocol_extractor_folder: The folder which Protocol Extractor is found in.
        :param requirements_folder: The folder that contains all the prepared requirements.
        """
        src_file = os.path.join(protocol_extractor_folder, file)
        dest_file = os.path.join(requirements_folder, file)
        renamed_file = os.path.join(requirements_folder, f'{self.mr}_Requirements.xlsx')

        try:
            # Copy file to requirements folder
            logging.info(f'Copying: {src_file} to: {requirements_folder}...')
            shutil.copy2(src_file, requirements_folder)
            logging.info('File was copied successfully.')
            # Rename file - adds underscore and the word Requirements.
            self.rename_file(dest_file, renamed_file)
        except FileExistsError:
            logging.info(f'{renamed_file} already exists.')
            self.handle_existing_file(renamed_file, dest_file)
        except Exception as e:
            logging.error(f'Failed to process file {file}: {e}')
            raise Exception()

    def handle_existing_file(self, existing_file, new_file):
        """
        Adds timestamp to existing requirements file and deletes it.
        :param existing_file: Existing file.
        :param new_file: The renamed file.
        """
        try:
            # Add timestamp and remove the old file if needed
            logging.info('Adding timestamp to file...')
            Requirements.add_timestamp(existing_file)
            logging.info('Removing old file...')
            os.remove(existing_file)
            # Rename the file
            self.rename_file(new_file, existing_file)
        except Exception as err:
            logging.error(f'Failed to handle existing requirements file: {err}')

    @staticmethod
    def remove_xlsx_files():
        """
        Remove all xlsx files from protocol extractor folder.
        """
        try:
            logging.info('Removing all .xlsx files from Protocol Extractor folder...')
            protocol_extractor_folder = os.path.join(os.getcwd(), 'Data', 'ProtocolExtractor')
            xls_files = glob.glob(f'{protocol_extractor_folder}\\*.xlsx')
            logging.info(f'Files found in Protocol Extractor folder are: {xls_files}.')
            for xls_file in xls_files:
                os.remove(xls_file)
            logging.info('All .xlsx files were removed from Protocol Extractor folder successfully.')
        except Exception as err:
            logging.info(f'Failed to remove {xls_file}.\nError: {err}')
            raise Exception()

    @staticmethod
    def get_ge_files() -> tuple:
        input_folder = os.path.join(os.getcwd(), 'Data', 'temp', 'Requirements')
        field_map_filepath = os.path.join(os.getcwd(), 'Data', 'ProtocolExtractor', 'ge_fields_map.ini')
        return input_folder, field_map_filepath

    @staticmethod
    def get_siemens_files() -> tuple:
        input_folder = glob.glob(os.path.join(os.getcwd(), 'Data', 'temp', 'Requirements', "*.yaml"))[0]
        field_map_filepath = os.path.join(os.getcwd(), 'Data', 'ProtocolExtractor', 'siemens_fields_map.ini')
        return input_folder, field_map_filepath

    @staticmethod
    def execute_protocol_extractor(input_folder: str, field_map_filepath: str, mode: str) -> None:
        """Runs the Protocol Extractor tool"""
        protocol_extractor_folder = os.path.join(os.getcwd(), 'Data', 'ProtocolExtractor')
        protocol_extractor_path = os.path.join(protocol_extractor_folder, 'ProtocolExtractor.exe')

        match mode:
            case 'GE':
                flag = '-f'
            case 'Siemens':
                flag = '-t'
        logging.info(
            f'Running Protocol Extractor tool: {protocol_extractor_path} -t {input_folder} -m {field_map_filepath}')
        subprocess.run(f'{protocol_extractor_path} {flag} {input_folder} -m {field_map_filepath}',
                       cwd=protocol_extractor_folder)

    @staticmethod
    def activate_protocol_extractor(mode: str) -> None:
        """
        Activates Protocol Extractor tool, which outputs Excel file from a given tar/xml.
        :param mode: GE or Siemens, according to MR vendor.
        """
        try:
            match mode:
                case 'GE':
                    input_folder, field_map_filepath = Requirements.get_ge_files()
                case 'Siemens':
                    input_folder, field_map_filepath = Requirements.get_siemens_files()
            Requirements.execute_protocol_extractor(input_folder, field_map_filepath, mode)
            logging.info(f'Protocol Extractor tool was executed successfully.')
        except Exception as err:
            logging.info(f'Failed to execute Protocol Extractor tool.\nError: {err}')
            raise Exception()

    @staticmethod
    def add_timestamp(filepath) -> None:
        """
        Adds timestamp to a given file.
        :param filepath: Filepath of the input file.
        """
        try:
            logging.info(f'Adding timestamp to {filepath}...')
            timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            filepath_without_extension = os.path.splitext(filepath)[0]
            shutil.copy2(src=filepath, dst=f'{filepath_without_extension}_{timestamp}.xlsx')
            logging.info(f'Added timestamp successfully.')
        except Exception as e:
            logging.error(f'Failed to add timestamp. error: {e}')

    @staticmethod
    def rename_file(file, renamed_file):
        logging.info(f'Renaming: {file} to: {renamed_file}...')
        os.rename(file, renamed_file)
        logging.info('File was renamed successfully.')

    def excel_rearrangement(self):
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
        logging.info(f'Retrieved the following sheets names: {sheets}.')
        # Deleting first sheet
        logging.info(
            f'Removing 1st sheet from {self.mr}_Requirements.xlsx...')
        requirement_file.remove(requirement_file[f'{sheets[0]}'])

        # Deleting unwanted sheets
        try:
            logging.info(f'The following sheets are found in file: {requirement_file.sheetnames}')
            for sheet in requirement_file.sheetnames:
                logging.info(f'Checking if sheet {sheet} was selected...')
                if sheet not in self.parameters.protocols:
                    logging.info(f'{sheet} was not found in {self.parameters.protocols}. Deleting: {sheet}...')
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
