import json

from flask.ext.script import Manager

import app
import mcbench.benchmark

manager = Manager(app.app)


EXAMPLE_QUERIES = (
    ('Calls to eval', "//ParameterizedExpr[is_call('eval')]"),
    ('Calls to feval with a string literal target',
     "//ParameterizedExpr[is_call('feval') and name(arg(1))='StringLiteralExpr']"),
    ('Copy statements inside loops',
     "//ForStmt//AssignStmt[name(lhs())='NameExpr' and name(rhs())='NameExpr' and rhs()/@kind='VAR']"),
    ('Recursive calls', '//ParameterizedExpr[is_call(ancestor::Function/@name)]'),
    ('Functions with multiple return values',
     "//Function[./OutputParamList[count(Name) > 1]]")
)


@manager.command
def load_manifest(manifest, mcbench_client=None):
    if mcbench_client is None:
        with app.app.app_context():
            load_manifest(manifest, app.get_client())
            return

    mcbench_client.init_tables()
    with open(manifest) as f:
        manifest = json.load(f)
        for project in manifest['projects']:
            mcbench_client.insert_benchmark(project)


@manager.command
def load_initial_queries(mcbench_client=None):
    if mcbench_client is None:
        with app.app.app_context():
            load_initial_queries(app.get_client())
            return

    all_benchmarks = mcbench_client.get_all_benchmarks()
    for name, xpath in EXAMPLE_QUERIES:
        benchmarks, matches_by_benchmark, num_matches = (
            all_benchmarks.get_num_matches(xpath))
        results = ','.join('%s:%s' % (b.id, matches_by_benchmark[b.name])
            for b in benchmarks)
        mcbench_client.insert_query(xpath, name, results)


if __name__ == '__main__':
    manager.run()
