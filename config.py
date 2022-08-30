
import configparser, os
import logging.handlers
from src.custom_formatter import CustomFormatter
from datetime import datetime
from multiprocessing import cpu_count

config = configparser.ConfigParser()
config.read('config.env')

from src.exceptions import DatabaseEngineNotFoundError
try:
    if config['DATABASE']['engine'] != 'MYSQL':
        raise DatabaseEngineNotFoundError('For DB Engine is used Sqlite')
    from services.mysql_database import MysqlDatabase as Database, dbException
except (ImportError, DatabaseEngineNotFoundError) as e:
    from services.sqlite_database import SqliteDatabase as Database, dbException




BASE_LOOP_ITER = 1000 
LIMIT_OF_THREADS = 32 # int(cpu_count() * 8)
FREE_MEMORY_IN_INTERVAL = True


def getLogger():
    logger = logging.getLogger("ETNY NODE")
    handler = logging.handlers.RotatingFileHandler(os.path.join(os.getcwd(), f"output_{datetime.now().strftime('%d-%m-%Y')}.log"), maxBytes=20480000, backupCount=5)
    fmt = '%(asctime)s %(message)s'
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    # handler.setFormatter(CustomFormatter(fmt))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger