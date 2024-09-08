from pathlib import Path
import os


class ApplicationParameters:
    def __init__(self, path_for_req, path_for_tar, mr_name):
        self.macro_excel_file = str(f'{os.getcwd()}\\PY_PERSONAL.XLSB')
        self.path_for_req = path_for_req
        self.path_for_tar = path_for_tar
        self.mr_name = mr_name

# D:\\TarTool\\Premier\\Auto\\protocol.tar
# C:\\Users\\RotemG\\PycharmProjects\\ProtocolsTool\\Data\\MR30_Premier\\MR30_Premier_Requirements.xlsx