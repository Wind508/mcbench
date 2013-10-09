import os

REDIS_URL = 'redis://localhost:6379'
DATA_ROOT = os.path.expanduser('~/mcbench-benchmarks')
SECRET_KEY = ''

try:
    from local_settings import *
except ImportError:
    pass
