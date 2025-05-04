import logging
import os
import glob
import json
import sys
from datetime import datetime


DEFAULT_LOG_DIR = "ExternalToolLogs"
def setup_logging(log_name, log_level=logging.INFO, console_log_level=logging.INFO):
    current_timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    log_filepath = os.path.join(os.getcwd(), DEFAULT_LOG_DIR, f"{log_name}-{current_timestamp}.log")
    os.makedirs(os.path.dirname(log_filepath), exist_ok=True)

    log_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d %(levelname)-8s %(module)s  %(funcName)-32s   %(message)s',
        datefmt='%d-%m-%Y %H:%M:%S'
    )

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # File handler
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_log_level)
    root_logger.addHandler(console_handler)

def read_mr_sw_type() -> str:
    """
    Reads MR SW type from yaml file, for Siemens scenario.
    :return: string that contains the SW type of the MR.
    """
    base_dir = os.path.join(os.getcwd(), 'Data', 'temp')
    yaml_file = glob.glob(os.path.join(base_dir, "*.yaml"))[0]
    logging.info(f'Reading MR SW type from: {yaml_file}')
    try:
        with open(yaml_file, 'r') as file:
            data = json.load(file)
            mr_sw_type = data[00]['MR Type']
            logging.info(f'MR SW type is: {mr_sw_type}')
            return 'VA' if 'VA' in mr_sw_type else 'VE'
    except Exception as e:
        logging.error(f'Failed to read MR SW type from yaml.\n error: {e}')
        raise Exception(f'Failed to read MR SW type from yaml.\n error: {e}')


class ProgressReporter:
    total_steps = 0
    current_step = 0

    @classmethod
    def initialize(cls, total_steps):
        cls.total_steps = total_steps
        cls.current_step = 0
        logging.info('Initialized progress reporter')

    @classmethod
    def report_progress(cls, message, steps_done=1):
        cls.current_step += steps_done
        percentage = (cls.current_step / cls.total_steps) * 100
        print(f"Progress: {percentage:.2f}% - {message}")

    @classmethod
    def get_progress(cls):
        return (cls.current_step / cls.total_steps) * 100 if cls.total_steps > 0 else 0