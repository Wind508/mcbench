import flask
import lxml.etree

import mcbench.client
import mcbench.highlighters

app = flask.Flask(__name__)
app.config.from_object('conf')
app.jinja_env.filters['highlight_matlab'] = mcbench.highlighters.matlab
app.jinja_env.filters['highlight_xml'] = mcbench.highlighters.xml

mcbench_client = mcbench.client.create_for_app(app)


@app.route('/', methods=['GET'])
def index():
    return flask.render_template('index.html')


@app.route('/list', methods=['GET'])
def benchmark_list():
    benchmarks = mcbench_client.get_all_benchmarks()

    query_string = flask.request.args.get('query')
    if query_string:
        try:
            query = lxml.etree.XPath(query_string)
        except lxml.etree.XPathSyntaxError as e:
            flask.flash('XPath syntax error: %s' % e.msg)
            return flask.redirect(flask.url_for('index'))
        benchmarks = [b for b in benchmarks if b.matches(query)]
    return flask.render_template('list.html', benchmarks=benchmarks)


@app.route('/benchmark/<name>', methods=['GET'])
def benchmark(name):
    benchmark = mcbench_client.get_benchmark_by_name(name)

    query = flask.request.args.get('query')
    if query:
        try:
            query = lxml.etree.XPath(query)
        except lxml.etree.XPathSyntaxError as e:
            flask.flash('XPath syntax error: %s' % e.msg)
            return flask.redirect(flask.url_for('benchmark', name=name))
    matching_lines = benchmark.matches(query)

    return flask.render_template(
        'benchmark.html',
        benchmark=benchmark,
        hl_lines=matching_lines,
        files=benchmark.get_files()
    )

if __name__ == "__main__":
    app.run(debug=True)
