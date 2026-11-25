"""Выполнение машинного кода и сохранение памяти УВМ."""

import argparse
import sys
import xml.etree.ElementTree as et
from pathlib import Path

from isa import (
    ADDRESS_MASK,
    COMMAND_SIZES,
    OP_BITS,
    OP_BSWAP,
    OP_LOAD,
    OP_MASK,
    OP_READ,
    OP_STORE,
    OPERAND_MASKS,
)

WORD_SIZE = 4
MEMORY_SIZE = (ADDRESS_MASK + 1) * WORD_SIZE


def decode(memory, pc, end):
    """Извлечь поля A и B и размер команды из общей памяти."""
    opcode = memory[pc] & OP_MASK
    if opcode not in COMMAND_SIZES:
        raise ValueError(f"байт {pc}: неизвестный код операции {opcode}")
    size = COMMAND_SIZES[opcode]
    if pc + size > end:
        raise ValueError(f"байт {pc}: неполная команда")
    word = int.from_bytes(memory[pc:pc + size], "little")
    operand = word >> OP_BITS
    if operand > OPERAND_MASKS[opcode]:
        raise ValueError(f"байт {pc}: ненулевые биты за полем B")
    return opcode, operand, size


def word_offset(address):
    """Перевести адрес слова в индекс его первого байта."""
    if not 0 <= address <= ADDRESS_MASK:
        raise ValueError(f"адрес {address} вне 0..{ADDRESS_MASK}")
    return address * WORD_SIZE


def read_word(memory, address):
    """Прочитать 32-битное слово из общей памяти."""
    start = word_offset(address)
    return int.from_bytes(memory[start:start + WORD_SIZE], "little")


def write_word(memory, address, value):
    """Записать 32-битное слово в общую память."""
    start = word_offset(address)
    memory[start:start + WORD_SIZE] = value.to_bytes(WORD_SIZE, "little")


def bswap(value):
    """Развернуть четыре байта беззнакового слова."""
    return int.from_bytes(value.to_bytes(WORD_SIZE, "little"), "big")


def run_program(binary):
    """Загрузить машинный код по адресу 0 и выполнить его до конца."""
    end = len(binary)
    if end > MEMORY_SIZE:
        raise ValueError(f"программа превышает {MEMORY_SIZE} байт")
    memory = bytearray(MEMORY_SIZE)
    memory[:end] = binary
    pc = 0
    accumulator = 0
    while pc < end:
        opcode, operand, size = decode(memory, pc, end)
        if opcode == OP_LOAD:
            accumulator = operand
        elif opcode == OP_READ:
            accumulator = read_word(memory, accumulator + operand)
        elif opcode == OP_STORE:
            write_word(memory, operand, accumulator)
        elif opcode == OP_BSWAP:
            accumulator = bswap(read_word(memory, operand))
        pc += size
    return memory


def dump_memory(memory, addresses, path):
    """Сохранить адрес и десятичное значение каждого слова в XML."""
    root = et.Element("memory")
    for address in addresses:
        cell = et.SubElement(root, "cell", address=str(address))
        cell.text = str(read_word(memory, address))
    tree = et.ElementTree(root)
    et.indent(tree)
    with path.open("wb") as file:
        tree.write(file, encoding="utf-8", xml_declaration=True)
        file.write(b"\n")


def main():
    """Проверить параметры, выполнить программу и создать XML-дамп."""
    parser = argparse.ArgumentParser(
        description="Интерпретатор УВМ, вариант 22"
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="двоичный файл"
    )
    parser.add_argument("--output", type=Path, required=True, help="дамп XML")
    parser.add_argument(
        "--range", dest="bounds", type=int, nargs=2, required=True,
        metavar=("START", "END"), help="границы диапазона включительно",
    )
    args = parser.parse_args()
    start, end = args.bounds
    try:
        if not 0 <= start <= end <= ADDRESS_MASK:
            raise ValueError(
                f"ожидается диапазон 0 <= START <= END <= {ADDRESS_MASK}"
            )
        memory = run_program(args.input.read_bytes())
        dump_memory(memory, range(start, end + 1), args.output)
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
