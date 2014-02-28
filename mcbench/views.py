import time

import flask

import mcbench.xpath
from mcbench.models import Benchmark, Query
from mcbench import querier
from mcbench import app


def redirect(url_name, *args, **kwargs):
    return flask.redirect(flask.url_for(url_name, *args, **kwargs))


def get_valid_query_or_throw():
    xpath = flask.request.args.get('query') or None
    if xpath is None:
        return None
    mcbench.xpath.compile(xpath)
    return xpath


@app.route('/', methods=['GET'])
def index():
    return flask.render_template('index.html', queries=Query.saved())


@app.route('/help', methods=['GET'])
def help():
    return flask.render_template('help.html')


@app.route('/about', methods=['GET'])
def about():
    return flask.render_template('about.html')


@app.route('/list', methods=['GET'])
def benchmark_list():
    try:
        xpath = get_valid_query_or_throw()
    except mcbench.xpath.XPathError as e:
        flask.flash(str(e), 'error')
        return redirect('index', query=e.query)

    if xpath is None:
        benchmarks = list(Benchmark.all())
        return flask.render_template('list.html', benchmarks=benchmarks)

    start = time.time()
    try:
        matches = querier.get_matches(xpath)
    except mcbench.xpath.XPathError as e:
        flask.flash(str(e), 'error')
        return redirect('index', query=e.query)
    elapsed_time = time.time() - start

    return flask.render_template(
        'search.html',
        show_save_query_form=not Query.find_by_xpath(xpath).is_saved,
        matches=matches,
        query=xpath,
        elapsed_time=elapsed_time,
        total_matches=sum(m.num_matches for m in matches),
        total_benchmarks=Benchmark.count())


@app.route('/benchmark/<name>', methods=['GET'])
def benchmark(name):
    benchmark = Benchmark.find_by_name(name)

    try:
        query = get_valid_query_or_throw()
        hl_lines = querier.matching_lines(benchmark, query)
    except mcbench.xpath.XPathError as e:
        flask.flash(str(e), 'error')
        query = None
        hl_lines = querier.matching_lines(benchmark, None)

    num_matches = sum(len(v['m']) for v in hl_lines.values())

    return flask.render_template(
        'benchmark.html',
        benchmark=benchmark,
        files=list(benchmark.files),
        hl_lines=hl_lines,
        num_matches=num_matches,
    )


@app.route('/save_query', methods=['POST'])
def save_query():
    xpath = flask.request.values['xpath']
    name = flask.request.values['name']

    query = Query.find_by_xpath(xpath)
    if query is None:
        flask.flash('No such query exists!', 'error')
    else:
        query.name = name
        query.save()
        flask.flash("Query '%s' successfully saved." % name, 'info')
    return redirect('benchmark_list', query=xpath)


@app.route('/delete_query', methods=['POST'])
def delete_query():
    xpath = flask.request.values['xpath']

    query = Query.find_by_xpath(xpath)
    if query is None:
        flask.flash('No such query exists!', 'error')
    else:
        name = query.name
        query.unsave()
        flask.flash("Query '%s' successfully deleted." % name, 'info')
    return redirect('index')
