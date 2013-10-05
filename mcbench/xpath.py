import lxml.etree


def register_extensions():
    ns = lxml.etree.FunctionNamespace(None)
    ns['is_call'] = lambda c, n: is_call(c.context_node, n)


def is_call(node, name):
    return (node.tag == 'ParameterizedExpr' and
        node[0].tag == 'NameExpr' and
        node[0].get('kind') == 'FUN' and
        node[0][0].get('nameId') == name)
