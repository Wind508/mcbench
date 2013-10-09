import os

import chardet
import redis

from . import xpath


def fix_utf8(s):
    encoding = chardet.detect(s)['encoding']
    try:
        return unicode(s.decode(encoding))
    except UnicodeDecodeError:
        # chardet seems to get the 2224-cost231-models files wrong;
        # it says windows-1255 but they're actually latin1 (according to vim).
        # This is an ugly workaround for this case.
        if encoding != 'windows-1255':
            raise
        return unicode(s.decode('latin1'))


class File(object):
    def __init__(self, root, name):
        self.root = root
        self.name = name

    def _read_file(self, ext):
        filename = os.path.join(self.root, '%s.%s' % (self.name, ext))
        with open(filename) as f:
            return f.read()

    def read_matlab(self):
        return fix_utf8(self._read_file('m'))

    def read_xml(self):
        return self._read_file('xml')

    def _parse_xml(self):
        return xpath.parse_xml_filename(
            os.path.join(self.root, '%s.xml' % self.name))

    def get_matches(self, query):
        if query is None:
            return []
        return query(self._parse_xml())

    def __repr__(self):
        return '<File: %s>' % self.name


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

        self._client = None

    def decode_utf8(self):
        self.author = self.author.decode('utf-8')
        self.summary = self.summary.decode('utf-8')
        self.tags = [tag.decode('utf-8') for tag in self.tags]
        self.title = self.title.decode('utf-8')

    def get_files(self):
        root = os.path.join(self._client.data_root, self.name)
        for dirpath, _, files in os.walk(root):
            for file in files:
                base, ext = os.path.splitext(file)
                if ext == '.m':
                    abs_path = os.path.join(dirpath, base)
                    yield File(root, abs_path[len(root) + 1:])

    def matches(self, query):
        if query is None:
            return True
        return any(file.get_matches(query) for file in self.get_files())

    def __repr__(self):
        return '<Benchmark: %s>' % self.name


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
        benchmark = Benchmark(**data)
        benchmark.tags = benchmark.tags.split(',')
        benchmark.decode_utf8()
        benchmark._client = self
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
        del benchmark_dict['_client']
        benchmark_dict['tags'] = ','.join(benchmark_dict['tags'])
        self.redis.set('name:%s:id' % benchmark.name, benchmark_id)
        self.redis.hmset('benchmark:%s' % benchmark_id, vars(benchmark))


def create_for_app(app):
    redis_instance = redis.from_url(app.config['REDIS_URL'])
    data_root = app.config['DATA_ROOT']
    return McBenchClient(redis=redis_instance, data_root=data_root)


def create(data_root, redis_url=None):
    if redis_url is None:
        redis_url = 'redis://localhost:6379'
    return McBenchClient(
        redis=redis.from_url(redis_url),
        data_root=data_root)
