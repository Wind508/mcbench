from multiprocessing import pool

import flask
import lxml.etree

import mcbench.client

app = flask.Flask(__name__)
app.config.from_object('conf')

mcbench_client = mcbench.client.from_redis_url(app.config['REDIS_URL'])


@app.route('/', methods=['GET'])
def index():
    return flask.render_template('index.html')


@app.route('/list', methods=['GET'])
def list():
    benchmarks = mcbench_client.get_all_benchmarks()
    return flask.render_template('list.html', benchmarks=benchmarks)


@app.route('/files/<name>', methods=['GET'])
def files(name):
    benchmark = mcbench_client.get_benchmark_by_name(name)
    return flask.render_template(
        'files.html',
        benchmark=benchmark,
        files=benchmark.get_files()
    )


@app.route('/search', methods=['GET'])
def search():
    query = flask.request.args.get('query')
    find = lxml.etree.XPath(query)
    def match(benchmark):
        results = {}
        for base, files in benchmark.get_files():
            results.setdefault(base, []).append(find(files['etree']))
        return results

    thread_pool = pool.ThreadPool(processes=10)
    results = thread_pool.map(match, mcbench_client.get_all_benchmarks())

if __name__ == "__main__":
    app.run(debug=True)
