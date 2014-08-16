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

    def execute(self, xml):
        try:
            return self.compiled_query(xml)
        except (lxml.etree.XPathError, UnexpectedContext) as e:
            raise XPathError(self.query, e) from e


def parse_xml(xml):
    return lxml.etree.XML(xml)


def parse_xml_filename(filename):
    return lxml.etree.parse(filename)


def compile(query):
    try:
        return XPathQuery(query, lxml.etree.XPath(query))
    except lxml.etree.XPathError as e:
        raise XPathError(query, e) from e


class UnexpectedContext(Exception):
    def __init__(self, f, context, tags):
        self.f = f
        self.context = context
        self.expected = tags
        super(UnexpectedContext, self).__init__(f, context, tags)

    def __str__(self):
        return '%s called in %s context, expecting any of %s' % (
            self.f, self.context, ', '.join(self.expected))

ns = lxml.etree.FunctionNamespace(None)


def extension(*nodes):
    """Decorator to register a function as an xpath extension.

    The optional nodes parameters are strings indicating the XML tags which
    are valid context for this function. The function will automatically check
    that the context is valid, throwing an UnexpectedContext exception if not.
    """
    def decorator(f, nodes=nodes):
        @functools.wraps(f)
        def wrapper(context, *args):
            node = context.context_node
            if nodes is not None and node.tag not in nodes:
                raise UnexpectedContext(f.__name__, node.tag, nodes)
            return f(context, *args)
        # This is the bit that does the registering.
        ns[f.__name__] = wrapper
        return wrapper

    # Trick to allow writing @extension instead of @extension():
    if len(nodes) == 1 and callable(nodes[0]):
        # If the first argument is a function, then this function (extension)
        # has to act as the decorator.
        return decorator(nodes[0], None)
    return decorator


@extension('ParameterizedExpr')
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
    if isinstance(names, str):
        return called_name == names
    # is_call('eval', 'feval') -> names is a tuple of strings
    # is_call(//some/sequence) -> names[0] is a list of strings
    names = names[0] if isinstance(names[0], list) else names
    return any(called_name == name for name in names)


@extension('ParameterizedExpr', 'CellIndexExpr')
def num_args(context):
    return len(context.context_node) - 1


@extension('ParameterizedExpr', 'CellIndexExpr')
def arg(context, index):
    return context.context_node[int(index)]


@extension('AssignStmt')
def lhs(context):
    return context.context_node[0]


@extension('AssignStmt')
def rhs(context):
    return context.context_node[1]


@extension('CellIndexExpr', 'DotExpr', 'ParameterizedExpr')
def target(context):
    return context.context_node[0]


@extension
def loopvars(context):
    node = context.context_node
    loop_vars = []
    while node is not None:
        if node.tag == 'ForStmt':
            loop_vars.append(node[0][0][0].get('nameId'))
        node = node.getparent()
    return loop_vars


@extension
def is_stmt(context):
    return context.context_node.tag.endswith('Stmt')


@extension
def is_expr(context):
    return context.context_node.tag.endswith('Expr')
