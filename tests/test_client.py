from nose.tools import eq_, ok_, assert_items_equal, assert_raises

import manage
import mcbench.client

class TestMcBenchClient(object):
    def setup(self):
        self.client = mcbench.client.create('testdata', ':memory:')
        manage.load_manifest('testdata/manifest.json', self.client)

    def teardown(self):
        self.client.close()

    def test_testdata_was_loaded_correctly(self):
        benchmarks = self.client.get_all_benchmarks()
        assert_items_equal(
            ['1888-repmf', '8636-emgm', '33851-wind-barb-plotter'],
            [benchmark.name for benchmark in benchmarks])

        repmf = self.client.get_benchmark_by_name('1888-repmf')
        emgm = self.client.get_benchmark_by_name('8636-emgm')
        plotter = self.client.get_benchmark_by_name('33851-wind-barb-plotter')
        eq_('repmf', next(repmf.get_files()).name)
        eq_('EM_GM', next(emgm.get_files()).name)
        eq_('windbarbm', next(plotter.get_files()).name)

    def test_get_nonexistent_benchmark(self):
        with assert_raises(mcbench.client.BenchmarkDoesNotExist):
            self.client.get_benchmark_by_name('does-not-exist')

    def test_simple_query(self):
        benchmarks = self.client.get_all_benchmarks()
        result = benchmarks.get_query_results('//ForStmt')
        eq_(16, result.total_matches)

    def test_malformed_query(self):
        benchmarks = self.client.get_all_benchmarks()
        with assert_raises(mcbench.xpath.XPathError):
            benchmarks.get_query_results(r'\ForStmt')

    def test_running_query_caches_results(self):
        original_results = self.client.get_query_results('//ForStmt')
        self.client.save_query('//ForStmt', 'For loops')

        cached_results = self.client.get_query_results('//ForStmt')
        ok_(cached_results.cached)
        ok_(cached_results.saved)
        eq_(original_results.total_matches, cached_results.total_matches)

    def test_unsaving_query_keeps_cached_results(self):
        original_results = self.client.get_query_results('//ForStmt')
        self.client.save_query('//ForStmt', 'For loops')
        self.client.unsave_query('//ForStmt')

        cached_results = self.client.get_query_results('//ForStmt')
        ok_(cached_results.cached)
        ok_(not cached_results.saved)
        eq_(original_results.total_matches, cached_results.total_matches)
