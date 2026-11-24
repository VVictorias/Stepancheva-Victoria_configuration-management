"""Построение графа и порядка загрузки на тестовых файлах."""

from importlib import import_module
from pathlib import Path
import sys
import unittest


HOMEWORK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOMEWORK / "src"))
graph = import_module("depgraph.graph")
repository = import_module("depgraph.repository")


def build(example):
    """Построить граф из файла примера."""
    path = HOMEWORK / "examples" / f"{example}.txt"
    source = repository.TestRepository(path)
    return graph.build_graph(source, source.resolve("A"))


class GraphTests(unittest.TestCase):
    """Проверить достижимые вершины, циклы и полную обработку ветвей."""

    def test_chain_and_leaf(self):
        """Включить последнюю вершину цепочки и отдельный лист."""
        self.assertEqual(graph.adjacency_text(build("chain")), "A: B\nB: C\nC:")
        self.assertEqual(graph.adjacency_text(build("leaf")), "A:")

    def test_diamond(self):
        """Сохранить обе ветви к общей вершине и исключить недостижимую."""
        result = build("diamond")
        self.assertEqual(
            result.edges, {"A": ["B", "C"], "B": ["D"], "D": [], "C": ["D"]}
        )
        self.assertEqual(graph.traverse(result)[1], [])

    def test_cycles(self):
        """Отметить обратное ребро цикла и петлю."""
        cases = (("cycle", ("C", "A")), ("self_cycle", ("A", "A")))
        for example, back_edge in cases:
            with self.subTest(example=example):
                result = build(example)
                self.assertEqual(graph.traverse(result)[1], [back_edge])
                with self.assertRaisesRegex(ValueError, "порядок.*цикл"):
                    graph.dependency_order(result)

    def test_dependency_order(self):
        """Поставить зависимость раньше пакета, который её использует."""
        for example, expected in (
            ("chain", ["C", "B"]), ("diamond", ["D", "B", "C"]), ("leaf", []),
        ):
            with self.subTest(example=example):
                order = graph.dependency_order(build(example))
                self.assertEqual(order, expected)

    def test_invalid_repository(self):
        """Отклонить неверный формат и неописанные вершины."""
        for text in ("", "A B", "A: BB", "A: B", "A:\nA:"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    repository.parse_test_repository(text)
