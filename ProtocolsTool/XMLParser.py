import xml.etree.ElementTree as ET
from Protocol import Protocol
from Parameter import Parameter
from Sequence import Sequence
import logging
import json


class XMLParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.tree = None
        self.root = None

    def parse(self):
        try:
            self.tree = ET.parse(self.file_path)
            self.root = self.tree.getroot()
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")

    @property
    def get_root(self):
        return self.root

    def get_all_protocol_elements(self) -> list[ET]:
        """
        Finds all protocol title elements that are found under "program" tag.
        :return: A list of all the protocol title elements.
        """
        # To get protocol name: protocol.get('name')
        logging.info(f'Retrieving all protocols elements from root...')
        protocols: list[ET] = []
        for protocol in self.root.iter('program'):
            protocols.append(protocol)
        logging.info(f'Found {len(protocols)} protocols within the whole file...')
        return protocols

    def get_all_sequence_elements(self) -> list[ET]:
        """
        Finds all sequence elements that contain sequence parameters values.
        Each sequence (and its parameters) is enclosed by "PrintProtocol" tag.
        :return: A list of all the sequence elements.
        """
        logging.info('Retrieving all sequences elements from root...')
        sequence_elements: list[ET] = []
        for sequence_element in self.root.iter('PrintProtocol'):
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
        logging.info(f'Filling out parameters for: {sequence}...')
        for prot_parameter in sequence_element.iter('ProtParameter'):
            name = prot_parameter.find('Label').text
            value = prot_parameter.find('ValueAndUnit').text
            parameter = Parameter(name, value)
            logging.info(f'Adding parameter: {parameter}...')
            sequence.add_parameter(parameter)

    @staticmethod
    def get_mr_general_info(protocol: ET) -> tuple:
        """
        Finds the last sequence of the protocol (the identifier sequence, a dummy sequence that contains a description of
        the MR)
        :param protocol: The protocol that contains the dummy sequence. Currently, every protocol contains the
        dummy sequence.
        :return: A tuple that the first element contain the type of the MR (e.g. Lumina-VA50) and the
        second elements contains the field strength (e.g. 3T).
        """
        try:
            logging.info('Retrieving MR general info...')
            for sequence in protocol.iter('NormalStep_decision_branch'):
                sequence_name = sequence.get('name')
                if sequence_name.__contains__('*'):
                    info = sequence_name.split('_')
                    mr_type = f'{info[1]}-{info[2]}'  # Info[1] - e.g. Lumina, info[2] - e.g. VA50.
                    field_strength = info[0].split(' ')[1]
                    logging.info(f'Successfully retrieved: {mr_type}, {field_strength}')
                    return mr_type, field_strength
        except Exception as e:
            logging.warning(f'Failed to retrieve mr information from last sequence. error: {e}')
            return 'mr_type', 'field_strength'

    @staticmethod
    def custom_serializer(obj):
        if hasattr(obj, 'to_dict'):  # Check if the object has a 'to_dict' method
            return obj.to_dict()

    @staticmethod
    def create_protocols(xml_parser, mr_type, field_strength, protocol_elements, sequence_elements):
        print_protocol_index = 0  # To iterate PrintProtocol elements within the whole file
        protocols_list = []
        # Create protocols according to xml file
        for protocol_element in protocol_elements:
            current_protocol_name = protocol_element.get('name')
            current_protocol = Protocol(name=current_protocol_name, mr_type=mr_type, field_strength=field_strength,
                                        grad_coil_type='gct')

            # Add sequences to existing protocol
            sequences_names_for_protocol = xml_parser.get_all_sequences_names(protocol_element)
            sequence_elements_for_protocol = sequence_elements[
                                             print_protocol_index:print_protocol_index + len(
                                                 sequences_names_for_protocol)]
            for index, sequence_element in enumerate(sequence_elements_for_protocol):
                sequence = Sequence(sequences_names_for_protocol[index])
                xml_parser.fill_in_parameters(sequence_element, sequence)
                current_protocol.add_sequence(sequence)
            print_protocol_index += len(sequences_names_for_protocol)
            protocols_list.append(current_protocol)
        return protocols_list

    @staticmethod
    def handle_parsing(xml_filepath):
        # Parse xml file
        xml_parser = XMLParser(xml_filepath)
        xml_parser.parse()

        # Retrieve all relevant elements
        protocol_elements = xml_parser.get_all_protocol_elements()
        sequence_elements = xml_parser.get_all_sequence_elements()

        # Retrieve general info regrading MR type and field strength
        mr_type, field_strength = xml_parser.get_mr_general_info(protocol_elements[0])

        # Parse xml file into protocols list
        protocols_list = xml_parser.create_protocols(xml_parser, mr_type, field_strength, protocol_elements, sequence_elements)

        # Dump protocols to json
        protocols_dict = [protocol.to_dict() for protocol in protocols_list]
        json_data = json.dumps(protocols_dict, default=xml_parser.custom_serializer, indent=4)
        return json_data


if __name__ == '__main__':
    data = XMLParser.handle_parsing('VA50_LUMINA.xml')
    print(data)
