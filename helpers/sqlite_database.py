import os, sqlite3
from helpers.singleton import Singleton
from helpers.database import Database, time
from sqlite3 import OperationalError as dbException

class SqliteDatabase(Database, metaclass = Singleton):

    DB_NAME = 'orders.db' 

    def connect(self):
        super().connect()
        self._conn = sqlite3.connect(f'{self.DB_NAME}')
        self._curr = self._conn.cursor()

    def init(self):
        self._curr.execute(f'''CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                id bigint(20) primary key, 
                order_id bigint(20) default 0,
                created_on int(11) not null default 0,
                last_updated int(11) not null default 0,
                updates_count int(11) not null default 0
            )''')
        self._curr.execute(f'''create table if not exists {self.TABLE_NAME}_details (
                id bigint(20) primary key,
                parent_id bigint(20) not null default 0,  
                address varchar(70) not null default '', 
                cpu tinyint(3) not null default 0, 
                memory tinyint(3) not null default 0, 
                storage tinyint(3) not null default 0, 
                bandwith tinyint(3) not null default 0, 
                duration tinyint(3) not null default 0, 
                status tinyint(3) not null default 0, 
                cost decimal(10, 2) not null default 0.00,
                FOREIGN KEY (parent_id) REFERENCES {self.TABLE_NAME}(id)
            )''')
        self._curr.execute(f'''CREATE INDEX if not exists parent_id ON {self.TABLE_NAME}_details (parent_id);''')
        print('init Sqlite...')
        self._conn.commit()

    def insert(self, node):
        try:
            public = node.public()
            private = node.private()
            # root
            query = f'''insert into {self.TABLE_NAME} ({",".join(private.keys())}, created_on) 
                            values 
                        ({",".join([f"'{x}'" if type(x) == str else f'{x}' for x in [*private.values()]])}, {int(time.time())})'''
            
            self._curr.execute(query)
            insert_id = self._curr.lastrowid
            print('-------insert id = ', insert_id)
            # child
            query = f'''insert into {self.TABLE_NAME}_details ({",".join(public.keys())}, parent_id) 
                            values 
                        (  {",".join([f"'{x}'" if type(x) == str else f'{x}' for x in [*public.values()]])}, {insert_id} )'''
            return self._curr.execute(query)
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

    


