import os

DB_PATH = 'mcbench.sqlite'
DATA_ROOT = os.path.expanduser('~/mcbench-benchmarks')
SECRET_KEY = ''

try:
    from local_settings import *
except ImportError:
    pass
