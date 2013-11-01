import sys

import lxml.etree


class XPathError(Exception):
    def __init__(self, query, cause):
        super(XPathError, self).__init__()
        self.query = query
        self.cause = cause

    def __str__(self):
        return '%s: %s' % (self.cause.__class__.__name__, self.cause.message)


class XPathQuery(object):
    def __init__(self, query, compiled_query):
        self.query = query
        self.compiled_query = compiled_query

    def __call__(self, xml):
        try:
            return self.compiled_query(xml)
        except lxml.etree.XPathError as e:
            raise XPathError(self.query, e), None, sys.exc_info()[2]


def parse_xml_filename(filename):
    return lxml.etree.parse(filename)


def compile(query):
    try:
        return XPathQuery(query, lxml.etree.XPath(query))
    except lxml.etree.XPathError as e:
        raise XPathError(query, e), None, sys.exc_info()[2]


def register_extensions():
    ns = lxml.etree.FunctionNamespace(None)
    ns['is_call'] = is_call


def is_call(context, *names):
    node = context.context_node
    if node.tag != 'ParameterizedExpr':
        return False
    if node[0].tag != 'NameExpr' or node[0].get('kind') != 'FUN':
        return False

    called_name = node[0][0].get('nameId')

    # Could this function like
    # is_call('eval', 'feval') -> names is a tuple of strings
    # is_call(//some/sequence) -> names[0] is a list of strings
    for name in names:
        if isinstance(name, basestring) and called_name == name:
            return True
        elif any(called_name == n for n in name):
            return True
    return False
