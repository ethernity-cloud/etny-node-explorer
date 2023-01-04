import os
import sys
# pylint: disable=wrong-import-position, import-error
sys.path.extend([os.getcwd().split('/run')[0]])
from config import Database, DB_TYPES

class DB(Database):
    """db class"""
        
    def get_last_dp_request(self):
        """get_last_dp_request"""
        self._curr.execute('SELECT max(dpRequestId) AS lst FROM dp_requests')
        return self._curr.fetchone()[0]

    def store_dp_requests(self, models):
        """store_dp_requests"""
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

    def get_missing_records(self, last_page = 1, per_page = 10):
        """get missing records"""
        self._curr.execute(f'select get_missing_records({last_page}, {per_page})')
        return self._curr.fetchone()[0]
        