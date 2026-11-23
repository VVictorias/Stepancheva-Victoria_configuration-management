"""Разбор учебного конфигурационного языка, вариант 22."""

import argparse
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

import tomli_w
from lark import Lark, Transformer_NonRecursive, v_args
from lark.exceptions import UnexpectedInput, UnexpectedToken, VisitError

PARSER = Lark.open(
    "language.lark", rel_to=__file__, parser="lalr", maybe_placeholders=False
)
TOML_INT_MIN = -(2**63)
TOML_INT_MAX = 2**63 - 1


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


def integer_operands(left, right):
    """Проверить аргументы сложения и вычитания."""
    if not isinstance(left, int) or not isinstance(right, int):
        raise ValueError("для + и - нужны два целых числа")


def check_toml_value(value):
    """Проверить диапазон целых чисел в значении для TOML."""
    if isinstance(value, list):
        for item in value:
            check_toml_value(item)
    elif isinstance(value, int) and not TOML_INT_MIN <= value <= TOML_INT_MAX:
        raise ValueError("число вне диапазона 64-битного целого TOML")


@v_args(inline=True)
class Calculate(Transformer_NonRecursive):
    """Вычислить значения объявлений в порядке их записи."""

    def __init__(self):
        """Создать пустой словарь констант."""
        super().__init__()
        self.values = {}

    def number(self, token):
        """Преобразовать запись числа в целое."""
        try:
            return int(token)
        except ValueError:
            raise ValueError("слишком много цифр в числе") from None

    def string(self, token):
        """Убрать обрамление строки."""
        return token[2:-1]

    def array(self, *items):
        """Собрать элементы в список."""
        return list(items)

    def reference(self, name):
        """Получить значение ранее объявленной константы."""
        if name not in self.values:
            raise ValueError(
                f"строка {name.line}: неизвестная константа {str(name)!r}"
            )
        return self.values[name]

    def add(self, left, right):
        """Сложить два целых числа."""
        integer_operands(left, right)
        return left + right

    def subtract(self, left, right):
        """Вычесть второе целое число из первого."""
        integer_operands(left, right)
        return left - right

    def char_code(self, value):
        """Получить код Unicode одного символа."""
        if not isinstance(value, str) or len(value) != 1:
            raise ValueError("для ord нужна строка из одного символа")
        return ord(value)

    def declaration(self, value, name):
        """Сохранить значение под уникальным именем."""
        if name in self.values:
            raise ValueError(f"строка {name.line}: повтор имени {str(name)!r}")
        check_toml_value(value)
        self.values[str(name)] = value


def convert(text):
    """Разобрать исходный текст и получить словарь для TOML."""
    calculation = Calculate()
    try:
        calculation.transform(parse(text))
    except VisitError as error:
        if not isinstance(error.orig_exc, ValueError):
            raise
        raise error.orig_exc from None
    return calculation.values


def write_output(path, text):
    """Записать весь TOML перед заменой выходного файла."""
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as file:
        draft = Path(file.name)
        try:
            file.write(text)
            file.close()
            draft.replace(path)
        finally:
            draft.unlink(missing_ok=True)


def fail(message):
    """Напечатать сообщение об ошибке и вернуть код завершения."""
    print(f"Ошибка: {message}", file=sys.stderr)
    return 1


def main():
    """Прочитать входной файл и записать результат в TOML."""
    parser = argparse.ArgumentParser(
        description="Перевод учебного конфигурационного языка в TOML.",
        allow_abbrev=False,
    )
    parser.add_argument("--input", required=True, type=Path, help="файл ввода")
    parser.add_argument("--output", required=True, type=Path, help="файл TOML")
    args = parser.parse_args()

    try:
        source = args.input.expanduser().resolve()
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError, RuntimeError) as error:
        return fail(f"не удалось прочитать {str(args.input)!r}: {error}")

    try:
        result = tomli_w.dumps(convert(text))
    except ValueError as error:
        return fail(f"{args.input}: {error}")
    except RecursionError:
        return fail(f"{args.input}: слишком глубокая вложенность")

    try:
        output = args.output.expanduser().resolve()
        if output == source:
            return fail("пути к входному и выходному файлам совпадают")
        write_output(output, result)
    except (OSError, RuntimeError) as error:
        return fail(f"не удалось записать {str(args.output)!r}: {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
