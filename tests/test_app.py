from nose.tools import eq_, assert_in, assert_not_in

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

    def _get(self, path, **kwargs):
        return self.app.get(path, query_string=kwargs, follow_redirects=True)

    def _post(self, path, **kwargs):
        return self.app.post(path, data=kwargs, follow_redirects=True)

    def _search_for(self, query):
        return self._get('/list', query=query)

    def _search_benchmark_for(self, benchmark, query):
        return self._get('/benchmark/%s' % benchmark, query=query)

    def _save_query(self, xpath, name):
        return self._post('/save_query', xpath=xpath, name=name)

    def _delete_query(self, xpath):
        return self._post('/delete_query', xpath=xpath)

    def test_index_page_renders_without_errors(self):
        eq_(200, self.app.get('/').status_code)

    def test_about_page_renders_without_errors(self):
        eq_(200, self.app.get('/about').status_code)

    def test_help_page_renders_without_errors(self):
        eq_(200, self.app.get('/help').status_code)

    def test_list_page_renders_without_errors(self):
        eq_(200, self.app.get('/list').status_code)

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

    def test_saving_non_cached_query_flashes_error(self):
        response = self._save_query('//ForStmt', 'For loops')
        assert_in('No such query', response.data)

    def test_deleting_unsaved_query_flashes_error(self):
        response = self._delete_query('//ForStmt')
        assert_in('No such query', response.data)

    def test_saved_query_appears_on_front_page(self):
        self._search_for('//ForStmt')
        self._save_query('//ForStmt', 'For loops')

        response = self.app.get('/')
        assert_in('//ForStmt', response.data)
        assert_in('For loops', response.data)

    def test_deleted_query_does_not_appear_on_front_page(self):
        self._search_for('//ForStmt')
        self._save_query('//ForStmt', 'For loops')
        self._delete_query('//ForStmt')

        response = self.app.get('/')
        assert_not_in('//ForStmt', response.data)

    def test_save_query_form_appears_for_uncached_query(self):
        response = self._search_for('//ForStmt')
        assert_in('Name this query', response.data)

    def test_save_query_form_appears_for_cached_but_unsaved_query(self):
        self._search_for('//ForStmt')
        response = self._search_for('//ForStmt')
        assert_in('Name this query', response.data)

    def test_save_query_form_does_not_appear_for_saved_query(self):
        self._search_for('//ForStmt')
        response = self._save_query('//ForStmt', 'For loops')
        assert_not_in('Name this query', response.data)
