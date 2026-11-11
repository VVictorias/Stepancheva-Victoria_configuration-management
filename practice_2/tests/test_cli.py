"""Воспроизводимые проверки CLI через отдельные процессы Python."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "src" / "cli.py"
FIXTURE = ROOT / "tests" / "fixtures" / "repository.txt"
PACKAGE = "org.apache.commons:commons-lang3:3.12.0"
URL = "https://repo.maven.apache.org/maven2/"
BASE = ["--package", PACKAGE, "--repository", URL]
sys.path.insert(0, str(ROOT / "src"))
from cli import validate_file  # noqa: E402


class CliTests(unittest.TestCase):
    """Проверить вывод, коды возврата и ошибки каждого параметра."""

    def run_cli(self, args, cwd=None):
        """Запустить настоящее приложение с переданными аргументами."""
        return subprocess.run(
            [sys.executable, str(CLI), *args], cwd=cwd,
            capture_output=True, text=True, check=False,
        )

    def assert_error(self, args, expected):
        """Проверить код 2, stderr и отсутствие частичного вывода."""
        result = self.run_cli(args)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("Ошибка:", result.stderr)
        self.assertIn(expected, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_remote_defaults(self):
        """Вывести все настройки, включая значения выключенных флагов."""
        result = self.run_cli(BASE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, (
            f"package={PACKAGE}\nrepository={URL}\n"
            "test_repository=false\nascii_tree=false\n"
        ))

    def test_remote_ascii_setting(self):
        """Включение настройки дерева не запускает построение графа."""
        result = self.run_cli(BASE + ["--ascii-tree"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 4)
        self.assertIn("ascii_tree=true\n", result.stdout)

    def test_test_mode_flag_combinations(self):
        """Проверить тестовый источник с обоими состояниями ASCII-флага."""
        for flags, ascii_value in [([], "false"), (["--ascii-tree"], "true")]:
            with self.subTest(flags=flags):
                result = self.run_cli([
                    "--package", "A", "--repository", str(FIXTURE),
                    "--test-repository", *flags,
                ])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, (
                    f"package=A\nrepository={FIXTURE}\n"
                    f"test_repository=true\nascii_tree={ascii_value}\n"
                ))

    def test_coordinates_and_urls(self):
        """Принять координаты без версии, HTTP, порт и IPv6."""
        for package, url in [
            ("org.example:demo", "http://localhost:8080/repository"),
            ("org.example:demo:1.0-SNAPSHOT", "https://[::1]:443/maven2/"),
        ]:
            with self.subTest(package=package, url=url):
                result = self.run_cli([
                    "--package", package, "--repository", url,
                ])
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_required_values(self):
        """Проверить отсутствие каждого обязательного параметра и значения."""
        cases = [
            ([], "--package"),
            (["--repository", URL], "--package"),
            (["--package", PACKAGE], "--repository"),
            (["--repository", URL, "--package"], "требуется одно значение"),
            (["--package", PACKAGE, "--repository"], "одно значение"),
        ]
        for args, message in cases:
            with self.subTest(args=args):
                self.assert_error(args, message)

    def test_invalid_package(self):
        """Отклонить пустые, неполные и повреждённые координаты Maven."""
        for package in [
            "", " ", "commons-lang3", "org.example:", ":demo", "g:a:",
            "g:a:1:extra", "org..example:demo", "g:bad name", "g:../demo",
        ]:
            with self.subTest(package=package):
                self.assert_error([
                    "--package", package, "--repository", URL,
                ], "--package")

    def test_invalid_test_package(self):
        """Тестовые имена должны состоять из одной большой латинской буквы."""
        for package in ["", "a", "AA", "А", PACKAGE]:
            with self.subTest(package=package):
                self.assert_error([
                    "--package", package, "--repository", str(FIXTURE),
                    "--test-repository",
                ], "буква A-Z")

    def test_invalid_url(self):
        """Отклонить неверную схему, сервер, порт и запрещённые части URL."""
        for url in [
            "", " ", "ftp://repo.example.org", "https://", "https:/repo.org",
            "https://bad host/repo", "https://bad_host/repo", "https://[abc]",
            "https://repo.org:abc", "https://repo.org:65536",
            "https://repo.org:0", "https://repo.org:",
            "https://[::1]garbage", "https://[::1]:bad",
            "https://repo.org/path\n", "https://repo.org/%zz",
            "https://repo.org/\\path", "https://user:pass@repo.org",
            "https://repo.org/?x=1", "https://repo.org/#part",
        ]:
            with self.subTest(url=url):
                self.assert_error([
                    "--package", PACKAGE, "--repository", url,
                ], "--repository")

    def test_source_mode_mismatch(self):
        """Отклонить URL в тестовом режиме и путь без тестового режима."""
        self.assert_error([
            "--package", "A", "--repository", URL, "--test-repository",
        ], "путь к файлу, а не URL")
        self.assert_error([
            "--package", PACKAGE, "--repository", str(FIXTURE),
        ], "для файла нужен тестовый режим")

    def test_invalid_file(self):
        """Отклонить пустой путь, отсутствующий файл, каталог и file URL."""
        with tempfile.TemporaryDirectory() as directory:
            sources = ["", " ", str(Path(directory) / "missing.txt"),
                       directory, "file:///tmp/repository.txt"]
            for source in sources:
                with self.subTest(source=source):
                    self.assert_error([
                        "--package", "A", "--repository", source,
                        "--test-repository",
                    ], "--repository")

    def test_unreadable_file(self):
        """Детерминированно проверить запрет чтения при любых правах ОС."""
        error = PermissionError("нет доступа")
        with patch("cli.Path.open", side_effect=error):
            with self.assertRaisesRegex(ValueError, "--repository.*доступа"):
                validate_file(str(FIXTURE))

    def test_flag_misuse(self):
        """Флаги не принимают true/false и другие отдельные значения."""
        for flag in ["--test-repository", "--ascii-tree"]:
            for tail in [[f"{flag}=true"], [f"{flag}=false"], [flag, "yes"]]:
                with self.subTest(tail=tail):
                    self.assert_error(BASE + tail, "Ошибка:")

    def test_unsupported_options(self):
        """Отклонить неизвестные опции, сокращения и поздние параметры."""
        for args in [["--unknown"], ["--ascii"], ["--depth", "3"]]:
            with self.subTest(args=args):
                self.assert_error(BASE + args, "неизвестные параметры")

    def test_help(self):
        """Справка доступна без обязательных параметров."""
        result = self.run_cli(["--help"])
        self.assertEqual(result.returncode, 0, result.stderr)
        for flag in ["--package", "--repository", "--test-repository",
                     "--ascii-tree"]:
            self.assertIn(flag, result.stdout)

    def test_launcher_from_other_directory(self):
        """Скрипт запуска работает с путями, содержащими пробелы."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "test repository.txt"
            source.write_text("не разбирается на этапе 1", encoding="utf-8")
            result = subprocess.run(
                ["sh", str(ROOT / "run.sh"), "--package", "A",
                 "--repository", source.name, "--test-repository"],
                cwd=directory, capture_output=True, text=True, check=False,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"repository={source.name}\n", result.stdout)


if __name__ == "__main__":
    unittest.main()
