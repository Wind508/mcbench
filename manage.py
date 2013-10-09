import json
import os

from flask.ext.script import Manager

import mcbench.client
from app import app

manager = Manager(app)


@manager.command
def load_manifest(manifest):
    mcbench_client = mcbench.client.create_for_app(app)
    with open(os.path.expanduser(manifest)) as f:
        manifest = json.load(f)
        for project in manifest['projects']:
            benchmark = mcbench.client.Benchmark(**project)
            mcbench_client.insert_benchmark(benchmark)

if __name__ == '__main__':
    manager.run()
