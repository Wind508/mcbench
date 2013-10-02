import os

REDIS_URL = os.environ.get('REDISCLOUD_URL', 'redis://localhost:6379')
