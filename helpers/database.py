

class Database:
    TABLE_NAME = 'orders'
    _conn, _curr = None, None

    def __init__(self) -> None:
        self.connect()

    def connect(self) -> None:
        pass

    def __del__(self):
        try:
            self._curr.close()
            self._conn.close()
        except:pass