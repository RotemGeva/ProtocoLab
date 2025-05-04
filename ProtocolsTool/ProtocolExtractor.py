import os
import glob
import logging
import shutil
import subprocess
from datetime import datetime
from utils import ProgressReporter

class ProtocolExtractor:
    TEMP_FOLDER_PATH = os.path.join(os.getcwd(), 'Data', 'temp')
    PROTOCOL_EXTRACTOR_FOLDER_PATH = os.path.join(os.getcwd(), 'Data', 'ProtocolExtractor')
    PROTOCOL_EXTRACTOR_FILEPATH = os.path.join(PROTOCOL_EXTRACTOR_FOLDER_PATH, 'ProtocolExtractor.exe')

    def __init__(self, mr_name: str, vendor: str, siemens_sw_type: str, is_comparing: bool):
        self.mr_name = mr_name
        self.vendor = vendor
        self.siemens_sw_type = siemens_sw_type
        self.is_comparing = is_comparing

    def handle_protocol_extractor(self):
        logging.info('Initializing Protocol Extractor processes...')
        ProgressReporter.report_progress(message="Preparing Protocol Extractor files")
        self.remove_output_files()
        input, field_map_filepath = self.prepare_protocol_extractor_files()
        ProgressReporter.report_progress(message="Executing Protocol Extractor")
        self.execute_protocol_extractor(input, field_map_filepath)
        self.process_protocol_extractor_output()
        logging.info('PE processes were completed.')

    def execute_protocol_extractor(self, input: str, field_map_filepath: str) -> None:
        """Runs the Protocol Extractor tool"""
        match self.vendor.lower():
            case 'ge':
                logging.info('Identified GE scenario.')
                flag = '-f'
            case 'siemens':
                logging.info('Identified Siemens scenario.')
                flag = '-t'
        logging.info(
            f'Running Protocol Extractor tool: {self.PROTOCOL_EXTRACTOR_FILEPATH} {flag} {input} -m '
            f'{field_map_filepath}')
        try:
            subprocess.run(f'{self.PROTOCOL_EXTRACTOR_FILEPATH} {flag} {input} -m {field_map_filepath}',
                           cwd=self.PROTOCOL_EXTRACTOR_FOLDER_PATH)
        except Exception as e:
            logging.error(f'Failed to execute PE. \n error: {e}')
            raise Exception(f'Failed to execute PE. \n error: {e}')

    def remove_output_files(self) -> None:
        """Remove all xlsx files from protocol extractor folder."""
        try:
            logging.info('Removing all .xlsx files from Protocol Extractor folder...')
            xls_files = glob.glob(f'{self.PROTOCOL_EXTRACTOR_FOLDER_PATH}\\*.xlsx')
            logging.info(f'Files found in Protocol Extractor folder: {xls_files}.')
            for xls_file in xls_files:
                os.remove(xls_file)
            logging.info('All .xlsx files were removed from Protocol Extractor folder successfully.')
        except Exception as e:
            logging.error(f'Failed to remove {xls_file}.\nError: {e}')
            raise Exception()

    def prepare_protocol_extractor_files(self) -> tuple:
        """Activates Protocol Extractor tool, which outputs Excel file from a given tar/xml."""
        try:
            match self.vendor.lower():
                case 'ge':
                    input = self.TEMP_FOLDER_PATH
                    field_map_filepath = os.path.join(self.PROTOCOL_EXTRACTOR_FOLDER_PATH, 'ge_fields_map.ini')
                    logging.info(f'Returning GE files: {self.TEMP_FOLDER_PATH}, {field_map_filepath}')
                case 'siemens':
                    input = glob.glob(os.path.join(self.TEMP_FOLDER_PATH, "*.yaml"))[0]
                    field_map_filepath = os.path.join(self.PROTOCOL_EXTRACTOR_FOLDER_PATH,
                                                      f'{self.siemens_sw_type}_siemens_fields_map.ini')
                    logging.info(f'Returning Siemens files: {input}, {field_map_filepath}')
            return input, field_map_filepath
        except Exception as e:
            logging.error(f'Failed to get PE files.\nError: {e}')
            raise Exception()

    def process_protocol_extractor_output(self):
        """Searches for protocol extractor output and handles it."""
        logging.info('Searching for Protocol Extractor output...')
        is_output_found = False
        for file in os.listdir(self.PROTOCOL_EXTRACTOR_FOLDER_PATH):
            if file.startswith('protocols_'):
                is_output_found = True
                if self.is_comparing:
                    self.process_file_compare(file)
                else:
                    self.process_file_requirements(file)
        if is_output_found is False:
            logging.error('PE output file was not found')
            raise Exception()

    def process_file_compare(self, file):
        """
        Process file using compare logic - copies PE output to ForCompare folder and renames it to _ForCompare.xlsx.
        :param file: the file that needs to be processed.
        """
        logging.info(f'Processing PE output using compare logic: {file}...')
        src_file = os.path.join(self.PROTOCOL_EXTRACTOR_FOLDER_PATH, file)
        compare_folder_path = os.path.join(os.getcwd(), 'Data', self.mr_name, 'ForCompare')
        renamed_file = os.path.join(compare_folder_path, f'{self.mr_name}_ForCompare.xlsx')
        try:
            if not os.path.exists(compare_folder_path):
                os.makedirs(compare_folder_path)
            logging.info(f'Copying: {src_file} to {compare_folder_path}...')
            shutil.copy2(src_file, compare_folder_path)
            logging.info(f'Renaming: {file} to {renamed_file}...')
            os.rename(os.path.join(compare_folder_path, file), renamed_file)
            logging.info('Output was processed successfully.')
        except Exception as e:
            logging.error(f'Failed to process file {file}: {e}')
            raise Exception(f'Failed to process file {file}: {e}')

    def process_file_requirements(self, file):
        """
        Copies input file to requirements folder (where all ready requirements are) and renames it.
        :param file: Input file.
        """
        logging.info(f'Processing PE output using requirements logic: {file}...')
        src_file = os.path.join(self.PROTOCOL_EXTRACTOR_FOLDER_PATH, file)
        requirements_folder_path = os.path.join(os.getcwd(), 'Data', 'Requirements')
        dest_file = os.path.join(requirements_folder_path, file)
        renamed_file = os.path.join(requirements_folder_path, f'{self.mr_name}_Requirements.xlsx')
        try:
            # Copy file to requirements folder
            logging.info(f'Copying: {src_file} to: {requirements_folder_path}...')
            shutil.copy2(src_file, requirements_folder_path)
            logging.info('File was copied successfully.')
            # Rename file - adds underscore and the word Requirements.
            self.rename_file(dest_file, renamed_file)
            logging.info('PE output was processed successfully.')
        except FileExistsError:
            logging.info(f'{renamed_file} already exists.')
            self.handle_existing_file(renamed_file, dest_file)
            logging.info('PE output was processed successfully.')
        except Exception as e:
            logging.error(f'Failed to process file {file}: {e}')
            raise Exception(f'Failed to process file {file}: {e}')

    def handle_existing_file(self, existing_file, new_file):
        """
        Adds timestamp to existing requirements file and deletes it.
        :param existing_file: Existing file.
        :param new_file: The renamed file.
        """
        try:
            # Add timestamp and remove the old file if needed
            self.add_timestamp(existing_file)
            logging.info(f'Removing old file: {existing_file}')
            os.remove(existing_file)
            # Rename the file
            self.rename_file(new_file, existing_file)
        except Exception as err:
            logging.error(f'Failed to handle existing requirements file: {err}')

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
    def rename_file(file, renamed_file) -> None:
        logging.info(f'Renaming: {file} to: {renamed_file}...')
        os.rename(file, renamed_file)
        logging.info('File was renamed successfully.')

