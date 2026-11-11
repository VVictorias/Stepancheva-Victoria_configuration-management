"""Приём и проверка конфигурации прототипа Maven, этап 1."""

import argparse
import ipaddress
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


class ConfigParser(argparse.ArgumentParser):
    """Парсер с понятными сообщениями об ошибках командной строки."""

    def error(self, message):
        """Вывести ошибку в stderr и завершить работу с кодом 2."""
        translations = {
            "the following arguments are required:":
                "не указаны обязательные параметры:",
            "expected one argument": "требуется одно значение",
            "unrecognized arguments:": "неизвестные параметры или значения:",
            "ignored explicit argument": "флаг не принимает значение",
            "argument ": "параметр ",
        }
        for original, translated in translations.items():
            message = message.replace(original, translated)
        self.print_usage(sys.stderr)
        self.exit(2, f"Ошибка: {message}\nСправка: --help\n")


def build_parser():
    """Описать четыре параметра варианта 22 и встроенную справку."""
    parser = ConfigParser(
        description="Maven: этап 1, только проверка и вывод конфигурации.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--package", required=True,
        help="groupId:artifactId[:version]; в тестовом режиме буква A-Z",
    )
    parser.add_argument(
        "--repository", required=True,
        help="HTTP(S) URL или путь к файлу при --test-repository",
    )
    parser.add_argument(
        "--test-repository", action="store_true",
        help="использовать локальный тестовый файл; значение не требуется",
    )
    parser.add_argument(
        "--ascii-tree", action="store_true",
        help="сохранить настройку ASCII-дерева; значение не требуется",
    )
    return parser


def validate_package(value, test_mode):
    """Проверить выбранный формат имени без обращения к Maven."""
    if test_mode:
        if not re.fullmatch(r"[A-Z]", value):
            raise ValueError("--package: в тестовом режиме нужна буква A-Z")
        return
    group = r"[A-Za-z0-9_][A-Za-z0-9_-]*"
    part = r"[A-Za-z0-9_][A-Za-z0-9_.-]*"
    pattern = rf"{group}(?:\.{group})*:{part}(?::{part})?"
    if not re.fullmatch(pattern, value):
        raise ValueError(
            "--package: ожидается groupId:artifactId[:version] без пробелов"
        )


def validate_host(host):
    """Проверить IP-адрес или синтаксис DNS-имени без сетевого запроса."""
    if not host:
        raise ValueError("отсутствует имя сервера")
    try:
        ipaddress.ip_address(host)
        return
    except ValueError:
        pass
    label = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    if len(host) > 253 or not re.fullmatch(rf"{label}(?:\.{label})*", host):
        raise ValueError("некорректное имя сервера")


def validate_url(value):
    """Проверить HTTP(S) URL; доступность сервера на этапе 1 не проверяется."""
    try:
        url = urlsplit(value)
        if url.scheme not in ("http", "https") or not url.netloc:
            raise ValueError(
                "нужен HTTP(S) URL; для файла нужен тестовый режим"
            )
        if any(char.isspace() or ord(char) < 32 for char in value):
            raise ValueError("пробелы и управляющие символы в URL запрещены")
        if "\\" in value or re.search(r"%(?![0-9A-Fa-f]{2})", value):
            raise ValueError("некорректное экранирование URL")
        if url.username is not None or url.password is not None:
            raise ValueError("данные авторизации в URL не поддерживаются")
        if "?" in value or "#" in value:
            raise ValueError("URL не должен содержать query или fragment")
        validate_host(url.hostname)
        if url.netloc.startswith("[") and not re.fullmatch(
            r"\[[^]]+\](?::[0-9]+)?", url.netloc
        ):
            raise ValueError("некорректная запись IPv6-адреса или порта")
        try:
            port = url.port
        except ValueError as error:
            raise ValueError(
                "порт должен быть числом от 1 до 65535"
            ) from error
        if url.netloc.endswith(":") or port == 0:
            raise ValueError("некорректный порт")
    except ValueError as error:
        raise ValueError(f"--repository: {error}") from error


def validate_file(value):
    """Проверить доступность обычного файла, не читая описание графа."""
    if not value.strip():
        raise ValueError("--repository: путь к тестовому файлу пуст")
    if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", value):
        raise ValueError(
            "--repository: тестовый режим требует путь к файлу, а не URL"
        )
    try:
        path = Path(value).expanduser()
        if not path.is_file():
            raise ValueError(
                "файл не существует или путь указывает на каталог"
            )
        with path.open("rb"):
            pass
    except (OSError, ValueError) as error:
        raise ValueError(f"--repository: {error}") from error


def parse_args(argv=None):
    """Прочитать и проверить настройки первого этапа."""
    parser = build_parser()
    config = parser.parse_args(argv)
    try:
        validate_package(config.package, config.test_repository)
        if config.test_repository:
            validate_file(config.repository)
        else:
            validate_url(config.repository)
    except ValueError as error:
        parser.error(str(error))
    return config
