"""Проверки ассемблера в отдельном процессе."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
ASSEMBLER = PROJECT / "src" / "assembler.py"
CONTROL = PROJECT / "examples" / "control.asm"


class AssemblerTests(unittest.TestCase):
    """Проверить команды языка, их операнды и сообщения об ошибках."""

    def setUp(self):
        """Подготовить временные файлы для каждого теста."""
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.source = Path(work.name) / "input file.asm"
        self.output = Path(work.name) / "output file.bin"

    def assemble(self, path, *options):
        """Выполнить ассемблер с указанным исходным файлом."""
        return subprocess.run(
            [
                sys.executable, "-B", str(ASSEMBLER),
                "--input", str(path), "--output", str(self.output), *options,
            ],
            capture_output=True, text=True, timeout=10,
        )

    def assert_bad_source(self, source, message):
        """Проверить, что ошибка указывает строку и её причину."""
        self.source.write_text("# первая строка\n" + source, encoding="utf-8")
        result = self.assemble(self.source, "--test")
        self.assertEqual(result.returncode, 1)
        self.assertIn("строка 2:", result.stderr)
        self.assertIn(message, result.stderr)

    def test_control_fields(self):
        """Сравнить поля четырёх контрольных команд с методичкой."""
        result = self.assemble(CONTROL, "--test")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "A=0, B=197", "A=11, B=93", "A=3, B=959", "A=5, B=654",
        ])

    def test_operand_limits(self):
        """Принять нижние и верхние границы всех числовых полей."""
        self.source.write_text(
            "  load 0 # минимум\n\nLOAD 0xFFFFFFF\n"
            "READ 0\nREAD 65535\nSTORE 0\nSTORE 65535\n"
            "BSWAP 0\nBSWAP 65535\n",
            encoding="utf-8",
        )
        result = self.assemble(self.source, "--test")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "A=0, B=0", "A=0, B=268435455", "A=11, B=0", "A=11, B=65535",
            "A=3, B=0", "A=3, B=65535", "A=5, B=0", "A=5, B=65535",
        ])

    def test_bad_syntax(self):
        """Отклонить неизвестную команду, лишний или пропущенный аргумент."""
        for source, message in (
            ("MOVE 1", "неизвестная команда"),
            ("LOAD", "нужен один аргумент"),
            ("READ 1 2", "нужен один аргумент"),
            ("STORE 1.5", "неверное число"),
            ("BSWAP 0xG", "неверное число"),
        ):
            with self.subTest(source=source):
                self.assert_bad_source(source, message)

    def test_operand_out_of_range(self):
        """Отклонить отрицательные и слишком большие операнды."""
        for source in (
            "LOAD -1", "LOAD 268435456", "READ -1", "READ 65536",
            "STORE -1", "STORE 65536", "BSWAP -1", "BSWAP 65536",
        ):
            with self.subTest(source=source):
                self.assert_bad_source(source, "вне")

    def test_missing_input(self):
        """Проверить сообщение при отсутствии исходного файла."""
        result = self.assemble(self.source, "--test")
        self.assertEqual(result.returncode, 1)
        self.assertIn(str(self.source), result.stderr)
        self.assertFalse(self.output.exists())
