import redis

import mcbench.benchmark
import mcbench.query


class BenchmarkDoesNotExist(Exception):
    pass


class BenchmarkAlreadyExists(Exception):
    pass


class QueryDoesNotExist(Exception):
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
        data['author'] = data['author'].decode('utf-8')
        data['summary'] = data['summary'].decode('utf-8')
        data['tags'] = [tag.decode('utf-8') for tag in data['tags'].split(',')]
        data['title'] = data['title'].decode('utf-8')
        return mcbench.benchmark.Benchmark(self.data_root, data=data)

    def get_benchmark_by_name(self, name):
        benchmark_id = self.redis.get('name:%s:id' % name)
        if benchmark_id is None:
            raise BenchmarkDoesNotExist
        return self.get_benchmark_by_id(benchmark_id)

    def get_all_benchmarks(self):
        num_benchmarks = int(self.redis.get('global:next_benchmark_id'))
        benchmarks = (self.get_benchmark_by_id(id)
                      for id in xrange(1, num_benchmarks + 1))
        return mcbench.benchmark.BenchmarkSet(self.data_root, benchmarks)

    def insert_benchmark(self, benchmark):
        benchmark_id = self.redis.get('name:%s:id' % benchmark.name)
        if benchmark_id is not None:
            raise BenchmarkAlreadyExists
        benchmark_id = self.redis.incr('global:next_benchmark_id')
        self.redis.set('name:%s:id' % benchmark.name, benchmark_id)
        data = dict(benchmark.data, tags=','.join(benchmark.data['tags']))
        self.redis.hmset('benchmark:%s' % benchmark_id, data)

    def get_query_by_id(self, query_id):
        query_id = str(query_id)
        data = self.redis.hgetall('query:%s' % query_id)
        if not data:
            raise QueryDoesNotExist
        return mcbench.query.Query(data['xpath'], data['name'])

    def get_all_queries(self):
        num_queries = int(self.redis.get('global:next_query_id'))
        return [self.get_query_by_id(id) for id in xrange(1, num_queries + 1)]

    def insert_query(self, query):
        query_id = self.redis.incr('global:next_query_id')
        data = dict(name=query.name, xpath=query.xpath)
        self.redis.hmset('query:%s' % query_id, data)


def create_for_app(app):
    return create(app.config['DATA_ROOT'], app.config['REDIS_URL'])


def create(data_root, redis_url=None):
    if redis_url is None:
        redis_url = 'redis://localhost:6379'
    return McBenchClient(redis=redis.from_url(redis_url), data_root=data_root)
