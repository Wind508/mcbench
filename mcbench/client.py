import redis

import mcbench.benchmark


class BenchmarkDoesNotExist(Exception):
    pass


class BenchmarkAlreadyExists(Exception):
    pass


class McBenchClient(object):
    def __init__(self, redis, data_root):
        self.redis = redis
        self.data_root = data_root

    def get_benchmark_by_id(self, benchmark_id):
        benchmark_id = str(benchmark_id)
        data = self.redis.hgetall('benchmark:%s' % benchmark_id)
        if not data:
            raise BenchmarkDoesNotExist
        benchmark = mcbench.benchmark.Benchmark(**data)
        benchmark.tags = benchmark.tags.split(',')
        benchmark.decode_utf8()
        benchmark.data_root = self.data_root
        return benchmark

    def get_benchmark_by_name(self, name):
        benchmark_id = self.redis.get('name:%s:id' % name)
        if benchmark_id is None:
            raise BenchmarkDoesNotExist
        return self.get_benchmark_by_id(benchmark_id)

    def get_all_benchmarks(self):
        benchmarks = [self.get_benchmark_by_id(key[len('benchmark:'):])
            for key in self.redis.keys('benchmark:*')]
        return mcbench.benchmark.BenchmarkSet(benchmarks)

    def insert_benchmark(self, benchmark):
        benchmark_id = self.redis.get('name:%s:id' % benchmark.name)
        if benchmark_id is not None:
            raise BenchmarkAlreadyExists
        benchmark_id = self.redis.incr('global:next_benchmark_id')
        self.redis.set('name:%s:id' % benchmark.name, benchmark_id)
        self.redis.hmset('benchmark:%s' % benchmark_id, benchmark.as_dict())


def create_for_app(app):
    return create(app.config['DATA_ROOT'], app.config['REDIS_URL'])


def create(data_root, redis_url=None):
    if redis_url is None:
        redis_url = 'redis://localhost:6379'
    return McBenchClient(redis=redis.from_url(redis_url), data_root=data_root)
