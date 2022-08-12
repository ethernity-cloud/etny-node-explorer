
import time

class dbException(Exception):
    pass

class Database:
    TABLE_NAME = 'orders'
    _conn, _curr = None, None

    def __init__(self) -> None:
        self.connect()

    def connect(self) -> None:
        pass

    def init(self) -> None:
        pass

    def commit(self) -> None:
        self._conn.commit()

    def dropTable(self):
        self._curr.execute(f"drop table if exists {self.TABLE_NAME}")


    def insert(self, _id, order_id, ) -> None:
        self._curr.execute(f'''
            insert into {self.TABLE_NAME} 
                (id, order_id, ins_time) values 
                ({_id}, {order_id}, {int(time.time())})
            ''')

    def count(self):
        try:
            self._curr.execute(f"select count(*) from {self.TABLE_NAME}")
            print(self._curr.fetchone()[0])
        except Exception as e:
            print(e)

    def __del__(self):
        try:
            self._curr.close()
            self._conn.close()
        except:pass