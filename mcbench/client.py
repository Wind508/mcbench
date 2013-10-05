import collections
import os

import chardet
import redis

import mcbench.xpath


def fix_utf8(s):
    encoding = chardet.detect(s)['encoding']
    return unicode(s.decode(encoding))


def get_matlab_files(root):
    for dirpath, _, files in os.walk(root):
        for file in files:
            base, ext = os.path.splitext(file)
            if ext == '.m':
                yield os.path.join(dirpath, base)


def get_file_contents(filename):
    with open(filename) as f:
        return f.read()


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

        self._files = {}
        self._client = None

    def decode_utf8(self):
        self.author = self.author.decode('utf-8')
        self.summary = self.summary.decode('utf-8')
        self.tags = [tag.decode('utf-8') for tag in self.tags]
        self.title = self.title.decode('utf-8')

    def matches(self, query):
        return query is None or bool(self.get_matching_lines(query))

    def get_matching_lines(self, query):
        matching_lines = collections.defaultdict(lambda: {'m': [], 'xml': []})
        if query is not None:
            for base, files in self.get_files().items():
                for match in query(files['etree']):
                    matching_lines[base]['m'].append(match.get('line'))
                    matching_lines[base]['xml'].append(match.sourceline)
        return matching_lines

    def get_files(self):
        if not self._files:
            root = os.path.join(self._client.data_root, self.name)
            for base in get_matlab_files(root):
                m_contents = get_file_contents('%s.m' % base)
                xml_contents = get_file_contents('%s.xml' % base)
                xml_parsed = mcbench.xpath.parse_xml(xml_contents)
                self._files[base[len(root) + 1:]] = {
                    'm': fix_utf8(m_contents),
                    'xml': xml_contents,
                    'etree': xml_parsed,
                }
        return self._files

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

        self._benchmark_cache = {}

    def get_benchmark_by_id(self, benchmark_id):
        benchmark_id = str(benchmark_id)
        if benchmark_id not in self._benchmark_cache:
            data = self.redis.hgetall('benchmark:%s' % benchmark_id)
            if not data:
                raise BenchmarkDoesNotExist
            benchmark = Benchmark(**data)
            benchmark.tags = benchmark.tags.split(',')
            benchmark.decode_utf8()
            benchmark._client = self
            self._benchmark_cache[benchmark_id] = benchmark
        return self._benchmark_cache[benchmark_id]

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
        del benchmark_dict['_files']
        del benchmark_dict['_client']
        benchmark_dict['tags'] = ','.join(benchmark_dict['tags'])
        self.redis.set('name:%s:id' % benchmark.name, benchmark_id)
        self.redis.hmset('benchmark:%s' % benchmark_id, vars(benchmark))


def create_for_app(app):
    redis_instance = redis.from_url(app.config['REDIS_URL'])
    data_root = app.config['DATA_ROOT']
    return McBenchClient(redis=redis_instance, data_root=data_root)


def create(redis_url=None, data_root=None):
    if redis_url is None:
        redis_url = 'redis://localhost:6379'
    if data_root is None:
        data_root = '/Users/isbadawi/code/py/matlab-file-exchange-scraper/downloads/successfully_parsed'
    return McBenchClient(
        redis=redis.from_url(redis_url),
        data_root=data_root)
