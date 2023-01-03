
import time

 
class dbException(Exception):
    pass

class Database:
    TABLE_NAME = 'orders'
    _conn, _curr, logger = None, None, None
    queryLogIsEnabled = False

    dict_cursor = False
    def __init__(self, dict_cursor = False, config = None, logger = None) -> None:
        self.dict_cursor = dict_cursor
        self.logger = logger
        self.connect(config=config)

    def reConnect(self, config = None) -> None:
        pass

    def connect(self, config = None) -> None:
        try:
            self.queryLogIsEnabled = config['DATABASE']['queryLogIsEnabled'] in ['True', '1']
        except (ValueError, TypeError) as e:
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
        pass

    def update(self, node):
        public = node.public()
        private = node.private()
        query = f'''update {self.TABLE_NAME} set  {self.extract_args({x: y for x, y in private.items() if x not in ['id']})}, updates_count = updates_count + 1 where id = {node.id}'''
        if self.queryLogIsEnabled:
            print(query)
        sub_query = f'''update {self.TABLE_NAME}_details set 
                            {self.extract_args({**public})}, update_date = {int(time.time())}
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


    def raw_select(self, query):
        self._curr.execute(query)
        result = self._curr.fetchall()
        return (x for x in result) # generator

    def number_of_missing_items(self):
        query = f'''
            select 
                count(d.id)
            from {self.TABLE_NAME} d 
            where id > -1 and not exists (select id from {self.TABLE_NAME} where id = d.id + 1) and d.id < (select max(id) from {self.TABLE_NAME});
        '''
        query = self._curr.execute(query)
        return self._curr.fetchone()


    def select_all(self, limit = 1000):
        query = f'''
            select 
                o1.id,
                o1.block_identifier,
                d.address,
                d.cpu,
                d.memory,
                d.storage,
                d.bandwith,
                d.duration,
                d.status,
                d.cost,
                o1.created_on,
                -- (select created_on from {self.TABLE_NAME} where id = d.parent_id order by (case when last_updated then last_updated else created_on end) desc) as last_updated,
                -- max(d.insert_date) as last_updated,
                max((case when o1.last_updated then o1.last_updated else o1.created_on end)) as last_updated,
                count(o2.address) as updates_count
            from {self.TABLE_NAME}_details d 
            join (select * from {self.TABLE_NAME} order by created_on asc) o1 on o1.id = d.parent_id
            join (select * from {self.TABLE_NAME}_details order by id desc) o2 on o2.parent_id = d.parent_id
            group by d.address order by d.id;
        '''

        if limit: query += f" limit {limit}"
        return query


    def count_of_left_nodes(self):
        self._curr.execute(f'''
            select 
                count(d.id) as id
            from orders d 
            where id > -1 and not exists (select id from orders where id = d.id + 1) and d.id < (select max(id) from orders);
        ''')
        return self._curr.fetchone()

    def extract_args(self, items):
        return ",".join([f"{x} = {y}" if type(y) != str else f"{x} = '{y}'" for x, y in items.items()])

    def __del__(self):
        try:
            self._curr.close()
            self._conn.close()
        except:pass

    # new methods
    def getLastDPRequest(self):
        self._curr.execute('SELECT max(dpRequestId) AS lst FROM dp_requests')
        return self._curr.fetchone()[0]

    