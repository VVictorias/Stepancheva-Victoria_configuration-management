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
