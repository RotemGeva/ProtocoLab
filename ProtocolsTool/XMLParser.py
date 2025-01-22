import os.path
import re
import xml.etree.ElementTree as ET
import openpyxl

from Protocol import Protocol
from Parameter import Parameter
from Sequence import Sequence
import logging
import json


class XMLParser:
    def __init__(self, file_path):
        self.file_path = file_path
        try:
            self.tree = ET.parse(self.file_path)
            self.root = self.tree.getroot()
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")

    @property
    def get_root(self):
        return self.root

    def get_mr_siemens_info(self) -> tuple:
        # TODO: think about what to do in VE case - there is no field strength.
        """
        Checks whether the MR SW type is VA or VE and whether field strength is 1.5T or 3T.
        :return: A tuple that contains the above.
        """
        try:
            logging.info('Retrieving MR general info from Siemens line...')
            mr_info = self.root.find('.//HeaderTitle').text
            logging.info(f'Found: {mr_info}')
            sw_type = 'VA' if 'VA' in mr_info else 'VE'
            if sw_type == 'VA':
                logging.info(f'SW type is: {sw_type}')
                field_strength = '3T' if '3.0T' in mr_info else '1.5T'
                logging.info(f'Field strength is: {field_strength}')
                return sw_type, field_strength
            else:
                return sw_type, 'Not Specified'
        except Exception as e:
            logging.warning(f'Failed to retrieve MR information from Siemens line. error: {e}')
            raise Exception()

    def get_all_protocol_elements(self) -> list[ET]:
        """
        Finds all protocol title elements that are found under "program" tag.
        :return: A list of all the protocol title elements.
        """
        logging.info(f'Retrieving all protocols elements from root...')
        protocols: list[ET] = []
        for protocol in self.root.iter('program'):
            protocols.append(protocol)
        logging.info(f'Found {len(protocols)} protocols within the whole file...')
        return protocols

    def output_all_protocol_names(self, mr_name, output_path='Data\\temp\\Requirements') -> None:
        """
        Finds all protocol title elements that are found under "program" tag.
        :return: A list of all the protocol title elements.
        """
        logging.info(f'Outputting all protocols names...')
        protocols: list[str] = []
        for protocol in self.root.iter('program'):
            protocols.append(protocol.get('name'))
        try:
            with open(f'{output_path}\\protocols_list-{mr_name}.txt', 'w') as file:
                file.write(str(protocols)[1:-1].replace("'", "") + "\n")
        except Exception as e:
            logging.error(f'Failed to export protocols names. error: {e}')
            raise Exception()

    def get_all_sequence_elements(self) -> list[ET]:
        """
        Finds all sequence elements that contain sequence parameters values.
        Each sequence (and its parameters) is enclosed by "PrintProtocol" tag.
        :return: A list of all the sequence elements.
        """
        logging.info('Retrieving all sequences elements from root...')
        sequence_elements: list[ET] = []
        for sequence_element in self.root.iter('PrintProtocol'):  # Iter does not preserve the order of the elements
            sequence_elements.append(sequence_element)
        logging.info(f'Found {len(sequence_elements)} sequences within the whole xml file.')
        return sequence_elements

    @staticmethod
    def get_all_sequences_names(protocol: ET) -> list[str]:
        """
        Finds all the names of the sequences within a protocol tag.
        :param protocol: A xml element with "program" tag that encloses all sequences names inside.
        :return: A list with the sequences names within the given protocol.
        """
        protocol_name = protocol.get('name')
        logging.info(f'Retrieving all sequences names for: {protocol_name}...')
        sequences_names = []
        for sequence in protocol.iter('NormalStep_decision_branch'):
            sequences_names.append(sequence.get('name'))
        logging.info(f'The following sequences were found: {sequences_names}.')
        return sequences_names

    @staticmethod
    def fill_in_parameters(sequence_element: ET, sequence: Sequence) -> None:
        """
        Fills out the parameters in the given sequence.
        :param sequence_element: The xml element that contains the information regarding the parameters.
        :param sequence: The sequence object that should be filled with the parameters.
        """
        logging.info(f'Filling out parameters for: {sequence.name}...')
        for prot_parameter in sequence_element.iter('ProtParameter'):
            name = prot_parameter.find('Label').text
            value = prot_parameter.find('ValueAndUnit').text.strip()
            parameter = Parameter(name, value)
            logging.info(f'Adding parameter: {parameter}...')
            sequence.add_parameter(parameter)
        scan_time = XMLParser.get_scan_time(sequence_element)
        scan_time_parameter = Parameter('Scan Time', scan_time)
        logging.info(f'Adding scan time parameter: {scan_time_parameter}...')
        sequence.add_parameter(scan_time_parameter)

    def get_mr_home_info(self, protocol: ET) -> tuple:
        """
        Finds the last sequence of the protocol (the identifier sequence, a dummy sequence that contains a description of
        the MR)
        :param protocol: The protocol that contains the dummy sequence. Currently, every protocol contains the
        dummy sequence.
        :return: A tuple that the first element contain the type of the MR (e.g. Lumina-VA50) and the
        second elements contains the field strength (e.g. 3T).
        """
        try:
            protocol_name = protocol.get('name')
            logging.info(f'Retrieving MR general info from last sequence of {protocol_name}...')
            for sequence in protocol.iter('NormalStep_decision_branch'):
                sequence_name = sequence.get('name')
                if sequence_name.__contains__('*'):
                    info = sequence_name.split('_')
                    sw_type = f'{info[1]}-{info[2]}'  # Info[1] - e.g. Lumina, info[2] - e.g. VA50.
                    field_strength = info[0].split(' ')[1]
                    logging.info(f'Successfully retrieved: {sw_type}, {field_strength}')
                    return sw_type, field_strength
        except Exception as e:
            logging.warning(f'Failed to retrieve mr information from last sequence. error: {e}')
            self.get_mr_siemens_info()

    @staticmethod
    def custom_serializer(obj):
        if hasattr(obj, 'to_dict'):  # Check if the object has a 'to_dict' method
            return obj.to_dict()

    @staticmethod
    def create_protocols(xml_handler, mr_type, field_strength, protocol_elements, sequence_elements):
        """
        Creates the protocol list structure.
        :param xml_handler: XML object.
        :param mr_type: MR SW type.
        :param field_strength: Field strength
        :param protocol_elements: All protocol elements from XML file.
        :param sequence_elements: All sequence elements from XML file.
        :return: A list of filled protocols. Each protocol contains a sequence that is filled with parameters.
        """
        print_protocol_index = 0  # To iterate PrintProtocol elements within the whole file
        protocols_list = []
        # Create protocols according to xml file
        for protocol_element in protocol_elements:
            current_protocol_name = protocol_element.get('name')
            current_protocol = Protocol(name=current_protocol_name, mr_type=mr_type, field_strength=field_strength,
                                        grad_coil_type='gct')

            # Add sequences to existing protocol
            sequences_names_for_protocol = xml_handler.get_all_sequences_names(protocol_element)
            sequence_elements_for_protocol = sequence_elements[
                                             print_protocol_index:print_protocol_index + len(
                                                 sequences_names_for_protocol)]
            for index, sequence_element in enumerate(sequence_elements_for_protocol):
                sequence_name = xml_handler.get_sequence_name(sequence_element)
                if '*' not in sequence_name:
                    sequence = Sequence(sequence_name)
                    xml_handler.fill_in_parameters(sequence_element, sequence)
                    current_protocol.add_sequence(sequence)
            print_protocol_index += len(sequences_names_for_protocol)
            protocols_list.append(current_protocol)
        return protocols_list

    @staticmethod
    def parse(xml_filepath, mr_name, output_path='Data\\temp\\Requirements'):
        """
        Handles all xml parsing in high level.
        :param xml_filepath: Filepath of the xml file.
        :param mr_name: The MR type.
        :param output_path: Output full path for exporting yaml.
        """
        # Parse xml file
        xml_handler = XMLParser(xml_filepath)

        # Retrieve all relevant elements
        protocol_elements = xml_handler.get_all_protocol_elements()
        sequence_elements = xml_handler.get_all_sequence_elements()

        # Retrieve general info regrading MR type and field strength
        mr_type, field_strength = xml_handler.get_mr_home_info(protocol_elements[0])

        # Parse xml file into protocols list
        protocols_list = xml_handler.create_protocols(xml_handler, mr_type, field_strength, protocol_elements,
                                                      sequence_elements)

        # Dump protocols to json
        XMLParser.export_parsing(xml_handler, protocols_list, output_path, mr_name)

    @staticmethod
    def export_parsing(xml_handler, protocols_list, output_path, mr_name):
        logging.info('Exporting the parsed file...')
        protocols_dict = [protocol.to_dict() for protocol in protocols_list]
        data = json.dumps(protocols_dict, default=xml_handler.custom_serializer, indent=4)
        try:
            with open(f'{output_path}\\{mr_name}.yaml', 'w') as file:
                file.write(data)
        except Exception as e:
            logging.error(f'Failed to export the parsed file. error: {e}')
            raise Exception()

    @staticmethod
    def retrieve_relevant_protocols_names(req_filepath):
        try:
            logging.info(f'Try to open: {req_filepath}...')
            requirement_file = openpyxl.load_workbook(req_filepath)
        except Exception as err:
            logging.info(f'Could not open file.\nError: {err}.')
            raise Exception(f'Could not Excel file.\nError: {err}.')
        try:
            logging.info('Retrieving sheet names from file...')
            list_of_all_sheets = requirement_file.sheetnames
            logging.info(f'Retrieved the following sheets names: {list_of_all_sheets}.')
        except Exception as err:
            logging.info(f'Could not retrieve sheets name from Excel file.\nError: {err}.')
            raise Exception(f'Could not receive sheets name from Excel file.\nError: {err}.')
        return list_of_all_sheets

    @staticmethod
    def get_sequence_name(sequence: ET) -> str:
        full_path = sequence.find('.//HeaderProtPath').text
        name = os.path.basename(full_path)
        return name

    @staticmethod
    def get_protocol_of_sequence(sequence: ET) -> str:
        full_path = sequence.find('.//HeaderProtPath').text
        name = os.path.basename(os.path.dirname(full_path))
        return name

    @staticmethod
    def get_scan_time(sequence: ET):
        """
        Retrieves scan time of a given sequence.
        :param sequence: Sequence elements that contains the line with scan time info.
        :return: Scan time in seconds.
        """
        sequence_name = XMLParser.get_sequence_name(sequence)
        logging.info(f'Searching scan time for: {sequence_name}')
        regex_lists = [r"TA: (\d+) sec", r"TA: (\d+) s", r"TA: (\d+):(\d+)", r"TA: (\d+):(\d+) min", r"TA: (\d\.\d) s"]
        scan_time_line = sequence.find('.//HeaderProperty').text
        logging.info(f'Scan time line is: {scan_time_line}')
        for regex in regex_lists:
            match = re.search(regex, scan_time_line)
            if match:
                if match.lastindex == 1:  # Case: "TA: <seconds> sec" or "TA: <seconds> s"
                    scan_time = match.group(1)
                elif match.lastindex == 2:  # Case: "TA: <minutes>:<seconds>"
                    # Convert minutes and seconds to total seconds
                    minutes = int(match.group(1))
                    seconds = int(match.group(2))
                    scan_time = minutes * 60 + seconds
                logging.info(f'Scan time is: {scan_time} seconds')
                return scan_time
        logging.warning('Scan time was not found.')
        return None


if __name__ == '__main__':
    parse = XMLParser('VA50_LUMINA.xml')
    sequences = parse.get_all_sequence_elements()
    XMLParser.get_scan_time(sequences[0])
