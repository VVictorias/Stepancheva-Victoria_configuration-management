"""Проверки DFS на циклах, ромбе и длинной цепочке."""

from importlib import import_module
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
graph_module = import_module("depgraph.graph")
repository_module = import_module("depgraph.repository")


class MemorySource:
    """Простой источник для проверки DFS независимо от формата имён."""

    def __init__(self, edges):
        """Запомнить рёбра и список фактических загрузок."""
        self.edges = edges
        self.calls = []

    def children(self, node, exclusions):
        """Записать посещение вершины и вернуть соседей."""
        self.calls.append(node)
        return [(child, exclusions) for child in self.edges[node]]


class GraphTests(unittest.TestCase):
    """Проверить граф, а не только совпадение текста CLI."""

    def build(self, edges):
        """Построить граф от A через настоящий стековый DFS."""
        return graph_module.build_graph(MemorySource(edges), "A")

    def test_diamond_and_unreachable(self):
        """Посетить общий узел один раз; недостижимый не включать."""
        source = MemorySource(
            {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": [], "Z": []}
        )
        graph = graph_module.build_graph(source, "A")
        self.assertEqual(source.calls, ["A", "B", "D", "C"])
        self.assertEqual(graph.edges["C"], ["D"])
        self.assertNotIn("Z", graph.edges)
        self.assertEqual(graph_module.traverse(graph)[1], [])

    def test_cycle_and_self_cycle(self):
        """Сохранить обратное ребро и завершить обход."""
        for edges, back in [
            ({"A": ["B"], "B": ["A"]}, ("B", "A")),
            ({"A": ["A"]}, ("A", "A")),
        ]:
            with self.subTest(edges=edges):
                graph = self.build(edges)
                self.assertIn(back, graph_module.traverse(graph)[1])

    def test_leaf(self):
        """Единственная вершина сохраняется в результате."""
        graph = self.build({"A": []})
        self.assertEqual(graph_module.adjacency_text(graph), "A:")
        self.assertEqual(graph_module.traverse(graph), (["A"], []))

    def test_deep_iterative_dfs(self):
        """Пройти 2500 узлов, превышающих обычный лимит рекурсии Python."""
        length = 2500
        edges = {str(i): [str(i + 1)] for i in range(length)}
        edges[str(length)] = []
        graph = graph_module.build_graph(MemorySource(edges), "0")
        completed, cycles = graph_module.traverse(graph)
        self.assertEqual(len(completed), length + 1)
        self.assertEqual(completed[0], str(length))
        self.assertEqual(cycles, [])

    def test_invalid_repository(self):
        """Отклонить пустой файл, неверные имена и отсутствующие вершины."""
        for text in ["", "a: B", "A B", "A: BB", "A: B", "A:\nA:"]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    repository_module.parse_test_repository(text)

    def test_test_file_and_missing_root(self):
        """Прочитать UTF-8 файл и проверить существование выбранного корня."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "repo.txt"
            path.write_text("A: B B # общий узел\nB:\n", encoding="utf-8")
            source = repository_module.TestRepository(path)
            self.assertEqual(source.direct(source.resolve("A")), ["B"])
            with self.assertRaisesRegex(ValueError, "отсутствует"):
                source.resolve("Z")
            path.write_bytes(b"\xff")
            with self.assertRaisesRegex(ValueError, "прочитать"):
                repository_module.TestRepository(path)

    def test_scope_optional_and_exclusions(self):
        """Применять scope и exclusions по контексту пути."""
        model = import_module("depgraph.model")
        source = repository_module.MavenSource("https://example.org/")
        source.direct = lambda node: [
            model.Dependency("g:b:1"),
            model.Dependency("g:c:1", scope="test"),
            model.Dependency("g:d:1", optional=True),
            model.Dependency("g:e:1", exclusions=frozenset({("x", "*")})),
        ]
        self.assertEqual(
            source.children("g:a:1", frozenset({("g", "b")})),
            [("g:e:1", frozenset({("g", "b"), ("x", "*")}))],
        )


if __name__ == "__main__":
    unittest.main()
