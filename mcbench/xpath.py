import sys

import lxml.etree


class XPathError(Exception):
    pass


def parse_xml_filename(filename):
    return lxml.etree.parse(filename)


def compile_xpath(query):
    try:
        return lxml.etree.XPath(query)
    except lxml.etree.XPathSyntaxError as e:
        raise XPathError(e.msg), None, sys.exc_info()[2]


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
