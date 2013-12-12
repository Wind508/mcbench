import json

from flask.ext.script import Manager

import app
import mcbench.benchmark

manager = Manager(app.app)


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

if __name__ == '__main__':
    manager.run()
