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

    def test_mermaid_files_and_browser(self):
        """Сохранить Mermaid и HTML с рёбрами, открыть страницу."""
        graph = graph_module.Graph("A", {"A": ["B"], "B": ["A"]})
        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "depgraph.visualize.webbrowser.open", return_value=True
            ) as opened:
                page = visualize.write_visualization(graph, directory)
            opened.assert_called_once_with(page.as_uri())
            html = page.read_text(encoding="utf-8")
            self.assertIn("mermaid.run", html)
            self.assertIn("Диаграмма готова", html)
            diagram = (page.parent / "graph.mmd").read_text(encoding="utf-8")
            self.assertIn("flowchart TD", diagram)
            self.assertIn("n0 --> n1", diagram)
            self.assertIn("n1 --> n0", diagram)

    def test_ascii_tree(self):
        """Отметить общий узел ромба, цикл и одиночную вершину."""
        cases = (
            ({"A": ["B", "C"], "B": ["D"], "D": [], "C": ["D"]},
             "A\n|-- B\n|   `-- D\n`-- C\n    `-- D [уже показан]"),
            ({"A": ["A"]}, "A\n`-- A [цикл]"),
            ({"A": []}, "A"),
        )
        for edges, expected in cases:
            with self.subTest(edges=edges):
                graph = graph_module.Graph("A", edges)
                self.assertEqual(visualize.ascii_tree(graph), expected)
