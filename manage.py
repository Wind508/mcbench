import json

from flask.ext.script import Manager

import mcbench.benchmark
import mcbench.client
import mcbench.query
from app import app

manager = Manager(app)
mcbench_client = mcbench.client.create_for_app(app)

EXAMPLE_QUERIES = (
    ('Calls to eval', "//ParameterizedExpr[is_call('eval')]"),
    ('Calls to feval with a string literal target',
     "//ParameterizedExpr[is_call('feval') and ./*[position()=2 and name(.)='StringLiteralExpr']]"),
    ('Copy statements inside loops', "//ForStmt//AssignStmt[./*[position()=1 and name(.)='NameExpr'] and ./*[position()=2 and name(.)='NameExpr' and ./@kind='VAR']]"),
    ('Recursive calls', '//ParameterizedExpr[is_call(ancestor::Function/@name)]'),
    ('Functions with multiple return values',
     "//Function[./OutputParamList[count(Name) > 1]]"),
)


@manager.command
def load_manifest(manifest, mcbench_client=mcbench_client):
    with open(manifest) as f:
        manifest = json.load(f)
        for project in manifest['projects']:
            mcbench_client.insert_benchmark(project)

@manager.command
def load_example_queries(mcbench_client=mcbench_client):
    for name, xpath in EXAMPLE_QUERIES:
        mcbench_client.insert_query(xpath, name)

if __name__ == '__main__':
    manager.run()
