"""
Babel extractor for the gettext() / ngettext() calls in app/static.

Babel ships a JavaScript extractor, but on this code base it silently drops
strings: a ${gettext('…')} between a pair of quotes in a template literal's
text (every HTML attribute), a call whose params object sits inside ${…}, a
gettext() nested in another call's arguments, and everything after a regex
such as /"/g once its lexer has read a /> as a JSX tag. This one scans the
source for the calls themselves, so a string is extracted wherever it is
written; lines that are only a comment are skipped.

Wired up through the [extractors] section of babel.cfg. pybabel imports it
from the working directory, hence ``PYTHONPATH=. pybabel extract …``.
"""

import re

_STRING = r"""'(?:[^'\\\n]|\\.)*'|"(?:[^"\\\n]|\\.)*\""""
_CALL = re.compile(
    r"\b(?P<name>\w+)\(\s*(?P<first>%(s)s)(?:\s*,\s*(?P<second>%(s)s))?" % {"s": _STRING}
)
_COMMENT_LINE = re.compile(r"^\s*(//|/?\*)")
_ESCAPE = re.compile(r"\\(?:u\{(?P<brace>[0-9a-fA-F]+)\}|u(?P<u4>[0-9a-fA-F]{4})|x(?P<x2>[0-9a-fA-F]{2})|(?P<char>.|\n))", re.S)
_SIMPLE_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v", "0": "\0", "\n": ""}


def _unquote(literal):
    def replace(match):
        code = match.group("brace") or match.group("u4") or match.group("x2")
        if code:
            return chr(int(code, 16))
        char = match.group("char")
        return _SIMPLE_ESCAPES.get(char, char)

    return _ESCAPE.sub(replace, literal[1:-1])


def extract(fileobj, keywords, comment_tags, options):
    """Yield ``(lineno, funcname, messages, comments)``; Babel applies the keyword specs."""
    source = fileobj.read().decode(options.get("encoding", "utf-8"))
    for lineno, line in enumerate(source.splitlines(), 1):
        if _COMMENT_LINE.match(line):
            continue
        for match in _CALL.finditer(line):
            name = match.group("name")
            if name not in keywords:
                continue
            messages = [_unquote(match.group("first"))]
            if match.group("second"):
                messages.append(_unquote(match.group("second")))
            yield lineno, name, messages, []
