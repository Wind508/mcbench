import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(root, 'mcbench.sqlite')
DATA_ROOT = os.path.expanduser('~/mcbench-benchmarks')
SECRET_KEY = ''

try:
    from local_settings import *
except ImportError:
    pass
