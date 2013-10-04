import pygments.formatters
import pygments.lexers

MATLAB_LEXER = pygments.lexers.MatlabLexer()
XML_LEXER = pygments.lexers.XmlLexer()


def highlight(code, lexer, lines=None):
    if lines is None:
        lines = []
    formatter = pygments.formatters.HtmlFormatter(hl_lines=lines)
    return pygments.highlight(code, lexer, formatter)


def matlab(code, lines=None):
    return highlight(code, MATLAB_LEXER, lines)


def xml(code, lines=None):
    return highlight(code, XML_LEXER, lines)
