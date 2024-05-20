import logging
import os


class ApplicationParameters:
    def __init__(self):
        logging.info(f'Init application parameters values')
        self.macro_excel_file = str(f'{os.getcwd()}\\PY_PERSONAL.XLSB')
        self.path_for_req = ""
        self.path_for_tar = ""

# D:\\TarTool\\Premier\\Auto\\protocol.tar
# C:\\Users\\RotemG\\PycharmProjects\\ProtocolsTool\\Data\\MR30_Premier\\MR30_Premier_Requirements.xlsx