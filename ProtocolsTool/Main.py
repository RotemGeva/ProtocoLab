import logging
import argparse
import os
from datetime import datetime
from pathlib import Path
from Compare import Compare
from ApplicationParameters import ApplicationParameters
from Requirements import Requirements

# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-r", "--req_path", help="Full path to requirements file")
parser.add_argument("-t", "--tar_path", required=True, help="Full path to tar file")
parser.add_argument("-f", "--function", required=True, help="Compare (c), Make ""requirements (r)")
parser.add_argument("-p", "--protocols", nargs='+', help="List of wanted protocols")
args = parser.parse_args()

# Change the log file name
if args.req_path:
    mr_name = Path(args.req_path).name.replace('_Requirements.xlsx', '')
else:
    mr_name = os.path.splitext(os.path.basename(args.tar_path))[0]

# Initialize program parameters
if args.protocols is None:
    parameters = ApplicationParameters(args.req_path, args.tar_path, mr_name, [])
else:
    parameters = ApplicationParameters(args.req_path, args.tar_path, mr_name, args.protocols)

# Create Log
log_folder = os.path.join(os.getcwd(), "ExternalToolLogs")
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
data_and_time = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
log_name = f'{parameters.mr_name}_{data_and_time}.log'
logging.basicConfig(filemode='w', filename=os.path.join(log_folder, log_name),
                    format='%(asctime)s.%(msecs)03d %(levelname)-8s %('
                           'funcName)-32s'
                           '%(message)s', datefmt='%d-%m-%Y %H:%M:%S',
                    level=logging.INFO)

# Compare\Make Requirements
match args.function:
    case 'c':
        Compare(parameters)
    case 'r':
        Requirements(parameters)
