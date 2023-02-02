import pymysql, configparser, sys
try:
    from services.database import Singleton, Database, DB_TYPES
except ImportError:
    from database import Singleton, Database, DB_TYPES

class MysqlDatabase(Database, metaclass = Singleton):

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
                charset = 'utf8'
            )

            self._curr = self._conn.cursor()     

        except pymysql.err.OperationalError:
            print('Please Call: "sudo ./create_mysql_database.sh" first ')
            sys.exit()


    def get_missing_records_count(self):
        return self.fetch_one('select get_missing_records_count()')

    def get_missing_records(self, last_page = 1, per_page = 10):
        return self.fetch_one(f'select get_missing_records({last_page}, {per_page})')

    def generate_unique_requests(self): 
        self._curr.execute('call group_by_dp_requests()')
        self._conn.commit()

    def get_yesterday(self):
        return self.fetch_one("select get_yesterday_timestamp()")

    def get_unique_requests_count(self):
        super().get_count_of_dp_requests()
        return self.fetch_one(f"select count(distinct dproc) from dp_requests where date(from_unixtime(createdAt)) = ( current_date - interval 1 day )")