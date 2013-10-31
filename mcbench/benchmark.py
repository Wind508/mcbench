import chardet

import collections
import itertools
import multiprocessing
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
        query = mcbench.xpath.compile(query)
        return query(self._parse_xml())

    def __repr__(self):
        return '<File: %s>' % self.name


class Benchmark(object):
    def __init__(self, data_root, name=None, data=None):
        assert not (name is None and data is None)
        self.data_root = data_root
        self.name = name if name is not None else data['name']
        self.data = data

    def __getattr__(self, attr):
        return self.data[attr]

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
        if query is None:
            return lines
        for f in self.get_files():
            for match in f.get_matches(query):
                lines[f.name]['m'].append(match.get('line'))
                lines[f.name]['xml'].append(match.sourceline)
        return lines

    def __repr__(self):
        return '<Benchmark: %s>' % self.name


def get_num_matches_worker((data_root, name, query)):
    return Benchmark(data_root, name).get_num_matches(query)


class BenchmarkSet(list):
    def __init__(self, data_root, benchmarks):
        super(BenchmarkSet, self).__init__(benchmarks)
        self.data_root = data_root

    def _map(self, query):
        pool = multiprocessing.Pool(processes=32)
        results = pool.map(
            get_num_matches_worker,
            ((self.data_root, b.name, query) for b in self))
        pool.close()
        return results

    def get_num_matches(self, query):
        benchmarks = []
        matches_by_benchmark = collections.defaultdict(int)
        total_matches = 0

        results = self._map(query)
        for benchmark, num_matches in itertools.izip(self, results):
            if num_matches:
                benchmarks.append(benchmark)
                matches_by_benchmark[benchmark.name] += num_matches
                total_matches += num_matches

        return benchmarks, matches_by_benchmark, total_matches
