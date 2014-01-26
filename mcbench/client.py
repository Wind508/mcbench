import itertools
import sqlite3

from mcbench.benchmark import Benchmark, BenchmarkSet
from mcbench.query import QueryResult


class BenchmarkDoesNotExist(Exception):
    pass


class BenchmarkAlreadyExists(Exception):
    pass


class QueryDoesNotExist(Exception):
    pass


class McBenchClient(object):
    def __init__(self, db, data_root):
        self.db = db
        self.data_root = data_root

    def close(self):
        self.db.close()

    def init_tables(self):
        self.db.executescript('''
            create table if not exists benchmark (
                id integer not null primary key autoincrement,
                author varchar(200) not null,
                author_url varchar(200) not null,
                date_submitted datetime not null,
                date_updated datetime not null,
                name varchar(200) unique not null,
                summary varchar(500) not null,
                tags varchar(1000) not null,
                title varchar(500) not null,
                url varchar(200) not null
            );

            create table if not exists query (
                id integer not null primary key autoincrement,
                name varchar(200) not null,
                xpath varchar(500) not null
            );

            create table if not exists query_results (
                id integer not null primary key autoincrement,
                benchmark_id integer not null references benchmark (id),
                query_id integer not null references query (id),
                num_matches integer not null,
                unique (benchmark_id, query_id)
            );
         ''')

    def _fetch(self, query, params=()):
        cursor = self.db.cursor()
        cursor.execute(query, params)
        return cursor

    def _fetchone(self, query, params=()):
        return self._fetch(query, params).fetchone()

    def _make_benchmark(self, data):
        if data is None:
            raise BenchmarkDoesNotExist
        data = dict(
            data, author=data['author'], summary=data['summary'],
            tags=data['tags'].split(','), title=data['title'])
        return Benchmark(data['id'], self.data_root, data=data)

    def get_benchmark_by_id(self, benchmark_id):
        benchmark = self._fetchone(
            'select * from benchmark where id=?', (benchmark_id,))
        return self._make_benchmark(benchmark)

    def get_benchmark_by_name(self, name):
        benchmark = self._fetchone(
            'select * from benchmark where name=?', (name,))
        return self._make_benchmark(benchmark)

    def _benchmark_exists(self, name):
        try:
            self.get_benchmark_by_name(name)
            return True
        except BenchmarkDoesNotExist:
            return False

    def get_all_benchmarks(self):
        return BenchmarkSet(self.data_root, itertools.imap(
            self._make_benchmark, self._fetch('select * from benchmark')))

    def insert_benchmark(self, data):
        if self._benchmark_exists(data['name']):
            raise BenchmarkAlreadyExists
        params = (data['author'], data['author_url'], data['date_submitted'],
                  data['date_updated'], data['name'], data['summary'],
                  ','.join(data['tags']), data['title'], data['url'])
        self.db.execute('''insert into benchmark (author, author_url,
            date_submitted, date_updated, name, summary, tags, title, url)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)''', params)
        self.db.commit()

    def get_query_by_id(self, query_id):
        query = self._fetchone('select * from query where id=?', (query_id,))
        if query is None:
            raise QueryDoesNotExist
        return query

    def get_all_queries(self):
        return list(self._fetch('select * from query'))

    def get_query_results(self, xpath):
        query = self._fetchone('select * from query where xpath=?', (xpath,))
        if query is None:
            return self.get_all_benchmarks().get_query_results(xpath)
        else:
            return self.get_saved_query_results(query['id'])

    def get_saved_query_results(self, query_id):
        result = QueryResult(cached=True)
        for row in self._fetch(
            '''select B.id, author, author_url, date_submitted, date_updated,
                      name, summary, tags, title, url, num_matches
            from benchmark as B
            join query_results as R
            on B.id = R.benchmark_id
            where query_id=?''', (query_id,)):
            benchmark = self._make_benchmark(
                {k: row[k] for k in row.keys() if k != 'num_matches'})
            result.add_matching_benchmark(benchmark, row['num_matches'])
        return result

    def insert_query(self, xpath, name):
        cursor = self.db.cursor()
        cursor.execute(
            'insert into query (name, xpath) values(?, ?)', (name, xpath))
        self.db.commit()
        return cursor.lastrowid

    def set_query_results(self, query_id, results):
        cursor = self.db.cursor()
        cursor.execute('delete from query_results where query_id=?', (query_id,))
        cursor.executemany('''insert into query_results
            (benchmark_id, query_id, num_matches) values (?, ?, ?)''',
            results.as_db_rows())
        self.db.commit()

    # TODO(isbadawi): Get rid of this.
    # (Could directly convert string to QueryResult, but that needs a list of
    # benchmark objects, not ids.)
    def set_query_results_from_client_string(self, query_id, string):
        def make_row(part):
            return (part.split(':')[0], query_id, part.split(':')[1])
        cursor = self.db.cursor()
        cursor.execute('delete from query_results where query_id=?', (query_id,))
        cursor.executemany('''insert into query_results
            (benchmark_id, query_id, num_matches) values (?, ?, ?)''',
            itertools.imap(make_row, string.split(',')))
        self.db.commit()

    def delete_query(self, query_id):
        self.db.execute('delete from query where id=?', (query_id,))
        self.db.execute('delete from query_results where query_id=?', (query_id,))
        self.db.commit()


def create(data_root, db_path):
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return McBenchClient(db, data_root)
