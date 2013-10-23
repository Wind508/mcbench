import collections

import flask

import mcbench.client
import mcbench.highlighters
import mcbench.xpath

EXAMPLE_QUERIES = (
    ('Calls to eval', "//ParameterizedExpr[is_call('eval')]"),
    ('Calls to feval with a string literal target',
     "//ParameterizedExpr[is_call('feval') and ./*[position()=2 and name(.)='StringLiteralExpr']]"),
    ('Copy statements inside loops', "//ForStmt//AssignStmt[./*[position()=1 and name(.)='NameExpr'] and ./*[position()=2 and name(.)='NameExpr' and ./@kind='VAR']]"),
    ('Recursive calls', '//ParameterizedExpr[is_call(ancestor::Function/@name)]'),
)

mcbench.xpath.register_extensions()

app = flask.Flask(__name__)
app.config.from_object('settings')
app.jinja_env.filters['highlight_matlab'] = mcbench.highlighters.matlab
app.jinja_env.filters['highlight_xml'] = mcbench.highlighters.xml
app.jinja_env.filters['pluralize'] = lambda n, s='s': s if n != 1 else ''

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
    return flask.render_template('index.html', examples=EXAMPLE_QUERIES)


@app.route('/list', methods=['GET'])
def benchmark_list():
    try:
        query = get_compiled_query()
    except mcbench.xpath.XPathError as e:
        flask.flash('XPath error: %s' % e.message)
        return redirect('index')

    if query is None:
        return flask.render_template(
            'list.html', benchmarks=mcbench_client.get_all_benchmarks())

    benchmarks = []
    matches_by_benchmark = collections.defaultdict(int)
    num_matches = 0
    for benchmark in mcbench_client.get_all_benchmarks():
        matches = benchmark.get_num_matches(query)
        if matches:
            benchmarks.append(benchmark)
            matches_by_benchmark[benchmark.name] += matches
            num_matches += matches
    benchmarks.sort(key=lambda b: matches_by_benchmark[b.name], reverse=True)

    return flask.render_template(
        'list.html',
        benchmarks=benchmarks,
        matches_by_benchmark=matches_by_benchmark,
        num_matches=num_matches)


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
    if query is not None:
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
