import csv
import os
from datetime import datetime
from models.dp_unique_request_model import DPUniqueRequestModel
from libs.db import DB

class CSVFileGenerator:

    def __init__(self):

        fileName = f'''documents/orders-{datetime.now().strftime('%d-%m-%Y_%H-%M')}.csv'''
        self._nodesFile = os.path.join(os.getcwd(), fileName)
        if not os.path.exists(os.path.join(os.getcwd(), 'documents')):
            os.mkdir(os.path.join(os.getcwd(), 'documents'))
        DB().connect()
        DB().generate_unique_requests()
        with open(self._nodesFile, 'w', newline='') as output_file: # pylint: disable=unspecified-encoding
            writer = csv.writer(output_file, dialect="excel-tab")
            writer.writerow(DPUniqueRequestModel.fields)
            _iter = 0
            data = map(DPUniqueRequestModel, DB().get_unique_requests()[:10])
            for node in data:
                writer.writerow([node.getAttr(x) for x in node.fields])
                _iter += 1
            print(f'''\n\nThe file "{fileName}" with {_iter} records was created. ''')



if __name__ == '__main__':
    CSVFileGenerator()


