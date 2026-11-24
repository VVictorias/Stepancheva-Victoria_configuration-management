"""Параметры командной строки и их проверка."""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

from .model import COORDINATES
from .repository import NODE


MAX_HOST_LENGTH = 253
INVALID_PORT = 0
USAGE_ERROR = 2
DNS_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
DNS_NAME = rf"{DNS_LABEL}(?:\.{DNS_LABEL})*"
URL_HOST_PORT = re.compile(rf"(?:{DNS_NAME}|\[[^]@]+\])(?::[0-9]+)?")


class ConfigParser(argparse.ArgumentParser):
    """Вывести сообщение об ошибке с подсказкой по запуску."""

    def error(self, message):
        """Завершить работу с кодом 2."""
        self.print_usage(sys.stderr)
        self.exit(USAGE_ERROR, f"Ошибка: {message}\nСправка: --help\n")


def build_parser():
    """Описать параметры командной строки."""
    parser = ConfigParser(
        description="Граф зависимостей Java Maven, вариант 22.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--package", required=True,
        help="groupId:artifactId[:version] или буква A-Z в тестовом режиме",
    )
    parser.add_argument(
        "--repository", required=True,
        help="URL HTTP(S) или путь к файлу при --test-repository",
    )
    parser.add_argument(
        "--test-repository", action="store_true",
        help="прочитать локальный тестовый файл",
    )
    parser.add_argument(
        "--ascii-tree", action="store_true", help="добавить ASCII-дерево",
    )
    parser.add_argument(
        "--mode", choices=("config", "direct", "graph", "order", "visualize"),
        default="visualize", help="режим работы (по умолчанию visualize)",
    )
    parser.add_argument("--output", help="каталог для graph.mmd и graph.html")
    parser.add_argument(
        "--no-open", action="store_true", help="сохранить граф без браузера",
    )
    return parser


def validate_url(value):
    """Проверить базовый HTTP(S) URL для загрузки POM."""
    if re.search(r"[\s\x00-\x1f\x7f\\?#]|%(?![0-9A-Fa-f]{2})", value):
        raise ValueError("URL содержит недопустимые символы")
    url = urlsplit(value)
    if url.scheme not in ("http", "https") or not url.hostname:
        raise ValueError("нужен HTTP(S) URL")
    if not URL_HOST_PORT.fullmatch(url.netloc):
        raise ValueError("некорректный сервер или порт")
    if len(url.hostname) > MAX_HOST_LENGTH:
        raise ValueError("слишком длинное имя сервера")
    if url.port == INVALID_PORT:
        raise ValueError("некорректный порт")


def validate_file(value):
    """Проверить, что локальный файл можно открыть."""
    path = Path(value).expanduser()
    if not path.is_file():
        raise ValueError("нужен путь к доступному тестовому файлу")
    with path.open("rb"):
        pass


def parse_args(argv=None):
    """Разобрать параметры и проверить выбранный источник."""
    parser = build_parser()
    config = parser.parse_args(argv)
    if config.test_repository:
        if not NODE.fullmatch(config.package):
            parser.error("--package: в тестовом режиме нужна буква A-Z")
        validate_repository = validate_file
    else:
        if not COORDINATES.fullmatch(config.package):
            parser.error("--package: ожидается groupId:artifactId[:version]")
        validate_repository = validate_url
    if config.output is not None and not config.output.strip():
        parser.error("--output: каталог вывода не может быть пустым")
    try:
        validate_repository(config.repository)
    except (OSError, ValueError) as error:
        parser.error(f"--repository: {error}")
    return config
