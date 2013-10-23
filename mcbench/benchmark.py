import chardet

import collections
import itertools
import multiprocessing.pool
import os

import mcbench.xpath


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
        return mcbench.xpath.parse_xml_filename(
            os.path.join(self.root, '%s.xml' % self.name))

    def get_matches(self, query):
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

        self.data_root = None

    def decode_utf8(self):
        self.author = self.author.decode('utf-8')
        self.summary = self.summary.decode('utf-8')
        self.tags = [tag.decode('utf-8') for tag in self.tags]
        self.title = self.title.decode('utf-8')

    def get_files(self):
        root = os.path.join(self.data_root, self.name)
        for dirpath, _, files in os.walk(root):
            for file in files:
                base, ext = os.path.splitext(file)
                if ext == '.m':
                    abs_path = os.path.join(dirpath, base)
                    yield File(root, abs_path[len(root) + 1:])

    def get_num_matches(self, query):
        return sum(len(f.get_matches(query)) for f in self.get_files())

    def get_matching_lines(self, query):
        lines = collections.defaultdict(lambda: {'m': [], 'xml': []})
        for f in self.get_files():
            for match in f.get_matches(query):
                lines[f.name]['m'].append(match.get('line'))
                lines[f.name]['xml'].append(match.sourceline)
        return lines

    def as_dict(self):
        return dict(
            author=self.author,
            author_url=self.author_url,
            date_submitted=self.date_submitted,
            date_updated=self.date_updated,
            name=self.name,
            summary=self.summary,
            tags=','.join(self.tags),
            title=self.title,
            url=self.url)

    def __repr__(self):
        return '<Benchmark: %s>' % self.name


class BenchmarkSet(list):
    def get_num_matches(self, query):
        thread_pool = multiprocessing.pool.ThreadPool(processes=4)
        results = thread_pool.map(lambda b: b.get_num_matches(query), self)

        benchmarks = []
        matches_by_benchmark = collections.defaultdict(int)
        total_matches = 0

        for benchmark, num_matches in itertools.izip(self, results):
            if num_matches:
                benchmarks.append(benchmark)
                matches_by_benchmark[benchmark.name] += num_matches
                total_matches += num_matches

        return benchmarks, matches_by_benchmark, total_matches
