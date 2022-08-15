import os, sqlite3
from helpers.singleton import Singleton
from helpers.database import Database
from sqlite3 import OperationalError as dbException

class SqliteDatabase(Database, metaclass = Singleton):

    DB_NAME = 'orders.db' 

    def connect(self):
        super().connect()
        self._conn = sqlite3.connect(f'{self.DB_NAME}')
        self._curr = self._conn.cursor()

    def init(self):
        self._conn.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    id int(11) primary key, 
                    order_id BIGINT(11) default 0,
                    ins_time int(11) not null default 0
            )''')
        self._conn.commit()

    def insert(self, _id, order_id):
        try:
            super().insert(_id = _id, order_id=order_id)
        except sqlite3.IntegrityError as e:
            pass

    def select(self):
        for row in self._curr.execute(f"select * from {self.TABLE_NAME}"):
            print(row)

    def commit(self) -> None:
        try:
            return super().commit()
        except dbException as e:
            print(e)

    


