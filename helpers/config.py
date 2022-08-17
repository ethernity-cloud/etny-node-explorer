
import configparser
from enum import Enum


config = configparser.ConfigParser()
config.read('config.env')

BASE_LOOP_ITER = 1000 

class bcolors(Enum):
    MESSAGE = '\033[94m'
    INFO = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    _END = '\033[0m'