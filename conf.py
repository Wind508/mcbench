import argparse
import os


def parse_args():
    parser = argparse.ArgumentParser(
        description='run xpath queries on Matlab ASTs')
    parser.add_argument(
        '--redis_url', type=str,
        help='URL of redis instance.')
    return parser.parse_args()

args = parse_args()
REDIS_URL = args.redis_url or os.environ['REDISCLOUD_URL']
