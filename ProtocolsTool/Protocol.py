from Sequence import Sequence
import logging


class Protocol:
    index = 0

    def __init__(self, name, mr_type, field_strength, grad_coil_type=""):
        self._name: str = name
        self._sequences: list[Sequence] = []
        self._mr_type: str = mr_type
        self._field_strength: str = field_strength
        self._grad_coil_type: str = grad_coil_type  # Appears in original ProtocolExtractor but has no use here.
        self._protocol_index = Protocol.index
        Protocol.index += 1

    def add_sequence(self, sequence: Sequence):
        logging.info(f'Adding sequence {sequence.name} to {self._name}')
        self._sequences.append(sequence)

    def get_sequence(self, sequence_name):
        for sequence in self._sequences:
            if sequence.name == sequence_name:
                return sequence
        return None

    def to_dict(self):
        sequences_dict = [sequence.to_dict() for sequence in self._sequences]
        return {"Protocol:": self._name, "Sequences": sequences_dict, "MR Type": self._mr_type,
                "Field Strength": self._field_strength, "Grad Coil Type": self._grad_coil_type,
                "Protocol Index": self.index}

    def __str__(self):
        str = (f'Protocol name: {self._name} \nMR Type: {self._mr_type}\nField Strength: {self._field_strength}\n'
               f'Gradient Coil Type: {self._grad_coil_type}\nProtocol Index: {self.index} \nSequences: \n')
        for sequence in self._sequences:
            str += sequence.__str__() + '\n'
        return str


if __name__ == '__main__':
    protocol = Protocol('FUS-Tx-BrainBBB746-HEAD', 'mrtype', 'fs', 'gcy')
    protocol.add_sequence('***CALIBRATION***')
    protocol.add_sequence('***sequence2***')
    protocol2 = Protocol('FUS-Tx-BrainBBB746-HEAD2', 'mrtype2', 'fs2', 'gcy2')
    sequence = protocol.get_sequence('***sequence2***')
    print(sequence)
