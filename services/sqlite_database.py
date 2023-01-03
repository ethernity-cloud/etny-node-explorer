from socket import timeout
from datetime import datetime
import sqlite3, configparser
from src.singleton import Singleton
from services.database import Database, time
from sqlite3 import OperationalError as dbException


class SqliteDatabase(Database, metaclass = Singleton):

    def reConnect(self, config = None) -> None:
        self.connect(config=config)

    def connect(self, config = None, has_dict_cursor = False):
        super().connect(config=config)
        if not config:
            config = configparser.ConfigParser()
            config.read('config.env')

        self._conn = sqlite3.connect(config['SQLITE']['DB_DATABASE'], timeout=15)

        if self.dict_cursor == True or has_dict_cursor:
            self._conn.row_factory = sqlite3.Row
        self._curr = self._conn.cursor()
        

    def init(self):
        self._curr.execute(f'''CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                id bigint(20) primary key, 
                block_identifier bigint(20) default 0,
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
                insert_date int(11) not null default 0,
                update_date int(11) not null default 0,
                status tinyint(3) not null default 0, 
                cost decimal(10, 2) not null default 0.00,
                FOREIGN KEY (parent_id) REFERENCES {self.TABLE_NAME}(id)
            )''')

        # self._curr.execute("drop table if exists dp_requests;")
        self._curr.execute(f'''create table if not exists dp_requests (
                id bigint(20) primary key,
                dpRequestId bigint(20) UNIQUE default 0,
                dproc varchar(70) not null default '',
                cpuRequest tinyint(3) not null default 0,
                memoryRequest tinyint(3) not null default 0,
                storageRequest tinyint(3) not null default 0,
                bandwidthRequest tinyint(3) not null default 0,
                duration tinyint(3) not null default 0,
                minPrice tinyint(3) not null default 0,
                `status` tinyint(3) not null default 0,

                createdAt int(11) not null default 0,
                local_created_at int(11) not null default (cast(strftime('%s','now') as int))
            )''')

        self._curr.execute(f'''CREATE INDEX if not exists parent_id ON {self.TABLE_NAME}_details (parent_id);''')
        self._curr.execute(f'''CREATE INDEX if not exists address ON {self.TABLE_NAME}_details (address);''')

        self._curr.execute(f'''CREATE INDEX if not exists dp_requests_dproc_idx ON  dp_requests (dproc);''')
        self._curr.execute(f'''CREATE INDEX if not exists dp_requests_dpRequestId_idx ON  dp_requests (dpRequestId);''')
        self._curr.execute(f'''CREATE INDEX if not exists dp_requests_createdAt_idx ON  dp_requests (createdAt);''')
        print('init Sqlite...')
        self._conn.commit()

    def insert(self, node, recursion_count = 0):
        try:
            public = node.public()
            private = node.private()
            # root
            query = f'''insert into {self.TABLE_NAME} ({",".join(private.keys())}) values ({",".join([f"'{x}'" if type(x) == str else f'{x}' for x in [*private.values()]])})'''
            
            self._curr.execute(query)
            insert_id = self._curr.lastrowid
            if not insert_id:
                raise Exception('insert id not found...')
            # child
            if self.queryLogIsEnabled:
                print(query)
            sub_query = f'''insert into {self.TABLE_NAME}_details ({",".join(public.keys())}, parent_id, insert_date) 
                            values 
                        (  {",".join([f"'{x}'" if type(x) == str else f'{x}' for x in [*public.values()]])}, {insert_id}, {int(time.time())} )'''
            return self._curr.execute(sub_query)
        except sqlite3.IntegrityError as e:
            pass
        except (self._conn.Error, Exception) as e:
            if self.logger:
                self.logger.error(f'error = {e}')
            time.sleep(1)
            if recursion_count < 10:
                self.connect()
                return self.insert(node=node, recursion_count=recursion_count+1)
        finally:
            self._conn.commit()

    def select(self):
        for row in self._curr.execute(f"select * from {self.TABLE_NAME}"):
            print(row)

    def commit(self) -> None:
        try:
            return super().commit()
        except dbException as e:
            if self.logger:
                self.logger.error(f'db_error: {e}')
            time.sleep(2)
            self.connect()
            return self.commit()

    def select_all(self, limit = 1000):
        query = super().select_all(limit=limit)
        self._curr.execute(query)
        result = self._curr.fetchall()
        return self.generator_dict_from_result(result)

    def generator_dict_from_result(self, result):
        return ({'_id': result[i]['id'], **dict(zip(row.keys(), row))} for i, row in enumerate(result))
        
    def get_concatenated_fields(self):
        return "(select block_identifier || '-' || (block_identifier - d.block_identifier) as id_and_block from orders where block_identifier > d.block_identifier order by block_identifier asc limit 1) as next_id_and_block_identifier"

    # new
    def storeDPRequests(self, models):
        keys = models[0].keys
        sql = f'''INSERT or ignore into dp_requests ({",".join(keys)}) values '''
        values = []
        for model in models:
            items = model.items
            v = [f"'{items[x]}'" if type(items[x]) == str else str(items[x]) for x in keys]
            values.append(f'''( {",".join(v)}  )''')
        sql += ",".join(values)
        self._curr.execute(sql)
        self._conn.commit()