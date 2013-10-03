import collections
import os

import boto
import chardet
import lxml.etree
import redis


def fix_utf8(s):
    encoding = chardet.detect(s)['encoding']
    return unicode(s.decode(encoding))


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

    def matches(self, xpath_query):
        matching_lines = collections.defaultdict(list)
        for base, files in self.get_files().items():
            matches = xpath_query(files['etree'])
            if matches:
                matching_lines[base] = [e.get('line') for e in matches]
        return matching_lines

    def get_files(self):
        if not self._files:
            keys = self._client.s3_bucket.list(prefix=self.name)
            keys = {key.key: key for key in keys}
            for m_key in keys:
                if not m_key.endswith('.m'):
                    continue
                base = os.path.splitext(m_key)[0]
                xml_key = '%s.xml' % base
                m_contents = keys[m_key].get_contents_as_string()
                xml_contents = keys[xml_key].get_contents_as_string()
                xml_parsed = lxml.etree.XML(xml_contents)
                self._files[base] = {
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
    def __init__(self, redis, s3_bucket):
        self.redis = redis
        self.s3_bucket = s3_bucket

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
    aws_key = app.config['AWS_ACCESS_KEY_ID']
    aws_secret = app.config['AWS_SECRET_ACCESS_KEY']
    bucket = app.config['AWS_S3_BUCKET']
    s3_bucket = boto.connect_s3(aws_key, aws_secret).get_bucket(bucket)
    return McBenchClient(redis=redis_instance, s3_bucket=s3_bucket)


def create(redis_url=None):
    if redis_url is None:
        redis_url = 'redis://localhost:6379'
    return McBenchClient(
        redis=redis.from_url(redis_url),
        s3_bucket=boto.connect_s3().get_bucket('mclab.mcbench'))
