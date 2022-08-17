
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
        try:
            self._curr.execute("set foreign_key_checks = 0;")
        except:pass
        self._curr.execute(f"drop table if exists {self.TABLE_NAME}")
        self._curr.execute(f"drop table if exists {self.TABLE_NAME}_details")


    def insert(self, node = None) -> None:
        public = node.public()
        private = node.private()
        # root
        with self._curr:
            query = f'''insert into {self.TABLE_NAME} set {self.extract_args({**private, 'created_on': int(time.time())})}'''
            self._curr.execute(query)
            insert_id = self._curr.lastrowid
            # child
            sub_query = f'''insert into {self.TABLE_NAME}_details set {self.extract_args({**public, 'parent_id': insert_id})}'''
            print(query)
            print(sub_query)
            self._curr.execute(sub_query)

    def update(self, node):
        public = node.public()
        private = node.private()
        query = f'''update {self.TABLE_NAME} set 
                        {self.extract_args({x: y for x, y in private.items() if x not in ['id']})}, last_updated = {int(time.time())}, updates_count = updates_count + 1
                    where id = {node.id}'''
        sub_query = f'''update {self.TABLE_NAME}_details set 
                            {self.extract_args({**public})}
                        where parent_id = {node.id}'''
        self._curr.execute(query)
        self._curr.execute(sub_query)
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

                # print(query)
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