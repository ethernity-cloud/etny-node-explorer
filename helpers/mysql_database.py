import os, sys, time, pymysql, configparser
try:
    from helpers.singleton import Singleton
    from helpers.database import Database
except ImportError:
    from singleton import Singleton
    from database import Database

from pymysql.err import IntegrityError as dbException

class MysqlDatabase(Database, metaclass = Singleton):

    def connect(self) -> None:
        super().connect()
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
            self._curr = self._conn.cursor()     

        except pymysql.err.OperationalError as e:
            print(e)

    def init(self):
        self._curr.execute(f'''CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                id bigint(20) primary key auto_increment, 
                order_id bigint(20) default 0,
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

    def insert(self, node):
        try:
            return super().insert(node)
        except pymysql.err.IntegrityError as e:
            pass
        except pymysql.err.ProgrammingError as e:
            time.sleep(1)
            return super().insert(node)

    def commit(self, recursives_count = 0) -> None:
        try:
            return super().commit()
        except dbException as e:
            print(e)
        except (pymysql.err.OperationalError, pymysql.err.InternalError, pymysql.err.InterfaceError) as e:
            print('-------try again.... ', recursives_count)
            time.sleep(.1)
            if recursives_count < 10:
                return self.commit(recursives_count=recursives_count+1)


if __name__ == '__main__':
    Database().dropTable()