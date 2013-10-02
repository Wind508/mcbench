import collections

import redis

BENCHMARK_FIELDS = [
    'author', 'author_url', 'date_submitted', 'date_updated',
    'name', 'summary', 'tags', 'title', 'url'
]

Benchmark = collections.namedtuple('Benchmark', ' '.join(BENCHMARK_FIELDS))


class McBenchClient(object):
    def __init__(self, redis):
        self.redis = redis

    def get_benchmark_by_id(self, benchmark_id):
        return Benchmark(**self.redis.hgetall('benchmark:%s' % benchmark_id))

    def get_benchmark_by_name(self, name):
        benchmark_id = self.redis.get('benchmark:%s:id', name)
        return self.get_benchmark_by_id(benchmark_id)

    def insert_benchmark(self, benchmark):
        benchmark_id = self.redis.incr('global:next_benchmark_id')
        self.redis.set('benchmark:%s:id' % benchmark.name, benchmark_id)
        self.redis.hmset('benchmark:%s' % benchmark_id, benchmark._asdict())


def from_redis_url(redis_url):
    return McBenchClient(redis.from_url(redis_url))
