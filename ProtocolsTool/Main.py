import logging
import argparse
import os.path
from datetime import datetime
from pathlib import Path
import Requirements
from openpyxl.packaging.custom import StringProperty

from Compare import Compare
from ApplicationParameters import ApplicationParameters
import openpyxl


def check_execution_marker(file_path: str) -> bool:
    """
    :param file_path: path to the Excel file that needs to be checked if contains execution marker.
    :return: True if execution marker exists in file.
    """
    marker_const = 'ProtocoLab'
    try:
        wb = openpyxl.load_workbook(file_path)
    except Exception as err:
        logging.error(f"Cannot load workbook: {file_path}. {err}")

    # Check if the script execution marker is set
    doc_properties = wb.custom_doc_props
    if marker_const in doc_properties.names:
        logging.info(f"{marker_const} field was found in: {file_path}")
        return True
    else:
        logging.info(f"{marker_const} field was not found in: {file_path}")
        return False

def add_execution_marker(file_path) -> None:
    marker_const = 'ProtocoLab'
    try:
        wb = openpyxl.load_workbook(file_path)
    except Exception as err:
        logging.error(f"Cannot load workbook: {file_path}. {err}")

    # Add ProtocoLab field
    wb.custom_doc_props.append(StringProperty(name=marker_const, value="Executed"))
    logging.info(f"Added {marker_const} to {file_path}.")

    try:
        wb.save(file_path)
    except Exception as err:
        logging.error(f"Cannot save workbook: {file_path}. {err}")


# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-r", "--req_path", required=True, help="Full path to requirements file")
parser.add_argument("-t", "--tar_path", required=True, help="Full path to tar file")
args = parser.parse_args()

# Change the log file name
mr_name = Path(args.req_path).name.replace('_Requirements.xlsx', '')

# Initialize program parameters
parameters = ApplicationParameters(args.req_path, args.tar_path, mr_name)

# Create Log
log_folder = os.path.join(os.getcwd(), "CompareLogs")
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
data_and_time = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
log_name = f'{parameters.mr_name}_{data_and_time}.log'
logging.basicConfig(filemode='w', filename=os.path.join(log_folder, log_name),
                    format='%(asctime)s.%(msecs)03d %(levelname)-8s %('
                           'funcName)-32s'
                           '%(message)s', datefmt='%d-%m-%Y %H:%M:%S',
                    level=logging.INFO)

# Check execution marker
is_execution_marker_exist = check_execution_marker(parameters.path_for_req)
if not is_execution_marker_exist:
    Requirements.excel_rearrangement(parameters.mr_name, parameters.macro_excel_file)
    add_execution_marker(parameters.path_for_req)

# Compare
Compare(parameters)
