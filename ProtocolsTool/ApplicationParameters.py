import os


class ApplicationParameters:
    def __init__(self, path_for_req, path_for_tar, mr_name, protocols):
        self.macro_excel_file = str(f'{os.getcwd()}\\PY_PERSONAL.XLSB')
        self.path_for_req = path_for_req
        self.path_for_tar = path_for_tar
        self.mr_name = mr_name
        self.protocols = protocols

    def __str__(self):
        return (f'Macro file path: {self.macro_excel_file}, requirements file: {self.path_for_req}, tar file path: {self.path_for_tar}'
                f', MR name: {self.mr_name}, selected protocols: {self.protocols}')