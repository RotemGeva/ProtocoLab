import logging
import argparse
import os.path
from datetime import datetime
from pathlib import Path
import Requirements

from Compare import Compare
from ApplicationParameters import ApplicationParameters

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

# Fix requirements
Requirements.excel_rearrangement(parameters.mr_name, parameters.macro_excel_file)

# Compare
Compare(parameters)
