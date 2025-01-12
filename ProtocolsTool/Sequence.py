from Parameter import Parameter
import logging


class Sequence:
    def __init__(self, name: str):
        self._name = name
        self._parameters: dict[Parameter.name, Parameter] = {}

    @property
    def name(self):
        return self._name

    @property
    def parameters(self):
        return self._parameters

    def add_parameter(self, parameter: Parameter) -> None:
        # Add parameter to sequence in not already exists
        if not self.is_parameter_exist(parameter.name):
            logging.info('The parameter is not in sequence. Adding now...')
            self._parameters[parameter.name] = parameter

    def is_parameter_exist(self, name: str) -> bool:
        # A parameter can appear twice in xml file (with the same value).
        logging.info(f'Checking if parameter {name} already exists in {self._name}...')
        return name in self._parameters.keys()

    def __str__(self):
        str = f'Sequence name: {self._name} \nParameters:\n'
        for parameter in self._parameters.values():
            str += parameter.__str__() + ' \n'
        return str


if __name__ == '__main__':
    sequence = Sequence('Tracking')
    parameter = Parameter("Start measurements", "Single Measurement")
    parameter2 = Parameter("Start measurements2", "Single Measurement2")
    sequence.add_parameter(parameter)
    sequence.add_parameter(parameter2)
    print(sequence)
