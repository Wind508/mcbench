import unittest
import urllib

import app
import manage
import mcbench.client
import mcbench.xpath


class McBenchAppTestCase(unittest.TestCase):
    def setUp(self):
        app.app.config['DB_PATH'] = ':memory:'
        app.app.config['TESTING'] = True
        self.context = app.app.app_context()
        self.context.push()
        self.app = app.app.test_client()
        manage.load_manifest('testdata/manifest.json', app.get_client())

    def tearDown(self):
        self.context.pop()

    def test_index_page_renders_without_errors(self):
        self.assertEqual(200, self.app.get('/').status_code)

    def test_about_page_renders_without_errors(self):
        self.assertEqual(200, self.app.get('/about').status_code)

    def test_help_page_renders_without_errors(self):
        self.assertEqual(200, self.app.get('/help').status_code)

    def test_list_page_renders_without_errors(self):
        self.assertEqual(200, self.app.get('/list').status_code)

    def _search_for(self, query):
        params = urllib.urlencode({'query': query})
        return self.app.get('/list', query_string=params, follow_redirects=True)

    def _search_benchmark_for(self, benchmark, query):
        params = urllib.urlencode({'query': query})
        return self.app.get('/benchmark/%s' % benchmark, query_string=params)

    def test_valid_query_on_list_page(self):
        response = self._search_for('//ForStmt')
        self.assertEqual(200, response.status_code)
        self.assertIn('Found 16 occurrences', response.data)

    def test_saved_query_on_list_page(self):
        manage.load_initial_queries(app.get_client())
        response = self._search_for("//ParameterizedExpr[is_call('eval')]")
        self.assertEqual(200, response.status_code)
        self.assertIn('Found 6 occurrences', response.data)

    def test_syntax_error_in_query_flashes_error(self):
        response = self._search_for(r'\\ForStmt')
        self.assertEqual(200, response.status_code)
        self.assertIn('XPathSyntaxError', response.data)

    def test_eval_error_in_query_flashes_error(self):
        response = self._search_for(r'//ForStmt[badpredicate()]')
        self.assertEqual(200, response.status_code)
        self.assertIn('XPathEvalError', response.data)

    def test_benchmark_page_renders_without_errors(self):
        self.assertEqual(200, self.app.get('/benchmark/1888-repmf').status_code)

    def test_valid_query_on_benchmark_page(self):
        response = self._search_benchmark_for('1888-repmf', '//IfStmt')
        self.assertIn('Found 2 occurrences', response.data)

    def test_syntax_error_in_benchmark_query_flashes_error(self):
        response = self._search_benchmark_for('1888-repmf', r'\\ForStmt')
        self.assertIn('XPathSyntaxError', response.data)

    def test_eval_error_in_benchmark_query_flashes_error(self):
        response = self._search_benchmark_for('1888-repmf', '//IfStmt[bad()]')
        self.assertIn('XPathEvalError', response.data)


class McBenchClientTestCase(unittest.TestCase):
    def setUp(self):
        self.client = mcbench.client.create('testdata', ':memory:')
        manage.load_manifest('testdata/manifest.json', self.client)

    def tearDown(self):
        self.client.close()

    def test_testdata_was_loaded_correctly(self):
        benchmarks = self.client.get_all_benchmarks()
        self.assertItemsEqual(
            ['1888-repmf', '8636-emgm', '33851-wind-barb-plotter'],
            [benchmark.name for benchmark in benchmarks])

        repmf = self.client.get_benchmark_by_name('1888-repmf')
        emgm = self.client.get_benchmark_by_name('8636-emgm')
        plotter = self.client.get_benchmark_by_name('33851-wind-barb-plotter')
        self.assertEqual('repmf', next(repmf.get_files()).name)
        self.assertEqual('EM_GM', next(emgm.get_files()).name)
        self.assertEqual('windbarbm', next(plotter.get_files()).name)

    def test_get_nonexistent_benchmark(self):
        with self.assertRaises(mcbench.client.BenchmarkDoesNotExist):
            self.client.get_benchmark_by_name('does-not-exist')

    def test_simple_query(self):
        benchmarks = self.client.get_all_benchmarks()
        result = benchmarks.get_query_results('//ForStmt')
        self.assertEqual(16, result.num_matches)

    def test_malformed_query(self):
        benchmarks = self.client.get_all_benchmarks()
        with self.assertRaises(mcbench.xpath.XPathError):
            benchmarks.get_query_results(r'\ForStmt')

    def test_saving_query_caches_results(self):
        results = self.client.get_query_results('//ForStmt')
        query_id = self.client.insert_query('//ForStmt', 'For loops')
        self.client.set_query_results(query_id, results)

        results = self.client.get_query_results('//ForStmt')
        self.assertTrue(results.cached)
        self.assertEqual(16, results.num_matches)

    def test_deleting_query_deletes_cached_results(self):
        results = self.client.get_query_results('//ForStmt')
        query_id = self.client.insert_query('//ForStmt', 'For loops')
        self.client.set_query_results(query_id, results)
        self.client.delete_query(query_id)

        results = self.client.get_query_results('//ForStmt')
        self.assertFalse(results.cached)

if __name__ == '__main__':
    unittest.main()
