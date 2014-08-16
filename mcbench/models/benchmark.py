import pathlib

import chardet
import peewee

from mcbench import settings
from mcbench.models import Model


class Benchmark(Model):
    author = peewee.CharField()
    author_url = peewee.CharField()
    date_submitted = peewee.DateField()
    date_updated = peewee.DateField()
    name = peewee.CharField(unique=True)
    summary = peewee.TextField()
    tags = peewee.CharField()
    title = peewee.CharField()
    url = peewee.CharField()

    @staticmethod
    def all():
        return Benchmark.select()

    @staticmethod
    def count():
        return Benchmark.select().count()

    @staticmethod
    def find_by_name(name):
        return Benchmark.select().where(Benchmark.name == name).first()

    @property
    def root(self):
        return pathlib.Path(settings.DATA_ROOT, self.name)

    @property
    def files(self):
        for path in self.root.glob('**/*.m'):
            yield File(path.with_name(path.stem))


def fix_utf8(s):
    encoding = chardet.detect(s)['encoding']
    try:
        return str(s.decode(encoding))
    except UnicodeDecodeError:
        # chardet seems to get the 2224-cost231-models files wrong;
        # it says windows-1255 but they're actually latin1 (according to vim).
        # This is an ugly workaround for this case.
        if encoding != 'windows-1255':
            raise
        return str(s.decode('latin1'))


class File(object):
    def __init__(self, path):
        self.path = path
        self.name = self.path.name
        self.matlab_path = self.path.with_suffix('.m')
        self.xml_path = self.path.with_suffix('.xml')

    def read_matlab(self):
        with self.matlab_path.open('rb') as f:
            return fix_utf8(f.read())

    def read_xml(self):
        with self.xml_path.open() as f:
            return f.read()
