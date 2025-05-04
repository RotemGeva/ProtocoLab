import logging
import os
import shutil
import stat
import openpyxl
import win32com.client
import sys
import tarfile
from ApplicationParameters import ApplicationParameters
from XMLParser import XMLParser
from ProtocolExtractor import ProtocolExtractor
import utils
import re


def resource_path(relative_path):
    # """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def remove_readonly(func, path, exc_info):
    """
    Change file/folder to be writable before attempting to delete.
    :param func:
    :param path: path to remove read-only attributes from.
    :param exc_info:
    """
    logging.info(f'Failed to delete {path}. removing read-only attribute...')
    os.chmod(path, stat.S_IWRITE)  # Removes read-only attribute
    func(path)


class Compare:
    def __init__(self, parameters):
        logging.info(f'***** Compare *****')
        try:
            self.parameters = parameters
            self.handle_extraction(self.parameters.mr_vendor)
            if self.parameters.mr_vendor == ApplicationParameters.GE:
                self.handle_moving_protocols()
                siemens_sw_type = None
            elif self.parameters.mr_vendor == ApplicationParameters.SIEMENS:
                siemens_sw_type = utils.read_mr_sw_type()
            pe = ProtocolExtractor(self.parameters.mr_name, self.parameters.mr_vendor,
                                   siemens_sw_type, is_comparing=True)
            pe.handle_protocol_extractor()
            self.prepare_comparison_file()
            self.activate_macros()
            self.compare()
            logging.info(f'***** Compare Done *****')
            sys.exit()
        except Exception as err:
            logging.error(f'Error during comparison: {err}.')
            sys.exit(1)

    def move_protocols(self, src_folder, dest_folder, existed_protocols) -> None:
        """
        Moves specific protocols from src folder to dest folder, according to the protocols that
        appear in requirements file.
        :param src_folder: src folder.
        :param dest_folder: dest folder.
        :param existed_protocols: all protocols found in original file.
        """
        logging.info(f'Moving protocols from: {src_folder} to: {dest_folder}.\n Protocols in original file are: '
                     f'{existed_protocols}')
        protocols_in_req = self.get_sheetsnames(self.parameters.req_path)
        logging.info(f'Protocols in requirements file are: {protocols_in_req}')
        protocol_regex = "^adult_other_(.+?)_\d+_\d+$"
        for protocol_in_req in protocols_in_req:
            for protocol_in_file in existed_protocols:
                if protocol_in_req == re.match(protocol_regex, str(protocol_in_file)).group(1):
                    try:
                        protocol_filepath = os.path.join(src_folder, protocol_in_file)
                        new_protocol_filepath = os.path.join(dest_folder, protocol_in_file)
                        logging.info(f'Copying: {protocol_filepath} to: {new_protocol_filepath}...')
                        shutil.copytree(protocol_filepath, new_protocol_filepath)
                        logging.info('File was copied successfully.')
                    except Exception as e:
                        logging.error('Failed to copy file.')
                        raise Exception(f'Failed to copy file. error: {e}')
        logging.info(f'All relevant protocols were moved successfully.')

    def handle_moving_protocols(self):
        """
        Handles all moving protocols process.
        """
        temp_folder_path = os.path.join(os.getcwd(), 'Data', 'temp')
        requirements_dir = os.path.dirname(self.parameters.req_path)
        for_compare_folder = os.path.join(requirements_dir, 'ForCompare')

        if 'ForCompare' in os.listdir(requirements_dir):
            logging.info(f'ForCompare folder already exists in {requirements_dir}')
            self.manage_folder(for_compare_folder, recreate=False)

        protocols_in_file = os.listdir(temp_folder_path)
        self.move_protocols(src_folder=temp_folder_path, dest_folder=for_compare_folder,
                            existed_protocols=protocols_in_file)

    def prepare_comparison_file(self):
        """
        Prepares comparison file before comparing process:
        Removes first sheet and modifies file name.
        """
        logging.info(f'Preparing comparison file...')
        # File paths
        base_path = os.path.join(os.getcwd(), 'Data', self.parameters.mr_name)
        src_file = os.path.join(base_path, f'{self.parameters.mr_name}_Requirements.xlsx')
        dest_file = os.path.join(base_path, f'{self.parameters.mr_name}_Comparison.xlsx')
        for_compare_filepath = os.path.join(base_path, 'ForCompare', f'{self.parameters.mr_name}_ForCompare.xlsx')
        try:
            shutil.copy2(src_file, dest_file)
            logging.info(f'Comparison file created at: {dest_file}')
            wb = openpyxl.load_workbook(for_compare_filepath)
            wb.remove(wb[wb.sheetnames[0]])
            wb.save(for_compare_filepath)
            logging.info(f'Removed first sheet and saved {for_compare_filepath}')
        except Exception as e:
            logging.error(f'Error during comparison file preparation: {e}')
            raise Exception(f'Error during comparison file preparation: {e}')

    def activate_macros(self):
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
            logging.info(f'Opening {self.parameters.mr_name}_ForCompare.xlsx for macros...')
            for_compare_file = excel.workbooks.Open(
                Filename=f'{os.getcwd()}\\Data\\{self.parameters.mr_name}\\ForCompare\\{self.parameters.mr_name}_ForCompare.xlsx')
        except Exception as err:
            logging.info(f'Failed to open excel file: {self.parameters.mr_name}_ForCompare.\nError: {err}')
            raise Exception(
                f'Failed to open macro excel file: {self.parameters.mr_name}_ForCompare.xlsx.\nError: {err}')
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
            logging.info(
                f'Saving: {os.getcwd()}\\Data\\{self.parameters.mr_name}\\ForCompare\\{self.parameters.mr_name}_ForCompare.xlsx...')
            for_compare_file.Close(SaveChanges=1)
            logging.info('File was saved successfully. Quitting excel.')
        except Exception as err:
            logging.info(f'Failed to save {self.parameters.mr_name}_ForCompare.xlsx.\nError: {err}.')
            raise Exception(f'Failed to save {self.parameters.mr_name}_ForCompare.xlsx.\nError: {err}.')
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
            logging.info(f'Opening {self.parameters.mr_name}_Comparison.xlsx to run macros on...')
            comparison_file = excel.workbooks.Open(
                Filename=f'{os.getcwd()}\\Data\\{self.parameters.mr_name}\\{self.parameters.mr_name}_Comparison.xlsx')
        except Exception as err:
            logging.info(f'Failed to open excel file: {self.parameters.mr_name}_Comparison.\nError: {err}.')
            raise Exception(
                f'Failed to open macro excel file: {self.parameters.mr_name}_Comparison.xlsx.\nError: {err}.')
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
                      str(f'{os.getcwd()}\\Data\\{self.parameters.mr_name}\\ForCompare\\{self.parameters.mr_name}_ForCompare.xlsx'),
                      str(f'{os.getcwd()}\\Data\\{self.parameters.mr_name}\\{self.parameters.mr_name}_Comparison.xlsx'))
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
            logging.info(f'Saving {self.parameters.mr_name}_Comparison.xlsx...')
            comparison_file.Close(SaveChanges=1)
            logging.info('File was saved. Quitting Excel.')
            excel.Quit()
        except Exception as err:
            logging.info(f'Failed to save {self.parameters.mr_name}_Comparison.xlsx.\nError: {err}')
            raise Exception(f'Failed to save {self.parameters.mr_name}_Comparison.xlsx.\nError: {err}')

    def handle_extraction(self, mode: str) -> None:
        """
        Handles all extraction process.
        tar for GE scenario and convertion of xml to yaml for Siemens scenario.
        """
        dest_folder = os.path.join(os.getcwd(), 'Data', 'temp')
        if os.path.exists(dest_folder):
            logging.info(f'The folder: {dest_folder} already exists.')
            self.manage_folder(dest_folder, recreate=True)
        else:
            logging.info(f'The folder: {dest_folder} does not exist. Creating folder...')
            os.mkdir(dest_folder)
        logging.info(f'Extracting using mode: {mode}')
        match mode.lower():
            case 'ge':
                self.extract_tar(filepath=self.parameters.actual_path, dest_folder_path=dest_folder)
            case 'siemens':
                protocols_in_req = self.get_sheetsnames(self.parameters.req_path)
                XMLParser.parse(self.parameters.actual_path, self.parameters.mr_name,
                                relevant_protocols=protocols_in_req)

    @staticmethod
    def manage_folder(folder_path: str, recreate: bool = True) -> None:
        """
        Deletes folder and re-creates it.
        :param recreate: True recreates the folder. False only deletes the folder.
        :param folder_path: The folder to delete and re-create.
        """
        logging.info(f'Managing folder: {folder_path} with recreate: {recreate}...')
        try:
            shutil.rmtree(folder_path, onerror=remove_readonly)
            logging.info(f"Deleted {folder_path} successfully.")
            if recreate:
                logging.info(f"Re-creating folder: {folder_path}...")
                os.mkdir(folder_path)
                logging.info(f'Successfully created a new folder: {folder_path}')
            else:
                logging.info(f"Folder {folder_path} was deleted, but not re-created.")
        except Exception as err:
            logging.error(f'Failed to delete and re-create folder: {folder_path}. error: {err}.')
            raise Exception(f'Failed to delete and re-create folder: {folder_path}. error: {err}.')

    @staticmethod
    def extract_tar(filepath: str, dest_folder_path: str) -> None:
        """
        Extracts tar content from a given folder to a destination folder.
        :param filepath: The file to extract.
        :param dest_folder_path: The folder that will contain the content.
        """
        try:
            logging.info(f'Opening the tar file from: {filepath}...')
            tar = tarfile.open(filepath)
            logging.info(f'Extracting tar content to: {dest_folder_path}...')
            tar.extractall(dest_folder_path)
            logging.info('Tar file was extracted successfully. Closing file...')
            tar.close()
        except Exception as e:
            logging.error(f'Failed to extract tar: {filepath}. error: {e}')
            raise Exception(f'Failed to extract tar: {filepath}. error: {e}')

    @staticmethod
    def get_sheetsnames(filepath) -> list[str]:
        """
        Retrieves sheets names from a given Excel files.
        :param filepath: Excel file.
        """
        logging.info(f'Retrieving sheets names from: {filepath}...')
        try:
            logging.info(f'Opening: {filepath}...')
            file = openpyxl.load_workbook(filepath)
            sheet_names = file.sheetnames
            logging.info(f'Retrieved the following sheets names: {sheet_names}.')
            return sheet_names
        except Exception as e:
            logging.error(f'Could not retrieve sheets names from: {filepath}. error: {e}')
            raise Exception(f'Could not retrieve sheets names from: {filepath}. error: {e}')
