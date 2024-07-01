import logging
import argparse
from datetime import datetime
#from numpy.f2py import __version__
from Compare import Compare
from ApplicationParameters import ApplicationParameters

# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-r", "--req_path", required= True, help="Full path to requirements file")
parser.add_argument("-t", "--tar_path", required= True, help="Full path to tar file")
args = parser.parse_args()

# Create Log
data_and_time = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
log_name = f'AutoProtocol_{data_and_time}.log'
logging.basicConfig(filemode='w', filename=log_name,format='%(asctime)s.%(msecs)03d %(levelname)-8s %(funcName)-32s '
                                                           '%(message)s',datefmt='%d-%m-%Y %H:%M:%S', level=logging.INFO)
#logging.info(f'AutoProtocol version: {__version__}')

# Initialize program parameters
parameters = ApplicationParameters()
parameters.path_for_req = args.req_path
parameters.path_for_tar = args.tar_path
Compare(parameters)
