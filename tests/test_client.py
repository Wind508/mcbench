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
        eq_(16, result.num_matches)

    def test_malformed_query(self):
        benchmarks = self.client.get_all_benchmarks()
        with assert_raises(mcbench.xpath.XPathError):
            benchmarks.get_query_results(r'\ForStmt')

    def test_saving_query_caches_results(self):
        results = self.client.get_query_results('//ForStmt')
        query_id = self.client.insert_query('//ForStmt', 'For loops')
        self.client.set_query_results(query_id, results)

        results = self.client.get_query_results('//ForStmt')
        ok_(results.cached)
        eq_(16, results.num_matches)

    def test_deleting_query_deletes_cached_results(self):
        results = self.client.get_query_results('//ForStmt')
        query_id = self.client.insert_query('//ForStmt', 'For loops')
        self.client.set_query_results(query_id, results)
        self.client.delete_query(query_id)

        results = self.client.get_query_results('//ForStmt')
        ok_(not results.cached)
