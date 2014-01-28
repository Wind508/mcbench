import urllib

from nose.tools import eq_, assert_in

import app
import manage


class TestMcBenchApp(object):
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
        eq_(200, self.app.get('/').status_code)

    def test_about_page_renders_without_errors(self):
        eq_(200, self.app.get('/about').status_code)

    def test_help_page_renders_without_errors(self):
        eq_(200, self.app.get('/help').status_code)

    def test_list_page_renders_without_errors(self):
        eq_(200, self.app.get('/list').status_code)

    def _search_for(self, query):
        params = urllib.urlencode({'query': query})
        return self.app.get('/list', query_string=params, follow_redirects=True)

    def _search_benchmark_for(self, benchmark, query):
        params = urllib.urlencode({'query': query})
        return self.app.get('/benchmark/%s' % benchmark, query_string=params)

    def test_valid_query_on_list_page(self):
        response = self._search_for('//ForStmt')
        eq_(200, response.status_code)
        assert_in('Found 16 occurrences', response.data)

    def test_saved_query_on_list_page(self):
        manage.load_initial_queries(app.get_client())
        response = self._search_for("//ParameterizedExpr[is_call('eval')]")
        eq_(200, response.status_code)
        assert_in('Found 6 occurrences', response.data)

    def test_syntax_error_in_query_flashes_error(self):
        response = self._search_for(r'\\ForStmt')
        eq_(200, response.status_code)
        assert_in('XPathSyntaxError', response.data)

    def test_eval_error_in_query_flashes_error(self):
        response = self._search_for(r'//ForStmt[badpredicate()]')
        eq_(200, response.status_code)
        assert_in('XPathEvalError', response.data)

    def test_benchmark_page_renders_without_errors(self):
        eq_(200, self.app.get('/benchmark/1888-repmf').status_code)

    def test_valid_query_on_benchmark_page(self):
        response = self._search_benchmark_for('1888-repmf', '//IfStmt')
        assert_in('Found 2 occurrences', response.data)

    def test_syntax_error_in_benchmark_query_flashes_error(self):
        response = self._search_benchmark_for('1888-repmf', r'\\ForStmt')
        assert_in('XPathSyntaxError', response.data)

    def test_eval_error_in_benchmark_query_flashes_error(self):
        response = self._search_benchmark_for('1888-repmf', '//IfStmt[bad()]')
        assert_in('XPathEvalError', response.data)
