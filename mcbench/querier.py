import collections
import multiprocessing

import mcbench.xpath
from mcbench.models import Benchmark, Query
from mcbench import settings


def matches_in(xpath, file):
    xpath = mcbench.xpath.compile(xpath)
    xml = mcbench.xpath.parse_xml_filename(file.xml_path)
    return xpath.execute(xml)


def matching_lines(benchmark, xpath):
    lines = collections.defaultdict(lambda: {'m': [], 'xml': []})
    if xpath is None:
        return lines
    for file in benchmark.files:
        matches = matches_in(xpath, file)
        lines[file.name]['m'] = [match.get('line', 1) for match in matches]
        lines[file.name]['xml'] = [match.sourceline for match in matches]
    return lines


def _num_matches_worker(args):
    name, xpath = args
    benchmark = Benchmark(name=name)
    return sum(len(matches_in(xpath, file)) for file in benchmark.files)


def _map(benchmarks, query):
    pool = multiprocessing.Pool(processes=32)
    results = pool.map(_num_matches_worker,
                       ((b.name, query) for b in benchmarks))
    pool.close()
    pool.join()
    return results


def compute_matches(xpath):
    benchmarks = Benchmark.all()
    results = _map(benchmarks, xpath)
    for benchmark, num_matches in zip(benchmarks, results):
        if num_matches:
            yield benchmark, num_matches


def get_matches(xpath):
    query = Query.find_by_xpath(xpath)
    if query is None:
        query = Query.create(xpath=xpath, name='')
        query.cache_matches(compute_matches(xpath))
    return list(query.get_cached_matches())
