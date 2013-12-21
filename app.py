import time

import flask

import mcbench.client
import mcbench.highlighters
import mcbench.xpath

app = flask.Flask(__name__)
app.config.from_object('settings')
app.jinja_env.filters['highlight_matlab'] = mcbench.highlighters.matlab
app.jinja_env.filters['highlight_xml'] = mcbench.highlighters.xml


def get_client():
    client = flask.g.get('client', None)
    if client is None:
        flask.g.client = client = mcbench.client.create(
            app.config['DATA_ROOT'], app.config['DB_PATH'])
    return client


@app.teardown_appcontext
def teardown_client(exception):
    client = flask.g.get('client', None)
    if client is not None:
        client.close()


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
    queries = get_client().get_all_queries()
    return flask.render_template('index.html', queries=queries)


@app.route('/help', methods=['GET'])
def help():
    return flask.render_template('help.html')


@app.route('/about', methods=['GET'])
def about():
    return flask.render_template('about.html')


@app.route('/list', methods=['GET'])
def benchmark_list():
    try:
        query = get_valid_query_or_throw()
    except mcbench.xpath.XPathError as e:
        flask.flash(str(e), 'error')
        return redirect('index', query=e.query)

    client = get_client()
    all_benchmarks = client.get_all_benchmarks()

    if query is None:
        return flask.render_template('list.html', benchmarks=all_benchmarks)

    saved_query = flask.request.args.get('query_id') or None
    start = time.time()
    if saved_query is not None:
        benchmarks, matches_by_benchmark, num_matches = (
            client.get_saved_query_results(saved_query))
    else:
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
        num_matches=num_matches,
        total_benchmarks=len(all_benchmarks))


@app.route('/benchmark/<name>', methods=['GET'])
def benchmark(name):
    benchmark = get_client().get_benchmark_by_name(name)

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
    results = flask.request.values['results']
    client = get_client()
    query_id = client.insert_query(xpath, name)
    client.set_query_results(query_id, results)
    flask.flash("Query '%s' successfully saved." % name, 'info')
    return redirect('benchmark_list', query=xpath, query_id=query_id)


@app.route('/delete_query', methods=['POST'])
def delete_query():
    client = get_client()
    query_id = flask.request.values['id']
    query = client.get_query_by_id(query_id)
    client.delete_query(query_id)
    flask.flash("Query '%s' successfully deleted." % query['name'], 'info')
    return redirect('index')

if __name__ == "__main__":
    app.run(debug=True)
