import sys

import lxml.etree


class XPathError(Exception):
    pass


def parse_xml_from_file(filename):
    return lxml.etree.parse(filename)


def compile_xpath(query):
    try:
        return lxml.etree.XPath(query)
    except lxml.etree.XPathSyntaxError as e:
        raise XPathError(e.msg), None, sys.exc_info()[2]


def register_extensions():
    ns = lxml.etree.FunctionNamespace(None)
    ns['is_call'] = lambda c, n: is_call(c.context_node, n)


def is_call(node, name):
    return (node.tag == 'ParameterizedExpr' and
            node[0].tag == 'NameExpr' and
            node[0].get('kind') == 'FUN' and
            node[0][0].get('nameId') == name)
