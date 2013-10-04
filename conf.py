import os

REDIS_URL = os.environ.get('REDISCLOUD_URL', 'redis://localhost:6379')
DATA_ROOT = '/Users/isbadawi/code/py/matlab-file-exchange-scraper/downloads/successfully_parsed'

SECRET_KEY = os.environ['SECRET_KEY']
