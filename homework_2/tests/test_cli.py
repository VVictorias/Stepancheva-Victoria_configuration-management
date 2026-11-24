"""Проверки настроек через скрипт запуска."""

from pathlib import Path
import subprocess
import unittest


HOMEWORK = Path(__file__).resolve().parents[1]
PACKAGE = "junit:junit:4.13.2"
URL = "https://repo.maven.apache.org/maven2/"
REMOTE = ("--package", PACKAGE, "--repository", URL)
LOCAL = (
    "--package", "A", "--repository", "examples/chain.txt", "--test-repository",
)


class CliTests(unittest.TestCase):
    """Проверить конфигурацию и ошибки параметров."""

    def run_config(self, *args):
        """Запустить режим первого этапа."""
        return subprocess.run(
            ["bash", "run.sh", "--mode", "config", *args],
            cwd=HOMEWORK, capture_output=True, text=True, timeout=10,
        )

    def test_valid_configurations(self):
        """Получить четыре настройки в сетевом и тестовом режимах."""
        cases = (
            (REMOTE, f"package={PACKAGE}\nrepository={URL}\n"
             "test_repository=false\nascii_tree=false\n"),
            ((*LOCAL, "--ascii-tree"), "package=A\n"
             "repository=examples/chain.txt\n"
             "test_repository=true\nascii_tree=true\n"),
        )
        for args, expected in cases:
            with self.subTest(args=args):
                result = self.run_config(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected)

    def test_invalid_arguments(self):
        """Отклонить пропуски, ошибочные имена и значения флагов."""
        cases = (
            (("--repository", URL), "--package"),
            (("--package", PACKAGE), "--repository"),
            ((*REMOTE, "--package", "junit"), "--package"),
            ((*LOCAL, "--package", "a"), "--package"),
            ((*REMOTE, "--test-repository=true"), "--test-repository"),
            ((*REMOTE, "--ascii-tree=true"), "--ascii-tree"),
        )
        for args, option in cases:
            with self.subTest(args=args):
                self.assert_usage_error(args, option)

    def test_invalid_repositories(self):
        """Отклонить неверный URL, порт и отсутствующий файл."""
        for args in (
            (*REMOTE, "--repository", "ftp://repo.example.org"),
            (*REMOTE, "--repository", "https://"),
            (*REMOTE, "--repository", "https://localhost:65536"),
            (*REMOTE, "--repository", "examples/chain.txt"),
            (*LOCAL, "--repository", "missing.txt"),
            (*LOCAL, "--repository", URL),
        ):
            with self.subTest(args=args):
                self.assert_usage_error(args, "--repository")

    def assert_usage_error(self, args, option):
        """Проверить код 2 и сообщение о параметре."""
        result = self.run_config(*args)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("Ошибка:", result.stderr)
        self.assertIn(option, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
