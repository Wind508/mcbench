import datetime
import json
import os

from flask.ext.script import Manager

from mcbench.models import Benchmark, Query, QueryMatch
from mcbench import settings, querier
from mcbench import app

manager = Manager(app)

EXAMPLE_QUERIES = (
    ('Calls to eval', "//ParameterizedExpr[is_call('eval')]"),
    ('Calls to feval with a string literal target',
     "//ParameterizedExpr[is_call('feval') and name(arg(1))='StringLiteralExpr']"),
    ('Copy statements inside loops',
     "//ForStmt//AssignStmt[name(lhs())='NameExpr' and name(rhs())='NameExpr' and rhs()/@kind='VAR']"),
    ('Recursive calls', '//ParameterizedExpr[is_call(ancestor::Function/Name/@nameId)]'),
    ('Functions with multiple return values',
     "//Function[./OutputParamList[count(Name) > 1]]")
)


@manager.command
def create_tables():
    Benchmark.create_table()
    Query.create_table()
    QueryMatch.create_table()


@manager.command
def drop_tables():
    Benchmark.drop_table()
    Query.drop_table()
    QueryMatch.drop_table()


def create_benchmark_from_manifest_entry(entry):
    date_submitted = datetime.datetime.strptime(
        entry['date_submitted'], '%d %b %Y')
    date_updated = datetime.datetime.strptime(
        entry['date_updated'], '%d %b %Y')
    fields = dict(entry,
                  date_submitted=date_submitted,
                  date_updated=date_updated)
    benchmark = Benchmark.create(**fields)


@manager.command
def load_manifest(manifest):
    existing_benchmarks = set(b.name for b in Benchmark.all())
    with open(manifest) as f:
        manifest = json.load(f)
        for project in manifest['projects']:
            if project['name'] not in existing_benchmarks:
                create_benchmark_from_manifest_entry(project)


@manager.command
def load_initial_queries():
    for name, xpath in EXAMPLE_QUERIES:
        query = Query.create(xpath=xpath, name=name)
        query.cache_matches(querier.compute_matches(xpath))


@manager.command
def refresh_query_results():
    for query in Query.all():
        query.expire_matches()
        query.cache_matches(querier.compute_matches(query.xpath))


@manager.command
def purge_unsaved_queries():
    for query in Query.unsaved():
        query.delete_instance()

if __name__ == '__main__':
    manager.run()
