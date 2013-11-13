import functools
import sys

import lxml.etree


class XPathError(Exception):
    def __init__(self, query, cause):
        self.query = query
        self.cause = cause
        super(XPathError, self).__init__(query, cause)

    def __str__(self):
        return '%s: %s' % (self.cause.__class__.__name__, str(self.cause))


class XPathQuery(object):
    def __init__(self, query, compiled_query):
        self.query = query
        self.compiled_query = compiled_query

    def __call__(self, xml):
        try:
            return self.compiled_query(xml)
        except (lxml.etree.XPathError, UnexpectedContext) as e:
            raise XPathError(self.query, e), None, sys.exc_info()[2]


def parse_xml_filename(filename):
    return lxml.etree.parse(filename)


def compile(query):
    try:
        return XPathQuery(query, lxml.etree.XPath(query))
    except lxml.etree.XPathError as e:
        raise XPathError(query, e), None, sys.exc_info()[2]


class UnexpectedContext(Exception):
    def __init__(self, f, context, tags):
        self.f = f
        self.context = context
        self.expected = tags
        super(UnexpectedContext, self).__init__(f, context, tags)

    def __str__(self):
        return '%s called in %s context, expecting any of %s' % (
            self.f, self.context, ', '.join(self.expected))


def expect(*nodes):
    def decorator(f):
        @functools.wraps(f)
        def helper(context, *args):
            node = context.context_node
            if node.tag not in nodes:
                raise UnexpectedContext(f.__name__, node.tag, nodes)
            return f(context, *args)
        return helper
    return decorator


@expect('ParameterizedExpr')
def is_call(context, *names):
    node = context.context_node
    if node[0].tag != 'NameExpr' or node[0].get('kind') != 'FUN':
        return False
    # no-arg is_call() returns whether this is a call to any function
    if not names:
        return True

    called_name = node[0][0].get('nameId')

    # Could call this function like
    # is_call('eval') -> names is a string
    if isinstance(names, basestring):
        return called_name == names
    # is_call('eval', 'feval') -> names is a tuple of strings
    # is_call(//some/sequence) -> names[0] is a list of strings
    names = names[0] if isinstance(names[0], list) else names
    return any(called_name == name for name in names)


@expect('ParameterizedExpr', 'CellIndexExpr')
def num_args(context):
    return len(context.context_node) - 1


@expect('ParameterizedExpr', 'CellIndexExpr')
def arg(context, index):
    return context.context_node[int(index)]


@expect('AssignStmt')
def lhs(context):
    return context.context_node[0]


@expect('AssignStmt')
def rhs(context):
    return context.context_node[1]


@expect('CellIndexExpr', 'DotExpr', 'ParameterizedExpr')
def target(context):
    return context.context_node[0]


def register_extensions():
    ns = lxml.etree.FunctionNamespace(None)
    ns['is_call'] = is_call
    ns['num_args'] = num_args
    ns['arg'] = arg
    ns['lhs'] = lhs
    ns['rhs'] = rhs
    ns['target'] = target
