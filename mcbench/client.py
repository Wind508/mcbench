import redis


class Benchmark(object):
    def __init__(self, author, author_url, date_submitted, date_updated,
                 name, summary, tags, title, url):
        self.author = author
        self.author_url = author_url
        self.date_submitted = date_submitted
        self.date_updated = date_updated
        self.name = name
        self.summary = summary
        self.tags = tags
        self.title = title
        self.url = url

    def decode_utf8(self):
        self.author = self.author.decode('utf-8')
        self.summary = self.summary.decode('utf-8')
        self.tags = [tag.decode('utf-8') for tag in self.tags]
        self.title = self.title.decode('utf-8')

    def __repr__(self):
        return '<Benchmark: %s>' % self.name


class BenchmarkDoesNotExist(Exception):
    pass


class BenchmarkAlreadyExists(Exception):
    pass


class McBenchClient(object):
    def __init__(self, redis):
        self.redis = redis

    def get_benchmark_by_id(self, benchmark_id):
        data = self.redis.hgetall('benchmark:%s' % benchmark_id)
        if not data:
            raise BenchmarkDoesNotExist
        benchmark = Benchmark(**data)
        benchmark.tags = benchmark.tags.split(',')
        benchmark.decode_utf8()
        return benchmark

    def get_benchmark_by_name(self, name):
        benchmark_id = self.redis.get('name:%s:id' % name)
        if benchmark_id is None:
            raise BenchmarkDoesNotExist
        return self.get_benchmark_by_id(benchmark_id)

    def get_all_benchmarks(self):
        return [self.get_benchmark_by_id(key[len('benchmark:'):])
                for key in self.redis.keys('benchmark:*')]

    def insert_benchmark(self, benchmark):
        benchmark_id = self.redis.get('name:%s:id' % benchmark.name)
        if benchmark_id is not None:
            raise BenchmarkAlreadyExists
        benchmark_id = self.redis.incr('global:next_benchmark_id')
        benchmark_dict = vars(benchmark)
        benchmark_dict['tags'] = ','.join(benchmark_dict['tags'])
        self.redis.set('name:%s:id' % benchmark.name, benchmark_id)
        self.redis.hmset('benchmark:%s' % benchmark_id, vars(benchmark))


def from_redis_url(redis_url):
    return McBenchClient(redis.from_url(redis_url))
