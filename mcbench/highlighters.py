import pygments.formatters
import pygments.lexers

MATLAB_LEXER = pygments.lexers.MatlabLexer()
XML_LEXER = pygments.lexers.XmlLexer()


def matlab(code, lines=None):
    if lines is None:
        lines = []
    formatter = pygments.formatters.HtmlFormatter(hl_lines=lines)
    return pygments.highlight(code, MATLAB_LEXER, formatter)


def xml(code):
    formatter = pygments.formatters.HtmlFormatter()
    return pygments.highlight(code, XML_LEXER, formatter)
