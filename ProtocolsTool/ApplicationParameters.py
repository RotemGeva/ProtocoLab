import os


class ApplicationParameters:
    def __init__(self, path_for_req, path_for_tar, mr_name, protocols=None):
        self.macro_excel_file = str(f'{os.getcwd()}\\PY_PERSONAL.XLSB')
        self.path_for_req = path_for_req
        self.path_for_tar = path_for_tar
        self.mr_name = mr_name
        if protocols is None:
            self.protocols = []
        else:
            self.protocols = protocols
        self.mr_vendor = self.get_mr_vendor()

    def get_mr_vendor(self):
        extension = os.path.splitext(self.path_for_tar)[1]
        match extension:
            case '.tar':
                return 'GE'
            case '.xml':
                return 'Siemens'

    def __str__(self):
        return (
            f'Macro filepath: {self.macro_excel_file}, requirements filepath: {self.path_for_req}, compare '
            f'filepath: {self.path_for_tar}'
            f', MR name: {self.mr_name}, selected protocols: {self.protocols}, MR vendor: {self.mr_vendor}')
