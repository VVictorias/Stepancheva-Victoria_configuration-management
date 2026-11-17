"""Проверки настоящего CLI с локальным HTTP Maven-репозиторием."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Thread
import unittest


CLI = Path(__file__).resolve().parents[1] / "src" / "main.py"


class QuietHandler(SimpleHTTPRequestHandler):
    """Обслуживать тестовые POM без записи запросов в консоль."""

    def log_message(self, format_string, *args):
        """Подавить только диагностический журнал HTTP-сервера."""


class IntegrationTests(unittest.TestCase):
    """Проверить HTTP, XML, DFS, CLI и запись HTML совместно."""

    @classmethod
    def setUpClass(cls):
        """Запустить временный HTTP-сервер на свободном локальном порту."""
        cls.directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls.directory.name)
        for name, child in [("a", "b"), ("b", "c"), ("c", None)]:
            base = cls.root / "g" / name / "1"
            base.mkdir(parents=True)
            dependencies = (
                ""
                if child is None
                else (
                    "<dependencies><dependency><groupId>g</groupId>"
                    f"<artifactId>{child}</artifactId><version>1</version>"
                    "</dependency></dependencies>"
                )
            )
            (base / f"{name}-1.pom").write_text(
                "<project>" + dependencies + "</project>", encoding="utf-8"
            )
        handler = partial(QuietHandler, directory=str(cls.root))
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/"

    @classmethod
    def tearDownClass(cls):
        """Остановить сервер и удалить временные файлы теста."""
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.directory.cleanup()

    def run_cli(self, *args):
        """Запустить отдельный процесс приложения без обращения к Internet."""
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(CLI),
                "--package",
                "g:a:1",
                "--repository",
                self.url,
                *args,
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

    def test_direct_graph_and_order(self):
        """Получить прямые и транзитивные связи через настоящий HTTP."""
        for mode, expected in [
            ("direct", "g:b:1\n"),
            ("graph", "g:a:1: g:b:1\ng:b:1: g:c:1\ng:c:1:\n"),
            ("order", "g:c:1\ng:b:1\n"),
        ]:
            with self.subTest(mode=mode):
                result = self.run_cli("--mode", mode)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected)
                self.assertEqual(result.stderr, "")

    def test_default_visualization_and_ascii(self):
        """Режим по умолчанию записывает Mermaid и HTML с полным графом."""
        output = self.root / "output"
        result = self.run_cli(
            "--ascii-tree", "--no-open", "--output", str(output)
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("n1 --> n2", result.stdout)
        self.assertIn("`-- g:b:1\n    `-- g:c:1", result.stdout)
        self.assertTrue((output / "graph.html").is_file())
        self.assertIn("n1 --> n2", (output / "graph.mmd").read_text())

    def test_http_not_found(self):
        """HTTP 404 даёт код 1 без traceback и частичного графа."""
        result = self.run_cli("--mode", "graph", "--package", "g:missing:1")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("404", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_malformed_xml(self):
        """CLI сообщает о неверном XML сервера."""
        directory = self.root / "g" / "broken" / "1"
        directory.mkdir(parents=True)
        (directory / "broken-1.pom").write_text("<project>")
        result = self.run_cli("--mode", "direct", "--package", "g:broken:1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("XML", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_unknown_mode_and_unwritable_output(self):
        """Проверить неверный режим и каталог вывода, занятый файлом."""
        for args in [
            ("--mode", "unknown"),
            ("--output", " "),
            ("--no-open=false",),
        ]:
            result = self.run_cli(*args)
            self.assertEqual(result.returncode, 2)
        output = self.root / "not-a-directory"
        output.write_text("existing data")
        result = self.run_cli("--no-open", "--output", str(output))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(output.read_text(), "existing data")
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
