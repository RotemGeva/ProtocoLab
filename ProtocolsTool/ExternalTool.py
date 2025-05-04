import logging
import argparse
import os
from pathlib import Path
from ApplicationParameters import ApplicationParameters
from Compare import Compare
from Requirements import Requirements
from XMLParser import XMLParser
from utils import ProgressReporter, setup_logging

# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-r", "--req_path", help="Full path to requirements file")
parser.add_argument("-a", "--actual_path", required=True, help="Full path to the file that contains actual data")
parser.add_argument("-f", "--function", required=True, choices=['c', 'r', 'x'],
                    help="Compare (c), Create requirements (r), Parse XML (x)")
parser.add_argument("-p", "--protocols", nargs='+', help="List of protocols")
args = parser.parse_args()

match args.function:
    case 'c':  # Compare
        ProgressReporter.initialize(total_steps=1)  # No report progress in comparison
        mr_name = Path(args.req_path).name.replace('_Requirements.xlsx', '')
        log_file_name = "Compare-" + mr_name
        setup_logging(log_file_name)
        parameters = ApplicationParameters(mr_name=mr_name, actual_path=args.actual_path, req_path=args.req_path)
        logging.info(f'Compare request with parameters: {parameters.__str__()}.')
        Compare(parameters)
    case 'r':  # Create requirements
        mr_name = os.path.splitext(os.path.basename(args.actual_path))[0]
        log_file_name = "Requirements-" + mr_name
        setup_logging(log_file_name)
        ProgressReporter.initialize(total_steps=5)
        ProgressReporter.report_progress("Initializing application parameters", steps_done=0)
        parameters = ApplicationParameters(mr_name=mr_name, actual_path=args.actual_path, protocols=args.protocols)
        logging.info(f'Making requirements request with parameters: {parameters.__str__()}.')
        Requirements(parameters)
    case 'x':  # Parse XML
        mr_name = os.path.splitext(os.path.basename(args.actual_path))[0]
        log_file_name = "Parsing XML-" + mr_name
        setup_logging(log_file_name)
        xml_object = XMLParser(args.actual_path)
        xml_object.output_all_protocol_names()
