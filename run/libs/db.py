import os
import sys
sys.path.extend([os.getcwd().split('/run')[0]])
from config import Database, DB_TYPES

class DB(Database):
        
    def get_last_dp_request(self):
        self._curr.execute('SELECT max(dpRequestId) AS lst FROM dp_requests')
        return self._curr.fetchone()[0]

    def get_count_of_dp_requests(self):
        self._curr.execute('SELECT count(dpRequestId) AS lst FROM dp_requests')
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
        self._curr.execute('select get_missing_records_count()')
        return self._curr.fetchone()[0]

    def generate_unique_requests(self):
        self._curr.execute('call group_by_dp_requests()')
        self._conn.commit()

    def get_unique_requests(self):
        self._curr.execute('SELECT * from dp_unique_requests')
        return self._curr.fetchall()
        

        