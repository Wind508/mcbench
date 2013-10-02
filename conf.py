import os

SECRET_KEY = os.environ['SECRET_KEY']
REDIS_URL = os.environ.get('REDISCLOUD_URL', 'redis://localhost:6379')
