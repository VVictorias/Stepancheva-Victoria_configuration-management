"""Командный интерфейс этапов домашней работы №2."""

import sys

from .config import parse_args
from .graph import adjacency_text, build_graph, dependency_order, traverse
from .maven import MavenRepository
from .repository import TestRepository
from .visualize import ascii_tree, mermaid_text, write_visualization


RUNTIME_ERROR = 1


def configuration_text(config):
    """Воспроизвести четыре настройки первого этапа."""
    return "\n".join(
        (
            f"package={config.package}",
            f"repository={config.repository}",
            f"test_repository={str(config.test_repository).lower()}",
            f"ascii_tree={str(config.ascii_tree).lower()}",
        )
    )


def execute(config):
    """Выбрать источник и выполнить операцию после проверки параметров."""
    if config.mode == "config":
        print(configuration_text(config))
        return
    source = (
        TestRepository(config.repository)
        if config.test_repository
        else MavenRepository(config.repository)
    )
    root = source.resolve(config.package)
    if config.mode == "direct":
        dependencies = source.direct(root)
        for item in dependencies:
            print(item if config.test_repository else item.package)
        return
    show_graph(build_graph(source, root), config)


def show_graph(graph, config):
    """Вывести граф, порядок зависимостей или визуализацию."""
    if config.mode == "order":
        order = dependency_order(graph)
        print("\n".join(order) if order else "Зависимостей нет.")
        return
    if config.mode == "graph":
        print(adjacency_text(graph))
    else:
        show_visualization(graph, config)
    _, cycles = traverse(graph)
    for left, right in cycles:
        print(f"Цикл: {left} -> {right}", file=sys.stderr)


def show_visualization(graph, config):
    """Вывести Mermaid, необязательное дерево и открыть изображение."""
    diagram = mermaid_text(graph)
    page = write_visualization(
        graph.root, diagram, config.output, not config.no_open
    )
    print(diagram, end="")
    if config.ascii_tree:
        print(ascii_tree(graph))
    print(f"Диаграмма: {page}")


def main(argv=None):
    """Обработать ожидаемые ошибки без вывода Python traceback."""
    config = parse_args(argv)
    try:
        execute(config)
    except (ValueError, OSError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return RUNTIME_ERROR
    return 0
