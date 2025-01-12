import glob
import logging
import argparse
import os
import time
from datetime import datetime
from pathlib import Path
from ApplicationParameters import ApplicationParameters
from Compare import Compare
from Requirements import Requirements


# Create log
def create_log_file(name: str, existed_log_file=None):
    """
    Handles log creation.
    :param name: MR name to concatenate to log file name.
    :param existed_log_file: If previous log file exists. Append logs.
    """
    log_folder_path = os.path.join(os.getcwd(), "ExternalToolLogs")
    if not os.path.exists(log_folder_path):
        os.makedirs(log_folder_path)
    if existed_log_file is None:
        data_and_time = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        log_name = f'{name}_{data_and_time}.log'
        logging.basicConfig(filemode='w', filename=os.path.join(log_folder_path, log_name),
                            format='%(asctime)s.%(msecs)03d %(levelname)-8s %('
                                   'funcName)-32s'
                                   '%(message)s', datefmt='%d-%m-%Y %H:%M:%S',
                            level=logging.INFO)
    else:
        logging.basicConfig(filemode='a', filename=existed_log_file,
                            format='%(asctime)s.%(msecs)03d %(levelname)-8s %('
                                   'funcName)-32s'
                                   '%(message)s', datefmt='%d-%m-%Y %H:%M:%S',
                            level=logging.INFO)
    logging.info('Log was initialized.')


def check_previous_log_files():
    """
    Checks if there is a log file that was modified less than 2 minute ago.
    :return: Returns the last modified log file path.
    """
    log_folder_path = os.path.join(os.getcwd(), "ExternalToolLogs")
    if os.path.exists(log_folder_path):
        if len(os.listdir(log_folder_path)) != 0:
            file_type = r'\*log'
            files = glob.glob(log_folder_path + file_type)
            max_file = max(files, key=os.path.getmtime)
            current_time = time.time()
            time_difference = abs(os.path.getmtime(max_file) - current_time)
            if time_difference < 120:
                return max_file


# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-r", "--req_path", help="Full path to requirements file")
parser.add_argument("-t", "--tar_path", required=True, help="Full path to tar file")
parser.add_argument("-f", "--function", required=True, choices=['c', 'r', 'p'],
                    help="Compare (c), Create requirements (r)")
parser.add_argument("-p", "--protocols", nargs='+', help="List of protocols")
args = parser.parse_args()

# Concatenate log files
# last_log_file = check_previous_log_files()

match args.function:
    case 'c':  # Compare
        mr_name = Path(args.req_path).name.replace('_Requirements.xlsx', '')
        create_log_file(name="Compare-" + mr_name)
        parameters = ApplicationParameters(args.req_path, args.tar_path, mr_name, args.protocols)
        logging.info(f'Compare request with parameters: {parameters.__str__()}.')
        Compare(parameters)
    case 'r':  # Create requirements
        mr_name = os.path.splitext(os.path.basename(args.tar_path))[0]
        create_log_file(name="Requirements-" + mr_name)
        if args.protocols is None:
            parameters = ApplicationParameters(args.req_path, args.tar_path, mr_name, [])
        else:
            parameters = ApplicationParameters(args.req_path, args.tar_path, mr_name, args.protocols)
        logging.info(f'Making requirements request with parameters: {parameters.__str__()}.')
        Requirements(parameters)
