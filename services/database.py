from enum import Enum

DB_TYPES = Enum('DB_TYPES', ['MYSQL', 'SQLITE'])

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Database:
    _conn, _curr = None, None
    ENGINE = ''

    def __init__(self, config = None) -> None:
        self.connect(config=config)

    def init(self) -> None:
        print('init ', self.ENGINE)

    def connect(self, config = None):
        pass

    def commit(self) -> None:
        self._conn.commit()

    def __del__(self):
        try:
            self._curr.close()
            self._conn.close()
        except: # pylint: disable=bare-except
            pass

    # - shared methods

    def get_last_dp_request(self, field = 'dpRequestId'):
        self._curr.execute(f'SELECT max({field}) FROM dp_requests')
        return self._curr.fetchone()[0]

    def get_count_of_dp_requests(self):
        self._curr.execute('SELECT count(dpRequestId) FROM dp_requests')
        return self._curr.fetchone()[0]

    def store_dp_requests(self, models):
        keys = models[0].keys
        sql = "INSERT "
        if self.ENGINE == DB_TYPES.SQLITE:
            sql += "or "
        sql += f'''ignore into dp_requests ({",".join(keys)}) values '''
        values = []
        for model in models:
            items = model.items
            v = [f"'{items[x]}'" if type(items[x]) == str else str(items[x]) for x in keys] # pylint: disable=unidiomatic-typecheck, invalid-name
            values.append(f'''( {",".join(v)}  )''')
        sql += ",".join(values)
        self._curr.execute(sql)
        self._conn.commit()

    def get_missing_records_count(self):
        pass

    def get_missing_records(self, last_page = 1, per_page = 10):
        pass

    def generate_unique_requests(self):
        pass

    def get_unique_requests(self):
        self._curr.execute('SELECT * from dp_unique_requests')
        return self._curr.fetchall()

    def get_unique_requests_count(self, interval_hours = 24):
        pass