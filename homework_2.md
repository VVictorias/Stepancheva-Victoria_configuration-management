# Домашняя работа №2

**Вариант 22.** Визуализация графа зависимостей Java Maven.

Для запуска нужен Python 3.9 или новее. Для сравнения результатов
нужна команда `mvn`. Начните в корне репозитория и выполняйте
команды в одном терминале.

```bash
cd homework_2
repo=https://repo.maven.apache.org/maven2/
```

## Этап 1. Настройка программы

Программа читает параметры через `argparse`, проверяет имя пакета
и адрес репозитория или путь к файлу. Режим `config` показывает
значения параметров до загрузки POM.

```bash
bash run.sh --package junit:junit:4.13.2 --repository "$repo" \
  --ascii-tree --mode config
```

```text
package=junit:junit:4.13.2
repository=https://repo.maven.apache.org/maven2/
test_repository=false
ascii_tree=true
```

Следующие четыре команды проверяют обработку ошибок.

```bash
bash run.sh --mode config --package junit --repository "$repo" || echo "Код: $?"
bash run.sh --mode config --package junit:junit:4.13.2 \
  --repository ftp://example.org || echo "Код: $?"
bash run.sh --mode config --package A --repository examples/chain.txt \
  --test-repository=true || echo "Код: $?"
bash run.sh --mode config --package junit:junit:4.13.2 --repository "$repo" \
  --ascii-tree=true || echo "Код: $?"
```

Во всех четырёх случаях получен код 2 и сообщение с именем ошибочного
параметра. Флаги `--test-repository` и `--ascii-tree` передаются без
значений.

## Этап 2. Прямые зависимости

Программа составляет путь к POM из координат пакета, загружает файл через
`urllib.request` и читает XML через `xml.etree.ElementTree`. При разборе
учитываются родительский POM, свойства и управляемые версии.

```bash
bash run.sh --package junit:junit:4.13.2 --repository "$repo" --mode direct
```

```text
org.hamcrest:hamcrest-core:1.3
org.hamcrest:hamcrest-library:1.3
```

Из POM JUnit получены два прямых объявления. `hamcrest-library` имеет область
`test`. Этот режим показывает все прямые объявления, включая тестовые.

## Этап 3. Построение графа

Граф транзитивных зависимостей строится обходом в глубину (DFS) без
рекурсии. При проверке циклов программа отмечает рёбра к вершинам,
которые ещё находятся в стеке. Из Maven POM в
граф потребителя входят зависимости с областями `compile` и `runtime`
с учётом `optional` и `exclusions`.

```bash
for file in chain diamond cycle; do
  bash run.sh --package A --repository "examples/$file.txt" \
    --test-repository --mode graph
done
```

В цепочке получены связи `A → B → C`. В ромбе обе ветви ведут к `D`.
При обходе третьего примера программа завершила построение графа и вывела
`Цикл: C -> A`.

## Этап 4. Порядок загрузки

Программа добавляет вершину в список после обхода её зависимостей.
Поэтому зависимость появляется раньше пакета, который её использует.
Корневой пакет в список не входит.

```bash
for file in chain diamond cycle; do
  bash run.sh --package A --repository "examples/$file.txt" \
    --test-repository --mode order || echo "Код: $?"
done
bash run.sh --package junit:junit:4.13.2 --repository "$repo" --mode order
```

Для цепочки получен порядок `C, B`, для ромба `D, B, C`. Граф с циклом
дал ошибку и код 1. Для JUnit программа вывела
`org.hamcrest:hamcrest-core:1.3`.
При сравнении в Maven 3.9.11 команда `dependency:build-classpath` поставила
JAR JUnit перед JAR Hamcrest Core. Classpath задаёт порядок поиска
классов, а порядок DFS показывает, какие зависимости нужны
до обработки пакета.

## Этап 5. Визуализация

Программа записывает Mermaid в `graph.mmd`, открывает `graph.html`
в браузере и выводит ASCII-дерево при флаге `--ascii-tree`.

```bash
demo="$(mktemp -d)"
packages=(junit:junit:4.13.2 org.hamcrest:hamcrest:2.2 org.slf4j:slf4j-simple:2.0.17)
for package in "${packages[@]}"; do
  IFS=: read -r group artifact version <<< "$package"
  bash run.sh --package "$package" --repository "$repo" --ascii-tree \
    --output "$demo/$artifact"
done
```

```mermaid
flowchart TD
    n0["junit:junit:4.13.2"]
    n1["org.hamcrest:hamcrest-core:1.3"]
    n0 --> n1
```

```mermaid
flowchart TD
    n0["org.hamcrest:hamcrest:2.2"]
```

```mermaid
flowchart TD
    n0["org.slf4j:slf4j-simple:2.0.17"]
    n1["org.slf4j:slf4j-api:2.0.17"]
    n0 --> n1
```

В ASCII-дереве JUnit показан Hamcrest Core, в дереве SLF4J Simple
показан SLF4J API. У Hamcrest 2.2 дерево состоит из одной вершины.
HTML-страницы всех трёх примеров отобразили диаграммы в браузере.

Для каждого пакета создаётся отдельный проверочный POM.
Maven выводит дерево зависимостей и список JAR-файлов.

```bash
plugin=org.apache.maven.plugins:maven-dependency-plugin:3.8.1
for package in "${packages[@]}"; do
  IFS=: read -r group artifact version <<< "$package"
  mkdir -p "$demo/$artifact"
  pom="$demo/$artifact/pom.xml"
  cat > "$pom" <<EOF
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>demo</groupId><artifactId>check</artifactId><version>1</version>
  <dependencies><dependency>
    <groupId>$group</groupId><artifactId>$artifact</artifactId><version>$version</version>
  </dependency></dependencies>
</project>
EOF
  mvn -B -f "$pom" "$plugin:tree" "$plugin:build-classpath"
done
```

После исключения корня проверочного проекта дерево Maven совпало с
каждым из трёх графов. Режим `direct` для SLF4J Simple дополнительно
показывает тестовый JUnit и второе объявление SLF4J API с типом
`test-jar`. В граф потребителя эти тестовые зависимости не входят.

## Тестирование

```bash
python3 -B -m unittest discover -s tests -v
```

Все 15 тестов прошли. Проверены параметры, чтение POM, тестовые графы,
циклы, порядок загрузки, Mermaid и ASCII-дерево.
