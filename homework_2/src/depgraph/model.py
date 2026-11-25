"""Небольшие структуры данных для POM и зависимостей Maven."""

from dataclasses import dataclass, field
import re
import xml.etree.ElementTree as et


GROUP = r"[A-Za-z0-9_][A-Za-z0-9_-]*"
PART = r"[A-Za-z0-9_][A-Za-z0-9_.-]*"
COORDINATES = re.compile(rf"{GROUP}(?:\.{GROUP})*:{PART}(?::{PART})?")
COORDINATE_KEYS = ("groupId", "artifactId", "version")
PROPERTY = re.compile(r"\$\{([^}]+)\}")
MAX_PROPERTY_PASSES = 64
COORDINATE_PARTS = len(COORDINATE_KEYS)


@dataclass
class Dependency:
    """Зависимость с областью действия и исключениями."""

    package: str
    scope: str = "compile"
    optional: bool = False
    exclusions: frozenset = frozenset()


@dataclass
class Model:
    """Наследуемые свойства, управление версиями и объявления зависимостей."""

    properties: dict = field(default_factory=dict)
    managed: dict = field(default_factory=dict)
    dependencies: dict = field(default_factory=dict)


def xml_document(data):
    """Прочитать POM и убрать пространства имён для единых XPath."""
    try:
        root = et.fromstring(data)
    except et.ParseError as error:
        raise ValueError(f"некорректный XML: {error}") from error
    for element in root.iter():
        element.tag = element.tag.rsplit("}", 1)[-1]
    return root


def expand(value, properties):
    """Подставить вложенные свойства, отклоняя циклы и неизвестные имена."""
    for _ in range(MAX_PROPERTY_PASSES):
        if not PROPERTY.search(value):
            return value
        replaced = PROPERTY.sub(
            lambda match: properties.get(match[1], match[0]), value
        )
        if replaced == value:
            break
        value = replaced
    raise ValueError(f"неразрешённое или циклическое свойство: {value}")


def declaration(element):
    """Прочитать поля зависимости, включая exclusions."""
    values = {child.tag: (child.text or "").strip() for child in element}
    if element.find("exclusions") is not None:
        values["exclusions"] = frozenset(
            (item.findtext("groupId", ""), item.findtext("artifactId", ""))
            for item in element.findall("exclusions/exclusion")
        )
    return values


def dependency_key(values):
    """Использовать Maven-ключ для наследования и dependencyManagement."""
    return (
        values.get("groupId", ""),
        values.get("artifactId", ""),
        values.get("type", "jar"),
        values.get("classifier", ""),
    )


def resolved_fields(values, properties):
    """Подставить свойства в обычные поля и пары исключений."""
    result = {}
    for key, value in values.items():
        if key == "exclusions":
            result[key] = frozenset(
                (expand(group, properties), expand(name, properties))
                for group, name in value
            )
        else:
            result[key] = expand(value, properties)
    return result


def coordinates(value):
    """Разобрать точные координаты; диапазоны не подменять версиями."""
    parts = value.split(":")
    if len(parts) != COORDINATE_PARTS or not COORDINATES.fullmatch(value):
        raise ValueError(f"нужны точные координаты Maven: {value}")
    return parts


def package_name(fields):
    """Собрать координаты из полей POM."""
    return ":".join(fields.get(key, "") for key in COORDINATE_KEYS)


def to_dependency(values, model):
    """Дополнить объявление настройками управления зависимостями."""
    resolved = resolved_fields(values, model.properties)
    defaults = model.managed.get(dependency_key(resolved), {})
    merged = {**resolved_fields(defaults, model.properties), **resolved}
    package = package_name(merged)
    coordinates(package)
    return Dependency(
        package,
        merged.get("scope", "compile"),
        merged.get("optional", "false") == "true",
        merged.get("exclusions", frozenset()),
    )
