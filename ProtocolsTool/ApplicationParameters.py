import os


class ApplicationParameters:
    GE = 'GE'
    SIEMENS = 'Siemens'

    def __init__(self, mr_name, actual_path, req_path=None, protocols=None):
        self.req_path = req_path
        self.actual_path = actual_path
        self.mr_name = mr_name
        self.mr_vendor = self.get_mr_vendor()
        if self.mr_vendor == self.GE:
            self.macro_excel_file = str(f'{os.getcwd()}\\GE_PY_PERSONAL.XLSB')
        elif self.mr_vendor == self.SIEMENS:
            self.macro_excel_file = str(f'{os.getcwd()}\\SIEMENS_PY_PERSONAL.XLSB')
        if protocols is None:
            self.protocols = []
        else:
            self.protocols = protocols

    def get_mr_vendor(self):
        extension = os.path.splitext(self.actual_path)[1]
        match extension:
            case '.tar':
                return self.GE
            case '.xml':
                return self.SIEMENS

    def __str__(self):
        return (
            f'Macro filepath: {self.macro_excel_file}, requirements filepath: {self.req_path}, actual '
            f'filepath: {self.actual_path}'
            f', MR name: {self.mr_name}, MR vendor: {self.mr_vendor}, selected protocols: {self.protocols}')
