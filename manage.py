import json

from flask.ext.script import Manager

import app

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
    existing_benchmarks = [b.name for b in mcbench_client.get_all_benchmarks()]
    with open(manifest) as f:
        manifest = json.load(f)
        for project in manifest['projects']:
            if project['name'] not in existing_benchmarks:
                mcbench_client.insert_benchmark(project)


@manager.command
def load_initial_queries(mcbench_client=None):
    if mcbench_client is None:
        with app.app.app_context():
            load_initial_queries(app.get_client())
            return

    for name, xpath in EXAMPLE_QUERIES:
        query_id = mcbench_client.insert_query(xpath, name)
    refresh_query_results(mcbench_client)


@manager.command
def refresh_query_results(mcbench_client=None):
    if mcbench_client is None:
        with app.app.app_context():
            refresh_query_results(app.get_client())
            return

    all_benchmarks = mcbench_client.get_all_benchmarks()
    for query in mcbench_client.get_all_queries():
        result = all_benchmarks.get_query_results(query['xpath'])
        mcbench_client.set_query_results(query['id'], result)



if __name__ == '__main__':
    manager.run()
