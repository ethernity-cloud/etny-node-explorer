
import configparser

config = configparser.ConfigParser()
config.read('config.env')

BASE_LOOP_ITER = 1000 