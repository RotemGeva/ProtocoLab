import logging
import argparse
import os
from datetime import datetime
from pathlib import Path
from ApplicationParameters import ApplicationParameters
from Compare import Compare
from Requirements import Requirements


# Create log
def create_log_file(name: str):
    log_folder_path = os.path.join(os.getcwd(), "ExternalToolLogs")
    if not os.path.exists(log_folder_path):
        os.makedirs(log_folder_path)
    data_and_time = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    log_name = f'{name}_{data_and_time}.log'
    logging.basicConfig(filemode='w', filename=os.path.join(log_folder_path, log_name),
                        format='%(asctime)s.%(msecs)03d %(levelname)-8s %('
                               'funcName)-32s'
                               '%(message)s', datefmt='%d-%m-%Y %H:%M:%S',
                        level=logging.INFO)
    logging.info('Log initialized.')


# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-r", "--req_path", help="Full path to requirements file")
parser.add_argument("-t", "--tar_path", required=True, help="Full path to tar file")
parser.add_argument("-f", "--function", required=True, help="Compare (c), Make ""requirements (r)")
parser.add_argument("-p", "--protocols", nargs='+', help="List of protocols")
args = parser.parse_args()


# Compare\Make Requirements
match args.function:
    case 'c':
        mr_name = Path(args.req_path).name.replace('_Requirements.xlsx', '')
        create_log_file(name=mr_name)
        parameters = ApplicationParameters(args.req_path, args.tar_path, mr_name, args.protocols)
        logging.info(f'Compare request with parameters: {parameters.__str__()}.')
        Compare(parameters)
    case 'r':
        mr_name = os.path.splitext(os.path.basename(args.tar_path))[0]
        create_log_file(name=mr_name)
        if args.protocols is None:
            parameters = ApplicationParameters(args.req_path, args.tar_path, mr_name, [])
        else:
            parameters = ApplicationParameters(args.req_path, args.tar_path, mr_name, args.protocols)
        logging.info(f'Making requirements request with parameters: {parameters.__str__()}.')
        Requirements(parameters)
