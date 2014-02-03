import peewee

from . import db, Model, Benchmark


class Query(Model):
    name = peewee.CharField()
    xpath = peewee.CharField(unique=True)

    @staticmethod
    def all():
        return Query.select()

    @staticmethod
    def saved():
        return Query.select().where(Query.name != '')

    @staticmethod
    def unsaved():
        return Query.select().where(Query.name == '')

    @staticmethod
    def find_by_xpath(xpath):
        return Query.select().where(Query.xpath == xpath).first()

    @property
    def is_saved(self):
        return self.name != ''

    def unsave(self):
        self.name = ''
        self.save()

    def expire_matches(self):
        QueryMatch.delete().where(QueryMatch.query == self).execute()

    def cache_matches(self, matches):
        db.set_autocommit(False)
        for benchmark, num_matches in matches:
            QueryMatch.create(query=self,
                              benchmark=benchmark,
                              num_matches=num_matches)
        db.commit()
        db.set_autocommit(True)

    def get_cached_matches(self):
        return list(self.querymatch_set.order_by(
            QueryMatch.num_matches.desc()))


class QueryMatch(Model):
    benchmark = peewee.ForeignKeyField(Benchmark, on_delete='CASCADE')
    query = peewee.ForeignKeyField(Query, on_delete='CASCADE')
    num_matches = peewee.IntegerField()
