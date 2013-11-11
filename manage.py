import json

from flask.ext.script import Manager

import mcbench.benchmark
import mcbench.client
import mcbench.query
from app import app

manager = Manager(app)
mcbench_client = mcbench.client.create_for_app(app)


@manager.command
def load_manifest(manifest, mcbench_client=mcbench_client):
    with open(manifest) as f:
        manifest = json.load(f)
        for project in manifest['projects']:
            mcbench_client.insert_benchmark(project)

if __name__ == '__main__':
    manager.run()
