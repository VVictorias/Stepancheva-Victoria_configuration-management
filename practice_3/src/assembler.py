"""Разбор программ учебной виртуальной машины."""

import argparse
import sys
from pathlib import Path

from isa import OPCODES, OPERAND_MASKS

ARGUMENT_COUNT = 2


def parse_line(text, number):
    """Получить значения полей A и B из одной команды."""
    parts = text.split()
    name = parts[0].upper()
    if name not in OPCODES:
        raise ValueError(f"строка {number}: неизвестная команда {parts[0]}")
    if len(parts) != ARGUMENT_COUNT:
        raise ValueError(f"строка {number}: для {name} нужен один аргумент")

    token = parts[1]
    base = 16 if token.lower().lstrip("+-").startswith("0x") else 10
    try:
        operand = int(token, base)
    except ValueError:
        raise ValueError(f"строка {number}: неверное число {token!r}") from None

    opcode = OPCODES[name]
    limit = OPERAND_MASKS[opcode]
    if not 0 <= operand <= limit:
        raise ValueError(f"строка {number}: аргумент {name} вне 0..{limit}")
    return opcode, operand


def parse_program(source):
    """Прочитать все команды, пропуская пустые строки и комментарии."""
    commands = []
    for number, line in enumerate(source.splitlines(), start=1):
        text = line.partition("#")[0].strip()
        if text:
            commands.append(parse_line(text, number))
    return commands


def show_ir(commands):
    """Вывести значения полей в том же виде, что и в методичке."""
    for opcode, operand in commands:
        print(f"A={opcode}, B={operand}")


def main():
    """Прочитать текстовый файл и запустить разбор."""
    parser = argparse.ArgumentParser(description="Ассемблер УВМ, вариант 22")
    parser.add_argument("--input", type=Path, required=True, help="текст УВМ")
    parser.add_argument("--output", type=Path, required=True, help="выходной файл")
    parser.add_argument("--test", action="store_true", help="показать поля A и B")
    args = parser.parse_args()
    try:
        commands = parse_program(args.input.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    if args.test:
        show_ir(commands)
    return 0


if __name__ == "__main__":
    sys.exit(main())
