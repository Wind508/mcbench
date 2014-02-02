from nose.tools import eq_, ok_, assert_items_equal, assert_raises

import manage
import mcbench.xpath
from mcbench.models import db, Query
from mcbench import querier


class TestQueries(object):
    def setup(self):
        db.init(':memory:')
        manage.create_tables()
        manage.load_manifest('testdata/manifest.json')

    def teardown(self):
        manage.drop_tables()

    def test_simple_query(self):
        matches = querier.get_matches('//ForStmt')
        eq_(16, sum(m.num_matches for m in matches))

    def test_malformed_query(self):
        with assert_raises(mcbench.xpath.XPathError):
            querier.get_matches(r'\ForStmt')

    def test_running_query_caches_results(self):
        original_matches = querier.get_matches('//ForStmt')
        query = Query.find_by_xpath('//ForStmt')
        cached_matches = query.get_cached_matches()
        eq_(len(original_matches), len(cached_matches))

    def test_unsaving_query_keeps_cached_results(self):
        original_matches = querier.get_matches('//ForStmt')
        query = Query.find_by_xpath('//ForStmt')
        query.name = 'For loops'
        query.save()
        query.unsave()
        cached_matches = query.get_cached_matches()
        eq_(len(original_matches), len(cached_matches))
