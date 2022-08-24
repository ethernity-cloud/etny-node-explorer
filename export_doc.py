from datetime import datetime
import csv, os
from node import Node 
from config import Database, dbException

class CSVFileGenerator:

    def __init__(self):

        fileName = f'''documents/orders-{datetime.now().strftime('%d-%m-%Y_%H-%M')}.csv'''
        self._nodesFile = os.path.join(os.getcwd(), fileName)

        Database().connect(has_dict_cursor = True)
        query = Database().select_all(limit = 0)
        with open(self._nodesFile, 'w', newline='') as output_file:
            writer = csv.writer(output_file, dialect="excel-tab")
            writer.writerow(Node.all_fields)
            _iter = 0
            for item in query:
                node = Node(**item)
                if item.get('_id') and item['_id']:
                    node.id = item.get('_id')
                writer.writerow([node.getAttr(x) for x in node.all_fields])
                _iter += 1
            print(f'''\n\nThe file "{fileName}" with {_iter} records was created. ''')



if __name__ == '__main__':
    CSVFileGenerator()


