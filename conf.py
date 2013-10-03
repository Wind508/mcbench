import os

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_S3_BUCKET = 'mclab.mcbench'

REDIS_URL = os.environ.get('REDISCLOUD_URL', 'redis://localhost:6379')

SECRET_KEY = os.environ['SECRET_KEY']
