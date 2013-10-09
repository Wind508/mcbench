import collections

import flask

import mcbench.client
import mcbench.highlighters
import mcbench.xpath
import settings

mcbench.xpath.register_extensions()

app = flask.Flask(__name__)
app.config.from_object(settings)
app.jinja_env.filters['highlight_matlab'] = mcbench.highlighters.matlab
app.jinja_env.filters['highlight_xml'] = mcbench.highlighters.xml

mcbench_client = mcbench.client.create_for_app(app)


def redirect(url_name, *args, **kwargs):
    return flask.redirect(flask.url_for(url_name, *args, **kwargs))


def get_compiled_query():
    query = flask.request.args.get('query') or None
    if query is None:
        return None
    return mcbench.xpath.compile_xpath(query)


@app.route('/', methods=['GET'])
def index():
    return flask.render_template('index.html')


@app.route('/list', methods=['GET'])
def benchmark_list():
    benchmarks = mcbench_client.get_all_benchmarks()
    try:
        query = get_compiled_query()
    except mcbench.xpath.XPathError as e:
        flask.flash('XPath error: %s' % e.message)
        return redirect('index')
    benchmarks = [b for b in benchmarks if b.matches(query)]
    return flask.render_template('list.html', benchmarks=benchmarks)


@app.route('/benchmark/<name>', methods=['GET'])
def benchmark(name):
    benchmark = mcbench_client.get_benchmark_by_name(name)
    try:
        query = get_compiled_query()
    except mcbench.xpath.XPathError as e:
        flask.flash('XPath error: %s' % e.message)
        return redirect('benchmark', name=name)

    files = list(benchmark.get_files())
    hl_lines = collections.defaultdict(lambda: {'m': [], 'xml': []})
    num_matches = 0
    for file in files:
        for match in file.get_matches(query):
            hl_lines[file.name]['m'].append(match.get('line'))
            hl_lines[file.name]['xml'].append(match.sourceline)
            num_matches += 1
    return flask.render_template(
        'benchmark.html',
        benchmark=benchmark,
        hl_lines=hl_lines,
        num_matches=num_matches,
        files=files,
    )

if __name__ == "__main__":
    app.run(debug=True)
