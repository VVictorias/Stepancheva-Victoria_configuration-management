"""Ассемблер учебной виртуальной машины."""

import argparse
import sys
from pathlib import Path

from isa import COMMAND_SIZES, OP_BITS, OPCODES, OPERAND_MASKS

ARGUMENT_COUNT = 2


def parse_line(text, number):
    """Получить значения полей A и B из одной команды."""
    parts = text.split()
    name = parts[0].upper()
    opcode = OPCODES.get(name)
    if opcode is None:
        raise ValueError(f"строка {number}: неизвестная команда {parts[0]}")
    if len(parts) != ARGUMENT_COUNT:
        raise ValueError(f"строка {number}: для {name} нужен один аргумент")

    token = parts[1]
    base = 16 if token.lower().lstrip("+-").startswith("0x") else 10
    try:
        operand = int(token, base)
    except ValueError:
        raise ValueError(
            f"строка {number}: неверное число {token!r}"
        ) from None

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


def encode(opcode, operand):
    """Упаковать A и B в байты от младшего к старшему."""
    word = (operand << OP_BITS) | opcode
    return word.to_bytes(COMMAND_SIZES[opcode], "little")


def main():
    """Ассемблировать файл и вывести результат выбранного режима."""
    parser = argparse.ArgumentParser(description="Ассемблер УВМ, вариант 22")
    parser.add_argument("--input", type=Path, required=True, help="текст УВМ")
    parser.add_argument(
        "--output", type=Path, required=True, help="двоичный файл"
    )
    parser.add_argument(
        "--test", action="store_true", help="показать машинные байты"
    )
    parser.add_argument(
        "--ir", action="store_true", help="показать поля A и B"
    )
    args = parser.parse_args()
    try:
        commands = parse_program(args.input.read_text(encoding="utf-8"))
        chunks = [encode(opcode, operand) for opcode, operand in commands]
        args.output.write_bytes(b"".join(chunks))
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    if args.ir:
        for opcode, operand in commands:
            print(f"A={opcode}, B={operand}")
    if args.test:
        for chunk in chunks:
            print(", ".join(f"0x{byte:02X}" for byte in chunk))
    print(f"Ассемблировано команд: {len(commands)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
