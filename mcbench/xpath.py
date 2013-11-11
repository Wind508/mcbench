import sys

import lxml.etree


class XPathError(Exception):
    def __init__(self, query, cause):
        self.query = query
        self.cause = cause
        super(XPathError, self).__init__(query, cause)

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

    # Could call this function like
    # is_call('eval') -> names is a string
    if isinstance(names, basestring):
        return called_name == names
    # is_call('eval', 'feval') -> names is a tuple of strings
    # is_call(//some/sequence) -> names[0] is a list of strings
    names = names[0] if isinstance(names[0], list) else names
    return any(called_name == name for name in names)
