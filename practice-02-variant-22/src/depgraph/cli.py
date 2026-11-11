"""Вывод конфигурации первого этапа."""

from .config import parse_args


def main(argv=None):
    """Вывести четыре проверенные настройки в формате ключ=значение."""
    config = parse_args(argv)
    print(f"package={config.package}")
    print(f"repository={config.repository}")
    print(f"test_repository={str(config.test_repository).lower()}")
    print(f"ascii_tree={str(config.ascii_tree).lower()}")
    return 0
