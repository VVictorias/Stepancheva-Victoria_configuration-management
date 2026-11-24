"""Изолированные проверки POM, наследования и сетевых ошибок."""

from importlib import import_module
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
maven = import_module("depgraph.maven")
model_module = import_module("depgraph.model")


def project(body):
    """Создать XML POM с пространством имён Maven."""
    return model_module.xml_document(
        '<project xmlns="http://maven.apache.org/POM/4.0.0">'
        + body
        + "</project>"
    )


def dep(name="b", version="1", extra=""):
    """Сформировать простое объявление зависимости."""
    return (
        f"<dependency><groupId>g</groupId><artifactId>{name}</artifactId>"
        f"<version>{version}</version>{extra}</dependency>"
    )


class MavenTests(unittest.TestCase):
    """Проверить разбор без внешнего сервера и готового Maven resolver."""

    def repo(self, documents):
        """Подменить только транспорт, сохраняя настоящий разбор POM."""
        repository = maven.MavenRepository("https://example.org/")
        repository.document = lambda path: project(documents[path])
        return repository

    def test_parent_properties_and_management(self):
        """Получить версию из parent и применить свойство дочернего POM."""
        parent = (
            "<properties><ver>1</ver></properties>"
            "<dependencyManagement><dependencies>"
            + dep(version="${ver}")
            + "</dependencies></dependencyManagement>"
        )
        child = (
            "<parent><groupId>g</groupId><artifactId>p</artifactId>"
            "<version>1</version></parent>"
            "<properties><ver>2</ver></properties><dependencies>"
            "<dependency><groupId>g</groupId><artifactId>b</artifactId>"
            "</dependency></dependencies>"
        )
        repo = self.repo({"g/p/1/p-1.pom": parent, "g/a/1/a-1.pom": child})
        self.assertEqual(repo.direct("g:a:1")[0].package, "g:b:2")

    def test_bom_scopes_and_exclusions(self):
        """Импортировать версию и исключения, отобрать runtime-зависимости."""
        excludes = (
            "<exclusions><exclusion><groupId>x</groupId>"
            "<artifactId>*</artifactId></exclusion></exclusions>"
        )
        bom = (
            "<properties><ver>2</ver></properties>"
            "<dependencyManagement><dependencies>"
            + dep(version="${ver}", extra=excludes)
            + "</dependencies></dependencyManagement>"
        )
        root = (
            "<dependencyManagement><dependencies>"
            + dep("bom", extra="<scope>import</scope><type>pom</type>")
            + "</dependencies></dependencyManagement><dependencies>"
            "<dependency><groupId>g</groupId><artifactId>b</artifactId>"
            "</dependency>"
            + dep("test", extra="<scope>test</scope>")
            + dep("optional", extra="<optional>true</optional>")
            + "</dependencies>"
        )
        repo = self.repo({"g/bom/1/bom-1.pom": bom, "g/a/1/a-1.pom": root})
        self.assertEqual(
            [item.package for item in repo.direct("g:a:1")],
            ["g:b:2", "g:test:1", "g:optional:1"],
        )
        with patch.object(repo, "document") as load:
            self.assertEqual(
                repo.children("g:a:1", frozenset()),
                [("g:b:2", frozenset({("x", "*")}))],
            )
            self.assertEqual(repo.children("g:a:1", {("g", "*")}), [])
            load.assert_not_called()

    def test_invalid_poms(self):
        """Сообщить об ошибочном XML, цикле parent и неизвестной версии."""
        with self.assertRaisesRegex(ValueError, "XML"):
            model_module.xml_document("<project>")
        cases = (
            ("<parent><groupId>g</groupId><artifactId>a</artifactId>"
             "<version>1</version></parent>", "цикл"),
            ("<dependencies>" + dep(version="${missing}") + "</dependencies>",
             "свойство"),
            ("<dependencies>" + dep(version="[1,2)") + "</dependencies>",
             "точные координаты"),
        )
        for body, message in cases:
            with self.subTest(body=body):
                repo = self.repo({"g/a/1/a-1.pom": body})
                with self.assertRaisesRegex(ValueError, message):
                    repo.direct("g:a:1")

    def test_metadata(self):
        """Использовать release, а не лексикографическую сортировку версий."""
        repo = maven.MavenRepository("https://example.org/")
        repo.document = lambda path: project(
            "<versioning><release>2.10</release></versioning>"
        )
        self.assertEqual(repo.resolve("g:a"), "g:a:2.10")
        repo.document = lambda path: project("")
        with self.assertRaisesRegex(ValueError, "release"):
            repo.resolve("g:a")
