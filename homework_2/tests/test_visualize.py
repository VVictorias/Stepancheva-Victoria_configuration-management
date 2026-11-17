"""Проверки Mermaid, ASCII и открытия созданной HTML-страницы."""

from importlib import import_module
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
graph_module = import_module("depgraph.graph")
visualize = import_module("depgraph.visualize")


class VisualizationTests(unittest.TestCase):
    """Сверить рёбра изображения и защиту от повторного раскрытия."""

    def test_mermaid_edges_and_leaf(self):
        """Сохранить оба ребра цикла и отдельную вершину листа."""
        graph = graph_module.Graph("A", {"A": ["B"], "B": ["A"]})
        text = visualize.mermaid_text(graph)
        self.assertIn("flowchart TD", text)
        self.assertIn("n0 --> n1", text)
        self.assertIn("n1 --> n0", text)
        self.assertEqual(
            visualize.mermaid_text(graph_module.Graph("A", {"A": []})),
            'flowchart TD\n    n0["A"]\n',
        )

    def test_ascii_diamond(self):
        """Отобразить обе ветви и не раскрывать общий узел повторно."""
        graph = graph_module.Graph(
            "A", {"A": ["B", "C"], "B": ["D"], "D": [], "C": ["D"]}
        )
        self.assertEqual(
            visualize.ascii_tree(graph),
            "A\n|-- B\n|   `-- D\n`-- C\n    `-- D [уже показан]",
        )

    def test_ascii_cycle(self):
        """Завершить ASCII-обход петли с понятной отметкой."""
        graph = graph_module.Graph("A", {"A": ["A"]})
        self.assertEqual(visualize.ascii_tree(graph), "A\n`-- A [цикл]")

    def test_write_and_open(self):
        """Записать оба файла и передать браузеру абсолютный file URI."""
        graph = graph_module.Graph("A", {"A": []})
        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "depgraph.visualize.webbrowser.open", return_value=True
            ) as opened:
                page = visualize.write_visualization(graph, directory)
            opened.assert_called_once_with(page.as_uri())
            self.assertIn("mermaid.run", page.read_text())
            self.assertIn("Диаграмма готова", page.read_text())
            self.assertEqual(
                (page.parent / "graph.mmd").read_text(),
                visualize.mermaid_text(graph),
            )

    def test_headless_and_browser_failure(self):
        """Не открывать браузер при no-open и сообщать об отказе открытия."""
        graph = graph_module.Graph("A", {"A": []})
        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "depgraph.visualize.webbrowser.open", return_value=False
            ) as opened:
                visualize.write_visualization(graph, directory, False)
                opened.assert_not_called()
                with self.assertRaisesRegex(ValueError, "браузер"):
                    visualize.write_visualization(graph, directory)


if __name__ == "__main__":
    unittest.main()
