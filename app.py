import time

import flask

import mcbench.client
import mcbench.highlighters
import mcbench.xpath

mcbench.xpath.register_extensions()

app = flask.Flask(__name__)
app.config.from_object('settings')
app.jinja_env.filters['highlight_matlab'] = mcbench.highlighters.matlab
app.jinja_env.filters['highlight_xml'] = mcbench.highlighters.xml
app.jinja_env.filters['pluralize'] = lambda n, s='s': s if n != 1 else ''

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


def redirect(url_name, *args, **kwargs):
    return flask.redirect(flask.url_for(url_name, *args, **kwargs))


def get_valid_query_or_throw():
    query = flask.request.args.get('query') or None
    if query is None:
        return None
    mcbench.xpath.compile(query)
    return query


@app.route('/', methods=['GET'])
def index():
    queries = mcbench_client.get_all_queries()
    return flask.render_template(
        'index.html', examples=EXAMPLE_QUERIES, queries=queries)


@app.route('/help', methods=['GET'])
def help():
    return flask.render_template('help.html')


@app.route('/list', methods=['GET'])
def benchmark_list():
    try:
        query = get_valid_query_or_throw()
    except mcbench.xpath.XPathError as e:
        flask.flash(str(e), 'error')
        return redirect('index', query=e.query)

    all_benchmarks = mcbench_client.get_all_benchmarks()

    if query is None:
        return flask.render_template('list.html', benchmarks=all_benchmarks)

    start = time.time()
    try:
        benchmarks, matches_by_benchmark, num_matches = (
            all_benchmarks.get_num_matches(query))
    except mcbench.xpath.XPathError as e:
        flask.flash(str(e), 'error')
        return redirect('index', query=e.query)

    elapsed_time = time.time() - start
    benchmarks.sort(key=lambda b: matches_by_benchmark[b.name], reverse=True)

    return flask.render_template(
        'list.html',
        benchmarks=benchmarks,
        elapsed_time=elapsed_time,
        matches_by_benchmark=matches_by_benchmark,
        num_matches=num_matches)


@app.route('/benchmark/<name>', methods=['GET'])
def benchmark(name):
    benchmark = mcbench_client.get_benchmark_by_name(name)

    try:
        query = get_valid_query_or_throw()
        hl_lines = benchmark.get_matching_lines(query)
    except mcbench.xpath.XPathError as e:
        flask.flash(str(e), 'error')
        query = None
        hl_lines = benchmark.get_matching_lines(None)

    files = list(benchmark.get_files())
    num_matches = sum(len(v['m']) for v in hl_lines.values())

    return flask.render_template(
        'benchmark.html',
        benchmark=benchmark,
        hl_lines=hl_lines,
        num_matches=num_matches,
        files=files,
    )

@app.route('/save_query', methods=['POST'])
def save_query():
    xpath = flask.request.values['xpath']
    name = flask.request.values['name']
    mcbench_client.insert_query(xpath, name)
    flask.flash("Query '%s' successfully saved." % name, 'info')
    return redirect('index')

@app.route('/delete_query', methods=['POST'])
def delete_query():
    query_id = flask.request.values['id']
    query = mcbench_client.get_query_by_id(query_id)
    mcbench_client.delete_query(query_id)
    flask.flash("Query '%s' successfully deleted." % query.name, 'info')
    return redirect('index')

if __name__ == "__main__":
    app.run(debug=True)
