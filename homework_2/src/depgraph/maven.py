"""Получение POM по HTTP(S) без менеджеров пакетов и внешних библиотек."""

from pathlib import Path
import ssl
from urllib.request import Request, urlopen

from .model import (
    COORDINATE_KEYS,
    Model,
    coordinates,
    declaration,
    dependency_key,
    expand,
    package_name,
    resolved_fields,
    to_dependency,
    xml_document,
)


RUNTIME_SCOPES = {"compile", "runtime"}
VERSIONLESS_PARTS = 2
TIMEOUT_SECONDS = 20
MAX_DOCUMENT_BYTES = 4 * 1024 * 1024
MAX_MODEL_DEPTH = 64
SYSTEM_CERTIFICATES = Path("/etc/ssl/cert.pem")


class MavenRepository:
    """Загружать документы и собирать наследуемую модель POM с кешем."""

    def __init__(self, url):
        """Запомнить единственный выбранный пользователем репозиторий."""
        self.url = url.rstrip("/") + "/"
        self.models = {}
        self.active = set()
        self.context = ssl.create_default_context()
        if SYSTEM_CERTIFICATES.is_file():
            self.context.load_verify_locations(str(SYSTEM_CERTIFICATES))

    def document(self, relative):
        """Загрузить ограниченный по размеру XML с проверкой TLS."""
        url = self.url + relative
        request = Request(url, headers={"User-Agent": "depgraph-homework/1"})
        try:
            with urlopen(
                request, timeout=TIMEOUT_SECONDS, context=self.context
            ) as response:
                data = response.read(MAX_DOCUMENT_BYTES + 1)
        except OSError as error:
            raise ValueError(f"не удалось загрузить {url}: {error}") from error
        if len(data) > MAX_DOCUMENT_BYTES:
            raise ValueError(f"документ слишком большой: {url}")
        return xml_document(data)

    def resolve(self, package):
        """При пропуске версии выбрать release из maven-metadata.xml."""
        parts = package.split(":")
        if len(parts) == VERSIONLESS_PARTS:
            group, artifact = parts
            path = f"{group.replace('.', '/')}/{artifact}/maven-metadata.xml"
            root = self.document(path)
            version = root.findtext("versioning/release")
            if not version:
                raise ValueError(f"в metadata нет release для {package}")
            package += ":" + version.strip()
        coordinates(package)
        return package

    def model(self, package):
        """Собрать POM с защитой от циклических parent и BOM."""
        if package in self.models:
            return self.models[package]
        if package in self.active:
            raise ValueError(f"цикл наследования POM или BOM: {package}")
        if len(self.active) >= MAX_MODEL_DEPTH:
            raise ValueError("слишком глубокое наследование POM")
        self.active.add(package)
        try:
            model = self.read_model(package)
            self.models[package] = model
            return model
        finally:
            self.active.remove(package)

    def read_model(self, package):
        """Загрузить POM, унаследовать parent и применить дочерние поля."""
        group, artifact, version = coordinates(package)
        base = f"{group.replace('.', '/')}/{artifact}/{version}/"
        root = self.document(f"{base}{artifact}-{version}.pom")
        if root.tag != "project":
            raise ValueError(f"ожидался корневой элемент project: {package}")
        parent = self.parent_model(root)
        properties = {
            **parent.properties, **project_properties(root, package)
        }
        model = Model(
            properties, dict(parent.managed), dict(parent.dependencies)
        )
        self.read_management(root, model)
        for item in root.findall("dependencies/dependency"):
            values = declaration(item)
            key = dependency_key(resolved_fields(values, properties))
            model.dependencies[key] = values
        return model

    def parent_model(self, root):
        """Получить родительский POM из того же репозитория."""
        parent = root.find("parent")
        if parent is None:
            return Model()
        fields = {
            key: parent.findtext(key, "").strip() for key in COORDINATE_KEYS
        }
        return self.model(expand(package_name(fields), raw_properties(root)))

    def read_management(self, root, model):
        """Импортировать BOM, затем применить локальное управление."""
        path = "dependencyManagement/dependencies/dependency"
        local = {}
        imported = {}
        for item in root.findall(path):
            raw = declaration(item)
            values = resolved_fields(raw, model.properties)
            if values.get("scope") == "import":
                bom = self.model(package_name(values))
                for key, value in bom.managed.items():
                    imported.setdefault(
                        key, resolved_fields(value, bom.properties)
                    )
            else:
                local[dependency_key(values)] = raw
        model.managed.update(imported)
        model.managed.update(local)

    def direct(self, package):
        """Вернуть все прямые объявления, включая test и optional."""
        model = self.model(package)
        return [
            to_dependency(item, model) for item in model.dependencies.values()
        ]

    def children(self, package, exclusions):
        """Вернуть runtime-соседей с исключениями для следующего шага."""
        return [
            (item.package, exclusions | item.exclusions)
            for item in self.direct(package)
            if item.scope in RUNTIME_SCOPES
            and not item.optional
            and not excluded(item.package, exclusions)
        ]


def excluded(package, exclusions):
    """Проверить groupId и artifactId по списку исключений."""
    group, name, _ = package.split(":")
    return any(
        left in (group, "*") and right in (name, "*")
        for left, right in exclusions
    )


def raw_properties(root):
    """Прочитать свойства, заданные в POM."""
    return {
        item.tag: (item.text or "").strip()
        for item in root.findall("properties/*")
    }


def project_properties(root, package):
    """Добавить свойства project, pom и project.parent."""
    result = raw_properties(root)
    for key, value in zip(COORDINATE_KEYS, package.split(":")):
        result[f"project.{key}"] = result[f"pom.{key}"] = value
    for key in COORDINATE_KEYS:
        value = root.findtext(f"parent/{key}")
        if value is not None:
            result[f"project.parent.{key}"] = value.strip()
    return result
