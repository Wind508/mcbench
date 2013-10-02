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
    query_string = flask.request.args.get('query')
    try:
        query = lxml.etree.XPath(query_string)
    except lxml.etree.XPathSyntaxError as e:
        flask.flash('XPath syntax error: %s' % e.msg)
        return flask.redirect(flask.url_for('index'))

    all_benchmarks = mcbench_client.get_all_benchmarks()
    matching_benchmarks = [b for b in all_benchmarks if b.matches(query)]
    return flask.render_template('list.html', benchmarks=matching_benchmarks)

if __name__ == "__main__":
    app.run(debug=True)
