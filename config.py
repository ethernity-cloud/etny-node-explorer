
import configparser, os, sys

config = configparser.ConfigParser()
try:
    config.read('config.env')
except ImportError:
    config.read(os.path.join(os.getcwd(), 'config.env'))

from libs.exceptions import DatabaseEngineNotFoundError

try:
    if config['DATABASE']['engine'] != 'MYSQL':
        raise DatabaseEngineNotFoundError('For DB Engine is used Sqlite')
    from services.mysql_database import MysqlDatabase as Database, DB_TYPES, Singleton, IS_WINDOWS
    Database.ENGINE = DB_TYPES.MYSQL
except (ImportError, DatabaseEngineNotFoundError) as ex:
    from services.sqlite_database import SqliteDatabase as Database, DB_TYPES, Singleton, IS_WINDOWS
    Database.ENGINE = DB_TYPES.SQLITE
    print(Database.ENGINE)

