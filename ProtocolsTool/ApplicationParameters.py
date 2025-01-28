import os


class ApplicationParameters:
    def __init__(self, mr_name, actual_path, req_path=None, protocols=None):
        self.macro_excel_file = str(f'{os.getcwd()}\\PY_PERSONAL.XLSB')
        self.req_path = req_path
        self.actual_path = actual_path
        self.mr_name = mr_name
        self.mr_vendor = self.get_mr_vendor()
        # TODO: Complete scenarios of macro filepath
        if self.mr_vendor == 'GE':
            pass
        elif self.mr_vendor == 'Siemens':
            pass
        if protocols is None:
            self.protocols = []
        else:
            self.protocols = protocols

    def get_mr_vendor(self):
        extension = os.path.splitext(self.actual_path)[1]
        match extension:
            case '.tar':
                return 'GE'
            case '.xml':
                return 'Siemens'

    def __str__(self):
        return (
            f'Macro filepath: {self.macro_excel_file}, requirements filepath: {self.req_path}, actual '
            f'filepath: {self.actual_path}'
            f', MR name: {self.mr_name}, MR vendor: {self.mr_vendor}, selected protocols: {self.protocols}')
