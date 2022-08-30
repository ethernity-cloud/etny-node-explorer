import os, sys, time, pymysql, configparser
try:
    from src.singleton import Singleton
    from services.database import Database
except ImportError:
    from src.singleton import Singleton
    from database import Database

from pymysql.err import IntegrityError as dbException

class MysqlDatabase(Database, metaclass = Singleton):

    def reConnect(self, config = None) -> None:
        self.connect(config=config)

    def connect(self, config = None) -> None:
        super().connect(config = config)
        if not config:
            config = configparser.ConfigParser()
            config.read('config.env')

        try:
            self._conn = pymysql.connect(
                host = config['MYSQL']['DB_HOST_ALIAS'], 
                port = int(config['MYSQL']['DB_PORT']), 
                user = config['MYSQL']['DB_USERNAME'], 
                passwd = config['MYSQL']['DB_PASSWORD'], 
                db = config['MYSQL']['DB_DATABASE'],
                charset = 'utf8', 
                # cursorclass = pymysql.cursors.DictCursor
            )
          
            if self.dict_cursor == True:
                self._conn.cursorclass = pymysql.cursors.DictCursor

            self._curr = self._conn.cursor()     

        except pymysql.err.OperationalError as e:
            print(e)

    def init(self):
        self._curr.execute(f'''CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                id bigint(20) primary key auto_increment, 
                block_identifier bigint(20) default 0,
                insert_date int(11) not null default 0,
                update_date int(11) not null default 0,
                created_on int(11) not null default 0,
                last_updated int(11) not null default 0,
                updates_count int(11) not null default 0
            )''')
        self._curr.execute(f'''create table if not exists {self.TABLE_NAME}_details (
                id bigint(20) primary key auto_increment,
                parent_id bigint(20) not null default 0 comment 'id in {self.TABLE_NAME}',  
                address varchar(70) not null default '', 
                cpu tinyint(3) unsigned not null default 0, 
                memory tinyint(3) unsigned not null default 0, 
                storage tinyint(3) unsigned not null default 0, 
                bandwith tinyint(3) unsigned not null default 0, 
                duration tinyint(3) unsigned not null default 0, 
                status tinyint(3) unsigned not null default 0, 
                cost decimal(10, 2) not null default 0.00,
                FOREIGN KEY (parent_id) REFERENCES {self.TABLE_NAME}(id),
                index parent_id(parent_id)
            )''')

        print('init MySql...')

    def insert(self, node, recursion_call = 0):
        try:
            public = node.public()
            private = node.private()
            self._conn.begin()
            # root
            query = f'''insert into {self.TABLE_NAME} set {self.extract_args({**private})}, insert_date = {int(time.time())}'''
            self._curr.execute(query)
            insert_id = self._curr.lastrowid 
            if not insert_id:
                raise Exception(f'insert id not found - {insert_id}, :', query)
            # child
            sub_query = f'''insert into {self.TABLE_NAME}_details set {self.extract_args({**public, 'parent_id': (insert_id if insert_id and insert_id < 1844674407 else -1)})}'''
            if self.queryLogIsEnabled:
                print(query)
            # print(sub_query)
            self._curr.execute(sub_query)
            self._curr.close()
        except pymysql.err.IntegrityError as e:
            print('-----error while inserting the record: ', str(e),  str(node.block_identifier), str(node.id), os.getpid())
            self._conn.rollback()
            pass
        except (pymysql.err.ProgrammingError, Exception) as e:
            if recursion_call > 10:
                return print('cant retry anymore: ', node.instance())
            time.sleep(1 if type(e) != Exception else 3)
            print('retry....', str(e), node.instance())
            return self.insert(node=node, recursion_call=recursion_call+1)
        else:
            self._conn.commit()
            self._curr = self._conn.cursor()


    def commit(self, recursives_count = 0) -> None:
        try:
            return super().commit()
        except dbException as e:
            print(e)
        except (pymysql.err.OperationalError, pymysql.err.InternalError, pymysql.err.InterfaceError, pymysql.err.ProgrammingError) as e:
            print('-------try again.... ', recursives_count)
            time.sleep(.1)
            if recursives_count < 10:
                return self.commit(recursives_count=recursives_count+1)


    def select_all(self, limit = 1000):
        query = super().select_all(limit)
        self._curr.execute(query)
        result = self._curr.fetchall()
        return (x for x in result)


    def get_concatenated_fields(self):
        return "(select concat(block_identifier, '-', (block_identifier - d.block_identifier)) as id_and_block from orders where block_identifier > d.block_identifier order by block_identifier asc limit 1) as next_id_and_block_identifier"


if __name__ == '__main__':
    Database().dropTable()