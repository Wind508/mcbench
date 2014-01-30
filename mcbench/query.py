import itertools
import multiprocessing

from .benchmark import Benchmark


class QueryResult(object):
    def __init__(self, cached, saved=False):
        self.matches = []
        self.total_matches = 0
        self.cached = cached
        self.saved = saved

    def add_matching_benchmark(self, benchmark, num_matches):
        self.matches.append((benchmark, num_matches))
        self.total_matches += num_matches

    def as_db_rows(self, query_id):
        def make_row(match):
            return (match[0].id, query_id, match[1])
        return itertools.imap(make_row, self.matches)

    def sort_by_frequency(self):
        self.matches.sort(key=lambda m: m[1], reverse=True)


def _get_num_matches_worker((id, data_root, name, query)):
    return Benchmark(id, data_root, name).get_num_matches(query)


def _map(benchmarks, query, data_root):
    pool = multiprocessing.Pool(processes=32)
    results = pool.map(
        _get_num_matches_worker,
        ((b.id, data_root, b.name, query) for b in benchmarks))
    pool.close()
    return results


def execute(query, benchmarks, data_root):
    result = QueryResult(cached=False)
    results = _map(benchmarks, query, data_root)
    for benchmark, num_matches in itertools.izip(benchmarks, results):
        if num_matches:
            result.add_matching_benchmark(benchmark, num_matches)
    return result
