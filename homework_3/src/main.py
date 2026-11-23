"""Разбор учебного конфигурационного языка, вариант 22."""

from pathlib import Path

from lark import Lark
from lark.exceptions import UnexpectedInput, UnexpectedToken

PARSER = Lark.open(
    "language.lark", rel_to=__file__, parser="lalr", maybe_placeholders=False
)


def parse(text):
    """Построить дерево разбора или сообщить место ошибки."""
    try:
        return PARSER.parse(text)
    except UnexpectedInput as error:
        if isinstance(error, UnexpectedToken) and error.token.type == "$END":
            line = text.count("\n") + 1
            column = len(text) - text.rfind("\n")
            detail = "неожиданный конец файла"
        else:
            line, column = error.line, error.column
            char = text[error.pos_in_stream]
            detail = f"неожиданный символ {char!r}"
        raise ValueError(
            f"строка {line}, столбец {column}: "
            f"синтаксическая ошибка ({detail})"
        ) from None
