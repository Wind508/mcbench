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
    queries = get_client().get_saved_queries()
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

    start = time.time()
    try:
        result = client.get_query_results(query)
    except mcbench.xpath.XPathError as e:
        flask.flash(str(e), 'error')
        return redirect('index', query=e.query)
    elapsed_time = time.time() - start
    result.sort_by_frequency()

    return flask.render_template(
        'search.html',
        show_save_query_form=not result.saved,
        matches=result.matches,
        query=query,
        elapsed_time=elapsed_time,
        total_matches=result.total_matches,
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
    try:
        get_client().save_query(xpath, name)
        flask.flash("Query '%s' successfully saved." % name, 'info')
    except mcbench.client.QueryDoesNotExist:
        flask.flash('No such query exists!', 'error')
    return redirect('benchmark_list', query=xpath)


@app.route('/delete_query', methods=['POST'])
def delete_query():
    xpath = flask.request.values['xpath']
    try:
        query = get_client().unsave_query(xpath)
        flask.flash("Query '%s' successfully deleted." % query['name'], 'info')
    except mcbench.client.QueryDoesNotExist:
        flask.flash('No such query exists!', 'error')
    return redirect('index')

if __name__ == "__main__":
    app.run(debug=True)
