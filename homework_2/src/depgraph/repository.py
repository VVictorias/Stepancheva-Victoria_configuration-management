"""Чтение графа из локального тестового файла."""

from pathlib import Path
import re


NODE = re.compile(r"[A-Z]")


def parse_test_line(line, number):
    """Проверить форму одной непустой строки графа."""
    name, separator, tail = line.partition(":")
    name = name.strip()
    children = tail.split()
    if not separator or not NODE.fullmatch(name):
        raise ValueError(f"строка {number}: ожидается A: B C")
    if not all(NODE.fullmatch(child) for child in children):
        raise ValueError(f"строка {number}: нужны имена A-Z")
    return name, children


def parse_test_repository(text):
    """Прочитать строки A: B C; потребовать объявления всех вершин."""
    graph = {}
    for number, line in enumerate(text.splitlines(), start=1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        name, children = parse_test_line(line, number)
        if name in graph:
            raise ValueError(f"строка {number}: повторное объявление {name}")
        graph[name] = list(dict.fromkeys(children))
    if not graph:
        raise ValueError("тестовый репозиторий пуст")
    missing = {
        child for values in graph.values() for child in values
    } - graph.keys()
    if missing:
        raise ValueError("не объявлены пакеты: " + ", ".join(sorted(missing)))
    return graph


class TestRepository:
    """Предоставлять зависимости тестовых пакетов без сетевых обращений."""

    def __init__(self, path):
        """Прочитать и проверить весь UTF-8 файл."""
        try:
            self.graph = parse_test_repository(
                Path(path).expanduser().read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError) as error:
            raise ValueError(
                f"не удалось прочитать репозиторий: {error}"
            ) from error

    def resolve(self, package):
        """Потребовать присутствия корня в файле."""
        if package not in self.graph:
            raise ValueError(f"пакет {package} отсутствует в репозитории")
        return package

    def children(self, package, exclusions):
        """Вернуть соседей с пустым контекстом Maven-исключений."""
        return [(child, exclusions) for child in self.direct(package)]

    def direct(self, package):
        """Вернуть прямые зависимости тестового пакета."""
        return self.graph[package]
