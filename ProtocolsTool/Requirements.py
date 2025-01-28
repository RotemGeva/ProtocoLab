import logging
import os
import sys
import utils
import openpyxl
import win32com


def resource_path(relative_path):
    # """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class Requirements:
    def __init__(self, parameters):
        logging.info(f'***** Make Requirement *****')
        try:
            self.parameters = parameters
            siemens_sw_type = utils.read_mr_sw_type()
            utils.handle_protocol_extractor(self.parameters.mr_name, self.parameters.mr_vendor,
                                            siemens_sw_type, is_comparing=False)
            self.excel_rearrangement()
            logging.info(f'***** Make Requirement Done *****')
        except Exception as err:
            logging.error(f'Error during making requirements process: {err}.')
            sys.exit(1)

    def excel_rearrangement(self):
        logging.info(f'Working on {self.parameters.mr_name}_Requirements.xlsx...')
        try:
            logging.info(f'Opening {self.parameters.mr_name}_Requirements.xlsx using Python...')
            requirement_file = openpyxl.load_workbook(
                f'{os.getcwd()}\\Data\\Requirements\\{self.parameters.mr_name}_Requirements.xlsx')
        except Exception as err:
            logging.info(f'Failed to open {self.parameters.mr_name}_Requirements.xlsx.\nError: {err}')
            raise Exception(f'Failed to open {self.parameters.mr_name}_Requirements.xlsx.\nError: {err}')
        # Got a list of all sheets in the file and drove it into a variable
        sheets = requirement_file.sheetnames
        logging.info(f'Retrieved the following sheets names: {sheets}.')
        # Deleting first sheet
        logging.info(
            f'Removing 1st sheet from {self.parameters.mr_name}_Requirements.xlsx...')
        requirement_file.remove(requirement_file[f'{sheets[0]}'])

        # Deleting unwanted sheets
        try:
            logging.info(f'The following sheets are found in file: {requirement_file.sheetnames}')
            for sheet in requirement_file.sheetnames:
                logging.info(f'Checking if sheet {sheet} was selected...')
                if sheet not in self.parameters.protocols:
                    logging.info(f'{sheet} was not found in {self.parameters.protocols}. Deleting: {sheet}...')
                    del requirement_file[sheet]
                    logging.info('Deleted sheet.')
        except Exception as err:
            logging.info(f'Failed to delete the following sheet: {sheet}. {err}')
            raise Exception(f'Failed to delete the following sheet: {sheet}. {err}')

        # Saved file with changes (deleted page)
        requirement_file.save(f'{os.getcwd()}\\Data\\Requirements\\{self.parameters.mr_name}_Requirements.xlsx')
        logging.info(f'Sheet removed and file {self.parameters.mr_name}_Requirements.xlsx saved')

        # macros
        try:
            logging.info('Opening Excel...')
            excel = win32com.client.dynamic.Dispatch('Excel.Application')
            logging.info('Excel opened successfully.')
        except Exception as err:
            logging.info(f'Failed to open Excel software.\nError: {err}')
            raise Exception(f'Failed to open Excel software.\nError: {err}')
        # open macro excel file, macros will run from it
        try:
            logging.info(f'Opening macro excel file using Python, file: {self.parameters.macro_excel_file}...')
            excel.workbooks.Open(Filename=resource_path(f"{self.parameters.macro_excel_file}"))
            logging.info('Opened file successfully.')
        except Exception as err:
            logging.info(f'Failed to open macro excel file: {self.parameters.macro_excel_file}.\nError: {err}')
            raise Exception(f'Failed to open macro excel file: {self.parameters.macro_excel_file}.\nError: {err}')
        # open the file to run macros on
        try:
            logging.info(f'Opening {self.parameters.mr_name}_Requirements.xlsx for macros...')
            requirement_file = excel.workbooks.Open(
                Filename=f"{os.getcwd()}\\Data\\Requirements\\{self.parameters.mr_name}_Requirements.xlsx")
        except Exception as err:
            logging.info(f'Failed to open excel file: {self.parameters.mr_name}_Requirements.xlsx.\nError: {err}')
            raise Exception(f'Failed to open macro excel file: {self.parameters.mr_name}_Requirements.xlsx.\nError: {err}')
        # run macro
        try:
            logging.info(f'Running macro: MakeReqDocForAllSheets...')
            excel.Run(f"'{self.parameters.macro_excel_file}'!MakeReqDocForAllSheets")
            logging.info(f'Running macro MakeReqDocForAllSheets ended successfully.')
        except Exception as err:
            logging.info(f'Failed to run macro: MakeReqDocForAllSheets.\nError: {err}')
            raise Exception(f'Failed to run macro: MakeReqDocForAllSheets.\nError: {err}')
        try:
            logging.info(f'Running macro: EqualCellSizeForAllSheets...')
            excel.Run(f"'{self.parameters.macro_excel_file}'!EqualCellSizeForAllSheets")
            logging.info(f'Running macro EqualCellSizeForAllSheets ended successfully.')
        except Exception as err:
            logging.info(f'Failed to run macro: EqualCellSizeForAllSheets.\nError: {err}')
            raise Exception(f'Failed to run macro: EqualCellSizeForAllSheets.\nError: {err}')
        try:
            logging.info(f'Running macro: CenterForAllSheets...')
            excel.Run(f"'{self.parameters.macro_excel_file}'!CenterForAllSheets")
            logging.info(f'Ran macro: CenterForAllSheets')
            logging.info(f'Running macro CenterForAllSheets ended successfully.')
        except Exception as err:
            logging.info(f'Failed to run macro: CenterForAllSheets.\nError: {err}')
            raise Exception(f'Failed to run macro: CenterForAllSheets.\nError: {err}')

        # save the file after macros
        try:
            requirement_file.Close(SaveChanges=1)
            logging.info(f'{self.parameters.mr_name}_Requirements.xlsx saved. Quitting Excel...')
            excel.Quit()
        except Exception as err:
            logging.info(f'Failed to save {self.parameters.mr_name}_Requirements.xlsx.\nError: {err}')
            raise Exception(f'Failed to save {self.parameters.mr_name}_Requirements.xlsx.\nError: {err}')
