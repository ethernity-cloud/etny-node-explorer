import os, sqlite3, time
from helpers.singleton import Singleton
from sqlite3 import OperationalError as dbException
from helpers.database import Database

class SqliteDatabase(Database, metaclass = Singleton):

    DB_NAME = 'orders.db' 
    def connect(self):
        self._conn = sqlite3.connect(f'{self.DB_NAME}')
        self._curr = self._conn.cursor()

    def init(self):
        self._conn.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    id int primary key, 
                    order_id int(11) default 0,
                    ins_time int(11) not null default 0
            )''')

    def dropTable(self):
        self._conn.execute(f"drop table if exists {self.TABLE_NAME}")

    def insert(self, _id, order_id):
        try:
            self._curr.execute(f'''
                insert into {self.TABLE_NAME} 
                    (id, order_id, ins_time) values 
                    ({_id}, {order_id}, {int(time.time())})
                ''')
        except sqlite3.IntegrityError as e:
            pass

    def commit(self):
        self._conn.commit()

    def select(self):
        for row in self._curr.execute(f"select * from {self.TABLE_NAME}"):
            print(row)

    def count(self):
        try:
            print([x for x in self._conn.execute(f"select count(*) from {self.TABLE_NAME}")][0][0])
        except:pass


