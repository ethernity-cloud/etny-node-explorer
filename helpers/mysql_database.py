import os, sys, pymysql, configparser
from helpers.singleton import Singleton
from helpers.database import Database
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
        self._curr.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                id bigint(20) primary key auto_increment, 
                order_id bigint(20) default 0,
                ins_time int(11) not null default 0
            )''')

    def insert(self, _id, order_id):
        try:
            super().insert(_id = _id, order_id=order_id)
        except pymysql.err.IntegrityError as e:
            pass

    def commit(self) -> None:
        try:
            return super().commit()
        except dbException as e:
            print(e)


