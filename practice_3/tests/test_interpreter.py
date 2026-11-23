"""Проверки выполнения машинного кода и чтения XML."""

import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

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
        """Записать, прочитать и вывести последнее слово памяти."""
        self.assert_program(
            "LOAD 197\nSTORE 65535\nLOAD 65534\nREAD 1\nSTORE 65534\n",
            65534, [197, 197],
        )

    def test_zero_accumulator_and_unwritten_memory(self):
        """Проверить нулевое начальное значение регистра и данных."""
        self.assert_program("STORE 100\n", 100, [0, 0])

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
        """Отклонить обрезанную команду и ненулевые биты заполнения."""
        for machine_code, message in (
            ("50 0C 00", "неполная команда"),
            ("DB 05 80", "ненулевые биты за полем B"),
        ):
            with self.subTest(machine_code=machine_code):
                self.binary.write_bytes(bytes.fromhex(machine_code))
                result = self.interpret(0, 0)
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)
                self.assertFalse(self.dump.exists())

    def test_unknown_opcode(self):
        """Сообщить позицию неизвестной команды в машинном коде."""
        self.binary.write_bytes(bytes.fromhex("50 0C 00 00 0F"))
        result = self.interpret(0, 0)
        self.assertEqual(result.returncode, 1)
        self.assertIn("байт 4: неизвестный код операции 15", result.stderr)
        self.assertFalse(self.dump.exists())

    def test_missing_binary(self):
        """Сообщить об отсутствующем двоичном файле."""
        result = self.interpret(0, 0)
        self.assertEqual(result.returncode, 1)
        self.assertIn(str(self.binary), result.stderr)
        self.assertFalse(self.dump.exists())

    def test_bad_xml_path(self):
        """Сообщить об отсутствующей папке для XML-дампа."""
        self.assemble(EXAMPLES / "copy.asm")
        self.dump = self.directory / "absent" / "memory.xml"
        result = self.interpret(100, 107)
        self.assertEqual(result.returncode, 1)
        self.assertIn(str(self.dump), result.stderr)
