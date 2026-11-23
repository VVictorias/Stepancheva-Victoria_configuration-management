"""Проверки запуска конвертера через командную строку."""

import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
MAIN = PROJECT / "src" / "main.py"


class CliTests(unittest.TestCase):
    """Проверить преобразование файлов и сообщения об ошибках."""

    def setUp(self):
        """Подготовить отдельный каталог с путями для прогона."""
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.directory = Path(work.name)
        self.source = self.directory / "input file.cfg"
        self.output = self.directory / "output file.toml"

    def run_cli(self, input_path=None, output_path=None):
        """Запустить точку входа отдельным процессом."""
        return subprocess.run(
            [
                sys.executable, "-B", str(MAIN),
                "--input", str(input_path or self.source),
                "--output", str(output_path or self.output),
            ],
            cwd=self.directory,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def assert_config(self, source, expected):
        """Сравнить данные выходного TOML с ожидаемым словарём."""
        self.source.write_text(source, encoding="utf-8")
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        with self.output.open("rb") as file:
            self.assertEqual(tomllib.load(file), expected)

    def assert_invalid(self, source, message):
        """Проверить отказ без перезаписи выхода."""
        original = "previous = 42\n"
        self.source.write_text(source, encoding="utf-8")
        self.output.write_text(original, encoding="utf-8")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn(message, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(self.output.read_text(encoding="utf-8"), original)

    def test_integers(self):
        """Проверить знаки, нули и границы целых TOML."""
        self.assert_config(
            "list(0, +0, -0, 17, +42, -9,\n"
            "     9223372036854775807, -9223372036854775808) -> numbers",
            {
                "numbers": [
                    0, 0, 0, 17, 42, -9,
                    9223372036854775807, -9223372036854775808,
                ]
            },
        )

    def test_invalid_integers(self):
        """Отклонить дроби, ведущие нули и неверные знаки."""
        for value in ("01", "-01", "+00", "2.5", "1e3", "++1", "- 1", "١"):
            with self.subTest(value=value):
                self.assert_invalid(
                    f"{value} -> digit", "синтаксическая ошибка"
                )

    def test_toml_integer_range(self):
        """Отклонить слишком большие числа, в том числе вычисленные."""
        for value in (
            "9223372036854775808",
            "list(-9223372036854775809)",
            "?{+ 9223372036854775807 1}",
        ):
            with self.subTest(value=value):
                self.assert_invalid(f"{value} -> value", "64-битного целого")

    def test_strings(self):
        """Сохранить кириллицу, пробелы, обратную косую черту и табуляцию."""
        self.assert_config(
            '@"  Привет, мир!" -> text\n'
            '@"" -> empty\n'
            '@"C:\\temp\t# -> ()" -> path',
            {
                "text": "  Привет, мир!",
                "empty": "",
                "path": "C:\\temp\t# -> ()",
            },
        )

    def test_invalid_strings(self):
        """Отклонить кавычки без @, обрыв строки и перенос внутри строки."""
        for value in ('"text"', '@"text', '@"one\ntwo"'):
            with self.subTest(value=value):
                self.assert_invalid(f"{value} -> s", "синтаксическая ошибка")

    def test_arrays(self):
        """Проверить обычный, пустой и вложенный смешанный массивы."""
        self.assert_config(
            "list(1, 2, 3) -> flat\nlist( ) -> empty\n"
            'list(1,\n list(@"два", list(3)),\n ?{+ 4 5}) -> nested\n',
            {"flat": [1, 2, 3], "empty": [], "nested": [1, ["два", [3]], 9]},
        )

    def test_invalid_arrays(self):
        """Отклонить неверные разделители и пропущенные элементы."""
        values = ("list(1 2)", "list(1,)", "list(,2)", "list(1,,2)", "[1]")
        for value in values:
            with self.subTest(value=value):
                self.assert_invalid(f"{value} -> a", "синтаксическая ошибка")

    def test_names(self):
        """Принять регистр, подчёркивания и имена list и ord."""
        self.assert_config(
            "1 -> _\n2 -> Ab_C\n3 -> list\n4 -> ord\n"
            "?{+ list ord} -> result",
            {"_": 1, "Ab_C": 2, "list": 3, "ord": 4, "result": 7},
        )

    def test_invalid_names(self):
        """Отклонить цифры, дефис и нелатинские буквы в имени."""
        for name in ("name1", "1abc", "two-words", "буква", "two words"):
            with self.subTest(name=name):
                self.assert_invalid(
                    f"1 -> {name}", "синтаксическая ошибка"
                )

    def test_duplicate_constant(self):
        """Отклонить повторное объявление."""
        self.assert_invalid("1 -> x\n2 -> x", "строка 2: повтор имени 'x'")

    def test_nested_arithmetic(self):
        """Вычислить вложенные выражения с константами и знаками."""
        self.assert_config(
            "10 -> base\n?{+ base -3} -> first\n"
            "?{- ?{+ first +2} base} -> second\n"
            "list(?{- base 20}, ?{+ ?{- 3 2} 5}) -> results",
            {"base": 10, "first": 7, "second": -1, "results": [-10, 6]},
        )

    def test_ord(self):
        """Получить коды символов из литерала и из константы."""
        self.assert_config(
            '@"Я" -> letter\n?{ord letter} -> code\n'
            '?{+ ?{ord @"A"} 1} -> offset',
            {"letter": "Я", "code": ord("Я"), "offset": 66},
        )

    def test_unknown_constant(self):
        """Отклонить отсутствующее и объявленное ниже имя."""
        for source in (
            "?{+ missing 1} -> value",
            "?{+ missing 1} -> value\n1 -> missing",
        ):
            with self.subTest(source=source):
                self.assert_invalid(source, "неизвестная константа 'missing'")

    def test_bad_arithmetic_arguments(self):
        """Отклонить строки и массивы в арифметических операциях."""
        self.assert_invalid('?{+ @"1" 2} -> x', "нужны два целых числа")
        self.assert_invalid("?{- 2 list(1)} -> x", "нужны два целых числа")

    def test_bad_ord_arguments(self):
        """Отклонить строку неверной длины и значения другого типа."""
        for argument in ('@""', '@"AB"', '1', 'list(@"A")'):
            with self.subTest(argument=argument):
                self.assert_invalid(
                    f"?{{ord {argument}}} -> x", "строка из одного символа"
                )

    def test_invalid_expressions(self):
        """Отклонить неверную операцию, арность и разделение аргументов."""
        for value in (
            "?{* 2 3}", "?{+ 2}", "?{+ 2 3 4}", "?{ord}",
            "?{ord 1 2}", "?{+ 2+3}", "?{+2 3}",
        ):
            with self.subTest(value=value):
                self.assert_invalid(f"{value} -> x", "синтаксическая ошибка")

    def test_error_location(self):
        """Сообщить строку и столбец ошибки, в том числе в конце файла."""
        self.assert_invalid("1 -> x\nlist(1, ) -> y", "строка 2, столбец 9")
        self.assert_invalid("1 -> x\nlist(1,", "строка 2, столбец 8")
        self.assert_invalid("1 -> x\nlist(1,", "неожиданный конец файла")

    def test_missing_input(self):
        """Сообщить об отсутствующем файле и не создать выход."""
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("не удалось прочитать", result.stderr)
        self.assertFalse(self.output.exists())

    def test_invalid_utf8(self):
        """Сообщить об ошибке чтения файла в другой кодировке."""
        self.source.write_bytes(b'@"\xff" -> x')
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("не удалось прочитать", result.stderr)

    def test_output_is_directory(self):
        """Сообщить об ошибке записи и убрать временный файл."""
        self.source.write_text("1 -> x", encoding="utf-8")
        self.output.mkdir()
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("не удалось записать", result.stderr)
        self.assertEqual(set(self.directory.iterdir()),
                         {self.source, self.output})
        self.assertTrue(self.output.is_dir())

    def test_same_file(self):
        """Отклонить совпадение путей, сохранив исходный текст."""
        self.source.write_text("1 -> x", encoding="utf-8")
        result = self.run_cli(output_path=self.source)
        self.assertEqual(result.returncode, 1)
        self.assertIn("пути к входному и выходному файлам совпадают",
                      result.stderr)
        self.assertEqual(self.source.read_text(encoding="utf-8"), "1 -> x")

    def test_launcher_from_other_directory(self):
        """Запустить run.sh из другого каталога с путями с пробелами."""
        self.source.write_text('@"Ввод" -> title', encoding="utf-8")
        result = subprocess.run(
            [
                "bash", str(PROJECT / "run.sh"),
                "--input", self.source.name, "--output", self.output.name,
            ],
            cwd=self.directory,
            env={"PATH": f"{Path(sys.executable).parent}:/usr/bin:/bin"},
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with self.output.open("rb") as file:
            self.assertEqual(tomllib.load(file), {"title": "Ввод"})

    def test_required_arguments(self):
        """Вернуть код 2, когда отсутствуют обязательные аргументы."""
        result = subprocess.run(
            [sys.executable, "-B", str(MAIN)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--input", result.stderr)
        self.assertIn("--output", result.stderr)
