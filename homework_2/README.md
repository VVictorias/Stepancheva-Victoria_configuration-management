# Домашняя работа №2

**Вариант 22. Визуализация графа зависимостей Java Maven.**

Программа читает POM, строит граф обходом в глубину (DFS) и находит циклы.
[Отчёт с примерами всех пяти этапов](../homework_2.md).

## Запуск

Нужен Python 3.9 или новее. Mermaid для графа в браузере загружается
из интернета, Maven нужен для сравнения.

```bash
cd homework_2
```

```bash
bash run.sh --package junit:junit:4.13.2 \
  --repository https://repo.maven.apache.org/maven2/ --ascii-tree
```

- `--package` задаёт координаты Maven `groupId:artifactId[:version]` или букву A–Z.
- `--repository` задаёт адрес HTTP(S) или путь к файлу. Для файла нужен `--test-repository`.
- `--mode` выбирает настройки (`config`), прямые зависимости (`direct`), граф (`graph`),
  порядок (`order`) или диаграмму (`visualize`, по умолчанию).
- `--ascii-tree` добавляет дерево. `--output` задаёт папку для `graph.mmd` и `graph.html`.
- `--no-open` сохраняет файлы без открытия браузера. `--help` показывает справку.

Пример для тестового файла. Строка `A: B C` означает, что A зависит от B и C,
а `D:` задаёт пакет без зависимостей.

```bash
bash run.sh --package A --repository examples/diamond.txt --test-repository --mode order
```

## Код и тесты

- `run.sh` запускает программу. В `src/depgraph` файлы `config.py` и `cli.py` отвечают за параметры и режимы.
- `maven.py` и `model.py` читают POM. `repository.py` читает тестовые файлы.
- `graph.py` строит граф, `visualize.py` создаёт Mermaid, HTML и ASCII-дерево.
- В `examples` лежат тестовые графы и проверочные POM.

```bash
python3 -B -m unittest discover -s tests -v
```

15 тестов проверяют параметры, POM, графы, циклы, порядок и визуализацию.

## Работа с Maven

Поддерживаются родительские POM, управляемые версии и BOM. Если версия не указана,
берётся `release` из `maven-metadata.xml`. Граф учитывает `compile` и `runtime`
с исключениями, без тестовых и необязательных зависимостей. Правило ближайшей версии,
профили, диапазоны версий, SNAPSHOT с меткой времени и дополнительные репозитории
из POM не поддерживаются.
