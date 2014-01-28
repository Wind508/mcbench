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
                xpath varchar(500) not null unique
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

    def get_all_queries(self):
        return list(self._fetch('select * from query'))

    def get_saved_queries(self):
        return list(self._fetch("select * from query where name != ''"))

    def get_unsaved_queries(self):
        return list(self._fetch("select * from query where name = ''"))

    def get_query_results(self, xpath):
        query = self._fetchone('select * from query where xpath=?', (xpath,))
        if query is None:
            results = self.get_all_benchmarks().get_query_results(xpath)
            self.insert_query(xpath, results)
            return results
        else:
            return self.get_saved_query_results(query)

    def get_saved_query_results(self, query):
        result = QueryResult(cached=True, saved=bool(query['name']))
        for row in self._fetch(
            '''select B.id, author, author_url, date_submitted, date_updated,
                      name, summary, tags, title, url, num_matches
            from benchmark as B
            join query_results as R
            on B.id = R.benchmark_id
            where query_id=?''', (query['id'],)):
            benchmark = self._make_benchmark(
                {k: row[k] for k in row.keys() if k != 'num_matches'})
            result.add_matching_benchmark(benchmark, row['num_matches'])
        return result

    def insert_query(self, xpath, results):
        cursor = self.db.cursor()
        cursor.execute('insert into query(name, xpath) values(?, ?)', ('', xpath))
        query_id = cursor.lastrowid
        cursor.executemany('''insert into query_results
            (benchmark_id, query_id, num_matches) values (?, ?, ?)''',
            results.as_db_rows(query_id))
        self.db.commit()

    def save_query(self, xpath, name):
        cursor = self.db.cursor()
        cursor.execute('update query set name=? where xpath=?', (name, xpath))
        if cursor.rowcount != 1:
            raise QueryDoesNotExist
        self.db.commit()

    def unsave_query(self, xpath):
        query = self._fetchone('select * from query where xpath=?', (xpath,))
        if query is None:
            raise QueryDoesNotExist
        self.db.execute("update query set name='' where xpath=?", (xpath,))
        self.db.commit()
        return query

    def delete_query(self, xpath):
        query = self._fetchone('select * from query where xpath=?', (xpath,))
        if query is None:
            raise QueryDoesNotExist
        self.db.execute('delete from query where id=?', (query['id'],))
        self.db.execute('delete from query_results where query_id=?', (query['id'],))
        self.db.commit()
        return query


def create(data_root, db_path):
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return McBenchClient(db, data_root)
