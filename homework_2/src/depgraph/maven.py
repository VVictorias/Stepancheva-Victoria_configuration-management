"""Получение POM по HTTP(S) без менеджеров пакетов и внешних библиотек."""

from pathlib import Path
import ssl
from urllib.error import URLError
from urllib.request import Request, urlopen

from .model import (
    Model,
    coordinates,
    declaration,
    dependency_key,
    expand,
    resolved_fields,
    to_dependency,
    xml_document,
)


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
        except (OSError, URLError) as error:
            raise ValueError(f"не удалось загрузить {url}: {error}") from error
        if len(data) > MAX_DOCUMENT_BYTES:
            raise ValueError(f"документ слишком большой: {url}")
        return xml_document(data)

    def resolve(self, package):
        """При пропуске версии выбрать release из maven-metadata.xml."""
        if package.count(":") == 1:
            group, artifact = package.split(":")
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
        properties = dict(parent.properties)
        properties.update(self.project_properties(root, package))
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
        fields = (
            parent.findtext(key, "").strip()
            for key in ("groupId", "artifactId", "version")
        )
        properties = self.raw_properties(root)
        package = expand(":".join(fields), properties)
        return self.model(package)

    def raw_properties(self, root):
        """Извлечь пользовательские свойства текущего POM."""
        element = root.find("properties")
        if element is None:
            return {}
        return {item.tag: (item.text or "").strip() for item in element}

    def project_properties(self, root, package):
        """Добавить стандартные project/pom и parent-псевдонимы."""
        group, artifact, version = coordinates(package)
        result = self.raw_properties(root)
        for prefix in ("project", "pom"):
            for key, value in zip(
                ("groupId", "artifactId", "version"),
                (group, artifact, version),
            ):
                result[f"{prefix}.{key}"] = value
        parent = root.find("parent")
        if parent is not None:
            for key in ("groupId", "artifactId", "version"):
                result[f"project.parent.{key}"] = parent.findtext(key, "")
        return result

    def read_management(self, root, model):
        """Импортировать BOM, затем применить локальное управление."""
        items = [
            declaration(item)
            for item in root.findall(
                "dependencyManagement/dependencies/dependency"
            )
        ]
        local = []
        imported = {}
        for raw in items:
            values = resolved_fields(raw, model.properties)
            if values.get("scope") == "import":
                package = ":".join(
                    values.get(key, "")
                    for key in ("groupId", "artifactId", "version")
                )
                for key, value in self.model(package).managed.items():
                    imported.setdefault(key, value)
            else:
                local.append((dependency_key(values), raw))
        model.managed.update(imported)
        model.managed.update(local)

    def direct(self, package):
        """Вернуть все прямые объявления, включая test и optional."""
        model = self.model(package)
        return [
            to_dependency(item, model) for item in model.dependencies.values()
        ]
