import mcbench.xpath

from nose.tools import eq_, assert_raises


def test_compiling_malformed_query_raises_error():
    with assert_raises(mcbench.xpath.XPathError):
        mcbench.xpath.compile(r'\\ForStmt')


def test_eval_error_in_query_raises_error():
    query = mcbench.xpath.compile('//ForStmt[badpredicate()]')
    xml = mcbench.xpath.parse_xml('<ForStmt></ForStmt>')
    with assert_raises(mcbench.xpath.XPathError):
        query.execute(xml)


def test_extension_functions_can_be_called_and_work():
    @mcbench.xpath.extension
    def always_true(context):
        return True

    @mcbench.xpath.extension
    def always_false(context):
        return False

    true_query = mcbench.xpath.compile('//ForStmt[always_true()]')
    false_query = mcbench.xpath.compile('//ForStmt[always_false()]')
    xml = mcbench.xpath.parse_xml('<ForStmt></ForStmt>')
    eq_(1, len(true_query.execute(xml)))
    eq_(0, len(false_query.execute(xml)))


def test_unexpected_context_for_extension_function_raises_error():
    @mcbench.xpath.extension('AssignStmt')
    def expects_assignment(context):
        return True

    query = mcbench.xpath.compile('//ForStmt[expects_assignment()]')
    xml = mcbench.xpath.parse_xml('<ForStmt></ForStmt>')
    with assert_raises(mcbench.xpath.XPathError):
        query.execute(xml)
