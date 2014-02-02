import os

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
    def files(self):
        root = os.path.join(settings.DATA_ROOT, self.name)
        for dirpath, _, files in os.walk(root):
            for file in files:
                base, ext = os.path.splitext(file)
                if ext == '.m':
                    yield File(dirpath, base)


def fix_utf8(s):
    encoding = chardet.detect(s)['encoding']
    try:
        return unicode(s.decode(encoding))
    except UnicodeDecodeError:
        # chardet seems to get the 2224-cost231-models files wrong;
        # it says windows-1255 but they're actually latin1 (according to vim).
        # This is an ugly workaround for this case.
        if encoding != 'windows-1255':
            raise
        return unicode(s.decode('latin1'))


class File(object):
    def __init__(self, root, name):
        self.root = root
        self.name = name

    @property
    def matlab_path(self):
        return os.path.join(self.root, '%s.m' % self.name)

    @property
    def xml_path(self):
        return os.path.join(self.root, '%s.xml' % self.name)

    def read_matlab(self):
        with open(self.matlab_path) as f:
            return fix_utf8(f.read())

    def read_xml(self):
        with open(self.xml_path) as f:
            return f.read()
