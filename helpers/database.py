
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
        query = f'''insert into {self.TABLE_NAME} 
                        (id, order_id, ins_time) values 
                    ({_id}, {order_id}, {int(time.time())})'''
        self._curr.execute(query)

    def update(self, *args, **kwargs):
        fields = self.extract_args(kwargs['fields'])
        where = self.extract_args(kwargs['where'])
        query = f'''
            update {self.TABLE_NAME}
                set {fields}
                where {where}
        '''
        self._curr.execute(query)
        return self    

    def __getattr__(self, methodName):
        def wrapper(*args, **kwargs):
            if methodName in ['select_one', 'select_all', 'count']:
                is_single = 'single' in kwargs.keys()
                if is_single:
                    fields = kwargs['single']
                else:
                    fields = "count(*)" if methodName == 'count' else "*"

                query = f'''select {fields} from {self.TABLE_NAME}'''
                if [key for key in kwargs.keys() if key not in ['single']]:
                    arguments = [f"{x} = {y}" for x, y in kwargs.items() if x not in ['single']]
                    query += f''' where {(" and ".join(arguments))}'''

                print(query)
                self._curr.execute(query)
                if methodName in ['select_all']:             
                    result = self._curr.fetchall()
                    if is_single:
                        return (x[0] for x in result) # generator
                    return (x for x in result) # generator
                result = self._curr.fetchone()
                return [] if not result else (result[0] if is_single and result and ',' not in kwargs['single'] else [x for x in result if x])
        return wrapper


    def extract_args(self, items):
        return ",".join([f"{x} = {y}" if type(y) != str else f"{x} = '{y}'" for x, y in items.items()])

    def __del__(self):
        try:
            self._curr.close()
            self._conn.close()
        except:pass