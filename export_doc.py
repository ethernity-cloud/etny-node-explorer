import csv
from node import Node

import helpers.config as config  
from helpers.exceptions import NotFoundException, DatabaseEngineNotFoundError, BreackFromLoopException

try:
    if config.config['DATABASE']['engine'] != 'MYSQL':
        raise DatabaseEngineNotFoundError('For DB Engine is used Sqlite')
    from helpers.mysql_database import MysqlDatabase as Database, dbException
except (ImportError, DatabaseEngineNotFoundError) as e:
    from helpers.sqlite_database import SqliteDatabase as Database, dbException



class Writer:
    def __init__(self) -> None:
        self._nodesFile = config.config['DEFAULT']['CSVFile']
        self.init()

    def init(self):

        Database(dict_cursor=True).init()

        query = Database().select_all()
        with open(self._nodesFile, 'w',newline='') as output_file:
            writer = csv.writer(output_file, dialect="excel-tab")
            writer.writerow(Node.all_fields)
            for item in query:
                node = Node(**item)
                writer.writerow([getattr(node, x) for x in node.all_fields])



if __name__ == '__main__':
    Writer()


