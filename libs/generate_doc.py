import csv
import os
from datetime import datetime
from models.dp_unique_request_model import DPUniqueRequestModel
from config import Database
class CSVFileGenerator:

    def __init__(self):

        fileName = f'''documents/orders-{datetime.now().strftime('%d-%m-%Y_%H-%M')}.csv'''
        self._nodesFile = os.path.join(os.getcwd(), fileName)
        if not os.path.exists(os.path.join(os.getcwd(), 'documents')):
            os.mkdir(os.path.join(os.getcwd(), 'documents'))
        Database().connect()
        Database().generate_unique_requests()
        _iter = 0
        with open(self._nodesFile, 'w', newline='') as output_file: # pylint: disable=unspecified-encoding
            writer = csv.writer(output_file, dialect="excel-tab")
            writer.writerow(DPUniqueRequestModel.fields)
            data = map(DPUniqueRequestModel, Database().get_unique_requests())
            for node in data:
                writer.writerow([node.getAttr(x) for x in node.fields])
                _iter += 1
            print(f'''\n\nThe file "{fileName}" was created. ''')
        last_nodes_count = Database().get_unique_requests_count()
        print('-' * 10)
        print(f"total nodes number: {_iter}, active nodes: {last_nodes_count}")

if __name__ == '__main__':
    CSVFileGenerator()


