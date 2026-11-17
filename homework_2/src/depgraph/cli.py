"""Вывод конфигурации первого этапа."""

import sys

from .config import parse_args
from .maven import MavenRepository


def main(argv=None):
    """Вывести прямые зависимости, в тестовом режиме пока настройки."""
    config = parse_args(argv)
    if config.mode != "config" and not config.test_repository:
        try:
            repository = MavenRepository(config.repository)
            package = repository.resolve(config.package)
            dependencies = repository.direct(package)
        except ValueError as error:
            print(f"Ошибка: {error}", file=sys.stderr)
            return 1
        for dependency in dependencies:
            print(dependency.package)
        return 0
    print(f"package={config.package}")
    print(f"repository={config.repository}")
    print(f"test_repository={str(config.test_repository).lower()}")
    print(f"ascii_tree={str(config.ascii_tree).lower()}")
    return 0
