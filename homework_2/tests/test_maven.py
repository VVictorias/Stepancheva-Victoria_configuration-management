"""Изолированные проверки POM, наследования и сетевых ошибок."""

from importlib import import_module
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.error import URLError

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

    def test_direct_scopes_and_exclusions(self):
        """Сохранить scope, optional и исключения прямых зависимостей."""
        extra = (
            "<scope>test</scope><optional>true</optional><exclusions>"
            "<exclusion><groupId>x</groupId><artifactId>y</artifactId>"
            "</exclusion></exclusions>"
        )
        repo = self.repo(
            {
                "g/a/1/a-1.pom": "<dependencies>"
                + dep(extra=extra)
                + "</dependencies>"
            }
        )
        (item,) = repo.direct("g:a:1")
        self.assertEqual(item.package, "g:b:1")
        self.assertEqual(item.scope, "test")
        self.assertTrue(item.optional)
        self.assertIn(("x", "y"), item.exclusions)

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

    def test_bom_and_cache(self):
        """Импортировать BOM и повторно не загружать готовую модель."""
        bom = (
            "<properties><bom.version>1</bom.version></properties>"
            "<dependencyManagement><dependencies>"
            + dep(version="${bom.version}")
            + "</dependencies></dependencyManagement>"
        )
        root = (
            "<dependencyManagement><dependencies>"
            + dep("bom", extra="<scope>import</scope><type>pom</type>")
            + "</dependencies></dependencyManagement><dependencies>"
            "<dependency><groupId>g</groupId><artifactId>b</artifactId>"
            "</dependency></dependencies>"
        )
        repo = self.repo({"g/bom/1/bom-1.pom": bom, "g/a/1/a-1.pom": root})
        self.assertEqual(repo.direct("g:a:1")[0].package, "g:b:1")
        repo.document = lambda path: self.fail("cache miss")
        self.assertEqual(repo.direct("g:a:1")[0].package, "g:b:1")

    def test_managed_exclusions(self):
        """Не потерять exclusions, заданные через dependencyManagement."""
        exclusions = (
            "<exclusions><exclusion><groupId>x</groupId>"
            "<artifactId>*</artifactId></exclusion></exclusions>"
        )
        body = (
            "<dependencyManagement><dependencies>"
            + dep(extra=exclusions)
            + "</dependencies></dependencyManagement><dependencies>"
            "<dependency><groupId>g</groupId><artifactId>b</artifactId>"
            "</dependency></dependencies>"
        )
        repo = self.repo({"g/a/1/a-1.pom": body})
        self.assertEqual(
            repo.direct("g:a:1")[0].exclusions, frozenset({("x", "*")})
        )

    def test_empty_and_bad_pom(self):
        """Лист не имеет зависимостей; повреждённый XML вызывает ошибку."""
        self.assertEqual(self.repo({"g/a/1/a-1.pom": ""}).direct("g:a:1"), [])
        with self.assertRaisesRegex(ValueError, "XML"):
            model_module.xml_document("<project>")

    def test_parent_cycle(self):
        """Отклонить цикл родителей без бесконечной рекурсии."""
        body = (
            "<parent><groupId>g</groupId><artifactId>a</artifactId>"
            "<version>1</version></parent>"
        )
        with self.assertRaisesRegex(ValueError, "цикл"):
            self.repo({"g/a/1/a-1.pom": body}).direct("g:a:1")

    def test_unknown_and_cyclic_properties(self):
        """Не выдавать неразрешённые свойства за координаты пакетов."""
        for properties in [{}, {"v": "${w}", "w": "${v}"}]:
            with self.subTest(properties=properties):
                with self.assertRaisesRegex(ValueError, "свойство"):
                    model_module.expand("${v}", properties)

    def test_missing_version_and_range(self):
        """Отсутствующая версия и диапазон дают явную ошибку."""
        for version in ["", "[1,2)"]:
            repo = self.repo(
                {
                    "g/a/1/a-1.pom": "<dependencies>"
                    + dep(version=version)
                    + "</dependencies>"
                }
            )
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
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

    def test_transport_error(self):
        """Сетевая ошибка преобразуется в понятное исключение."""
        repo = maven.MavenRepository("https://example.org/")
        with patch("depgraph.maven.urlopen", side_effect=URLError("offline")):
            with self.assertRaisesRegex(ValueError, "загрузить.*offline"):
                repo.document("test.pom")


if __name__ == "__main__":
    unittest.main()
