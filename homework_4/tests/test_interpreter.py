"""Проверки выполнения машинного кода и чтения XML."""

import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
ASSEMBLER = PROJECT / "src" / "assembler.py"
INTERPRETER = PROJECT / "src" / "interpreter.py"
EXAMPLES = PROJECT / "examples"


class InterpreterTests(unittest.TestCase):
    """Проверить общую память, операции и ошибки интерпретатора."""

    def setUp(self):
        """Подготовить отдельные пути для исходника, кода и дампа."""
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.directory = Path(work.name)
        self.binary = self.directory / "program file.bin"
        self.dump = self.directory / "memory dump.xml"

    def cli(self, script, source, output, *options):
        """Запустить скрипт с путями и дополнительными параметрами."""
        return subprocess.run(
            [
                sys.executable, "-B", str(script),
                "--input", str(source), "--output", str(output), *options,
            ],
            capture_output=True, text=True, timeout=10,
        )

    def assemble(self, source):
        """Ассемблировать исходную программу во временный файл."""
        result = self.cli(ASSEMBLER, source, self.binary)
        self.assertEqual(result.returncode, 0, result.stderr)

    def interpret(self, start, end):
        """Выполнить программу и запросить указанный диапазон."""
        return self.cli(
            INTERPRETER, self.binary, self.dump,
            "--range", str(start), str(end),
        )

    def assert_dump(self, start, values):
        """Сравнить адреса и значения в XML с ожидаемыми."""
        root = ET.parse(self.dump).getroot()
        self.assertEqual(root.tag, "memory")
        self.assertEqual(
            [(cell.tag, cell.attrib, cell.text) for cell in root],
            [
                ("cell", {"address": str(address)}, str(value))
                for address, value in enumerate(values, start=start)
            ],
        )

    def assert_program(self, source, start, values):
        """Выполнить текст УВМ и сравнить выведенные слова."""
        path = self.directory / "program.asm"
        path.write_text(source, encoding="utf-8")
        self.assemble(path)
        result = self.interpret(start, start + len(values) - 1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_dump(start, values)

    def test_copy_array(self):
        """Скопировать массив из слов 100–103 в слова 104–107."""
        self.assemble(EXAMPLES / "copy.asm")
        result = self.interpret(100, 107)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_dump(100, [197, 0, 54321, 268435455] * 2)

    def test_read_code_as_data(self):
        """Прочитать машинное представление LOAD из нулевого слова."""
        self.assert_program("LOAD 42\nLOAD 0\nREAD 0\nSTORE 20\n", 20, [672])

    def test_execute_modified_code(self):
        """Выполнить LOAD, который был изменён командой STORE."""
        self.assert_program(
            "LOAD 0x12340\nSTORE 4\nSTORE 31\nSTORE 32\nSTORE 33\n"
            "LOAD 1\nSTORE 40\n",
            40, [0x1234],
        )

    def test_upper_address(self):
        """Проверить начальные нули и запись в последнее слово."""
        self.assert_program(
            "STORE 65535\nLOAD 65534\nREAD 1\nSTORE 65533\n"
            "LOAD 197\nSTORE 65535\nLOAD 65534\nREAD 1\nSTORE 65534\n",
            65532, [0, 0, 197, 197],
        )

    def test_read_out_of_memory(self):
        """Отклонить READ, если сумма регистра и смещения вне памяти."""
        source = self.directory / "outside.asm"
        source.write_text("LOAD 65535\nREAD 1\n", encoding="utf-8")
        self.assemble(source)
        result = self.interpret(0, 0)
        self.assertEqual(result.returncode, 1)
        self.assertIn("адрес 65536 вне", result.stderr)
        self.assertFalse(self.dump.exists())

    def test_invalid_ranges(self):
        """Отклонить обратный, отрицательный и слишком большой диапазон."""
        self.assemble(EXAMPLES / "copy.asm")
        for start, end in ((7, 6), (-1, 0), (0, 65536)):
            with self.subTest(start=start, end=end):
                result = self.interpret(start, end)
                self.assertEqual(result.returncode, 1)
                self.assertIn("ожидается диапазон", result.stderr)
                self.assertFalse(self.dump.exists())

    def test_corrupt_binary(self):
        """Отклонить неполную команду, лишние биты и неизвестный код."""
        for machine_code, message in (
            ("50 0C 00", "неполная команда"),
            ("DB 05 80", "ненулевые биты за полем B"),
            ("50 0C 00 00 0F", "байт 4: неизвестный код операции 15"),
        ):
            with self.subTest(machine_code=machine_code):
                self.binary.write_bytes(bytes.fromhex(machine_code))
                result = self.interpret(0, 0)
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)
                self.assertFalse(self.dump.exists())

    def test_bswap_example(self):
        """Проверить исходное и переставленное слово в XML."""
        self.assemble(EXAMPLES / "bswap.asm")
        result = self.interpret(100, 101)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_dump(100, [0x01020304, 0x04030201])

    def test_bswap_bounds(self):
        """Проверить границы слова и двойную перестановку байтов."""
        with patch.object(sys, "path", [str(INTERPRETER.parent), *sys.path]):
            from interpreter import bswap

        self.assertEqual(bswap(0), 0)
        self.assertEqual(bswap(0xFFFFFFFF), 0xFFFFFFFF)
        self.assert_program(
            "LOAD 0x80\nSTORE 100\nBSWAP 100\nSTORE 100\n"
            "BSWAP 100\nSTORE 101\n",
            100, [0x80000000, 0x80],
        )

    def assert_vector(self, name, expected):
        """Запустить пример и проверить все девять исходных адресов."""
        self.assemble(EXAMPLES / name)
        result = self.interpret(100, 108)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_dump(100, expected)

    def test_vector_bytes(self):
        """Сверить вектор с байтами в разных позициях."""
        self.assert_vector("vector_bytes.asm", [
            0x04030201, 0x33221100, 0x01000000,
            0x00010000, 0x00000100, 0x00000001,
            0xFFAA5500, 0x0D0C0B0A, 0x5634120F,
        ])

    def test_vector_edges(self):
        """Сверить вектор с повторяющимися и граничными значениями."""
        self.assert_vector("vector_edges.asm", [
            0x00000000, 0x0A0A0A0A, 0x00ABAB00,
            0xF0FF0F00, 0x80000000, 0xFF000000,
            0xFFFFFF0F, 0x00000008, 0xFE807F00,
        ])

    def test_vector_small(self):
        """Сверить вектор с небольшими десятичными числами."""
        self.assert_vector("vector_small.asm", [
            0x01000000, 0x02000000, 0x03000000,
            0x07000000, 0x0F000000, 0x1F000000,
            0x3F000000, 0x7F000000, 0xFF000000,
        ])
