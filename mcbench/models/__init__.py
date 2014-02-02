import peewee

db = peewee.SqliteDatabase(None, threadlocals=True)


class Model(peewee.Model):
    class Meta:
        database = db

from .benchmark import Benchmark, File
from .query import Query, QueryMatch
