"""Командный интерфейс этапов домашней работы №2."""

import sys

from .config import parse_args
from .graph import adjacency_text, build_graph, dependency_order, traverse
from .repository import MavenSource, TestRepository


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
        else MavenSource(config.repository)
    )
    root = source.resolve(config.package)
    if config.mode == "direct":
        for item in source.direct(root):
            print(item if isinstance(item, str) else item.package)
        return
    graph = build_graph(source, root)
    if config.mode == "order":
        order = dependency_order(graph)
        print("\n".join(order) if order else "Зависимостей нет.")
        return
    print(adjacency_text(graph))
    _, cycles = traverse(graph)
    for left, right in cycles:
        print(f"Цикл: {left} -> {right}", file=sys.stderr)


def main(argv=None):
    """Обработать ожидаемые ошибки без вывода Python traceback."""
    config = parse_args(argv)
    try:
        execute(config)
    except (ValueError, OSError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return RUNTIME_ERROR
    return 0
