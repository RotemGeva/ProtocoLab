class Parameter:
    def __init__(self, name: str, value, range_flag: bool = False, min_value=0, max_value=0):
        self._name = name
        self._value = str(value)
        self._range_flag: bool = range_flag
        self._min_value = min_value
        self._max_value = max_value

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    def to_dict(self):
        return {"Name:": self._name, "Value": self._value, "Range Flag": self._range_flag,
                "Min Value": self._min_value, "Max Value": self._max_value}

    def __str__(self):
        return f'{self._name}, {self._value} [{self._range_flag}, {self._min_value}-{self._max_value}]'


if __name__ == '__main__':
    parameter = Parameter('Rotem', 3)
    print(parameter)
