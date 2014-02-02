import peewee

db = peewee.SqliteDatabase(None)


class Model(peewee.Model):
    class Meta:
        database = db

from .benchmark import Benchmark, File
from .query import Query, QueryMatch
