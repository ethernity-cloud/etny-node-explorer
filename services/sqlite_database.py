import sqlite3, configparser
try:
    from services.database import Singleton, Database, DB_TYPES
except ImportError:
    from database import Singleton, Database, DB_TYPES


class SqliteDatabase(Database, metaclass = Singleton):

    def connect(self, config = None):
        super().connect(config=config)
        if not config:
            config = configparser.ConfigParser()
            config.read('config.env')

        self._conn = sqlite3.connect(config['SQLITE']['DB_DATABASE'], timeout=15)
        self._curr = self._conn.cursor()
        
    def init(self, *args, **kwargs):
        Database.init(self, *args, **kwargs)
        
        self._curr.execute('''create table if not exists dp_requests (
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

        self._curr.execute('''create table if not exists dp_unique_requests (
            id bigint(20) not null default 0,
            dpRequestId bigint(20) UNIQUE default 0,
            dproc varchar(70) unique not null default '',
            cpuRequest tinyint not null default 0,
            memoryRequest tinyint not null default 0,
            storageRequest tinyint not null default 0,
            bandwidthRequest tinyint not null default 0,
            duration tinyint not null default 0,
            minPrice tinyint not null default 0,
            `status` tinyint not null default 0,
            createdAt int(11) not null default 0,
            local_created_at int(11) not null default (cast(strftime('%s','now') as int)),
            updated_at int(11) not null default 0,
            nodes_count mediumint default 0
        )''')

        self._curr.execute('''CREATE INDEX if not exists dp_requests_dproc_idx ON  dp_requests (dproc);''')
        self._curr.execute('''CREATE INDEX if not exists dp_requests_dpRequestId_idx ON  dp_requests (dpRequestId);''')
        self._curr.execute('''CREATE INDEX if not exists dp_requests_createdAt_idx ON  dp_requests (createdAt);''')

        self._curr.execute('''CREATE INDEX if not exists dp_unique_requests_dproc_idx ON  dp_unique_requests (dproc);''')
        self._curr.execute('''CREATE INDEX if not exists dp_unique_requests_dpRequestId_idx ON  dp_unique_requests (dpRequestId);''')
        self._curr.execute('''CREATE INDEX if not exists dp_unique_requests_createdAt_idx ON  dp_unique_requests (createdAt);''')
        self._curr.execute('''CREATE INDEX if not exists dp_unique_requests_updated_at_idx ON  dp_unique_requests (updated_at);''')
        
        self._conn.commit()

    def get_missing_records_count(self):
        self._curr.execute('select max(id) - count(id) from dp_requests')
        result = self._curr.fetchone()
        return result[0] if result else 0

    def __get_dp_request_by_id(self, _id):
        self._curr.execute(f'SELECT id FROM dp_requests where id = {_id}')
        result = self._curr.fetchone()
        return result[0] if result else 0

    def get_missing_records(self, last_page = 1, per_page = 10):
        _max = self.get_last_dp_request(field='id')
        _str = ''
        inline_query = 0
        fount_items = 0
        current_iter = last_page + 2 if last_page > 1 else last_page
        while current_iter < _max and fount_items < per_page:
            inline_query = self.__get_dp_request_by_id(_id = current_iter)
            if not inline_query:
                _str += f'{current_iter - 1},'
                fount_items += 1
            current_iter += 1
        return f'{fount_items}-{current_iter}-{_max}-{_str}'

    def generate_unique_requests(self):
        sql = '''
            insert or replace into dp_unique_requests 
                ( id, dpRequestId, dproc, cpuRequest, memoryRequest, storageRequest, bandwidthRequest, duration, minPrice, `status`, createdAt, local_created_at, updated_at, nodes_count ) 
                select max(id) as id, max(dpRequestId) as dpRequestId, dproc, cpuRequest, memoryRequest, storageRequest, bandwidthRequest, duration, minPrice, max(`status`) as `status`, createdAt, local_created_at, max(createdAt) as updated_at, count(id) as nodes_count
            from dp_requests group by dproc
        '''
        self._curr.execute(sql)
        self._conn.commit()

    def get_unique_requests_count(self):
        super().get_count_of_dp_requests()

        query = f'''select count(distinct dproc) from dp_requests where date(createdAt, 'unixepoch', '-1 day') = date('now', '-1 day') '''
        return self.fetch_one(query)