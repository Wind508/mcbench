import pygments.formatters
import pygments.lexers

HTML_FORMATTER = pygments.formatters.HtmlFormatter()
MATLAB_LEXER = pygments.lexers.MatlabLexer()
XML_LEXER = pygments.lexers.XmlLexer()


def matlab(code):
    return pygments.highlight(code, MATLAB_LEXER, HTML_FORMATTER)


def xml(code):
    return pygments.highlight(code, XML_LEXER, HTML_FORMATTER)
