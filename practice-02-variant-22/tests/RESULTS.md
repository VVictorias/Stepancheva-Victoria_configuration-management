# Проверка этапа 1. Вариант 22

Дата: 11.11.2026. Все команды выполнены в `practice-02-variant-22`.
Среда: macOS, Python 3.14.9.
stdout и stderr приведены вместе; ошибки CLI выводятся в stderr.

## Запуск 1

```bash
python3 -B -m unittest discover -s tests -v
```

Код завершения: `0`.

```text
test_coordinates_and_urls (test_cli.CliTests.test_coordinates_and_urls)
Принять координаты без версии, HTTP, порт и IPv6. ... ok
test_flag_misuse (test_cli.CliTests.test_flag_misuse)
Флаги не принимают true/false и другие отдельные значения. ... ok
test_help (test_cli.CliTests.test_help)
Справка доступна без обязательных параметров. ... ok
test_invalid_file (test_cli.CliTests.test_invalid_file)
Отклонить пустой путь, отсутствующий файл, каталог и file URL. ... ok
test_invalid_package (test_cli.CliTests.test_invalid_package)
Отклонить пустые, неполные и повреждённые координаты Maven. ... ok
test_invalid_test_package (test_cli.CliTests.test_invalid_test_package)
Тестовые имена должны состоять из одной большой латинской буквы. ... ok
test_invalid_url (test_cli.CliTests.test_invalid_url)
Отклонить неверную схему, сервер, порт и запрещённые части URL. ... ok
test_launcher_from_other_directory (test_cli.CliTests.test_launcher_from_other_directory)
Скрипт запуска работает с путями, содержащими пробелы. ... ok
test_missing_required_values (test_cli.CliTests.test_missing_required_values)
Проверить отсутствие каждого обязательного параметра и значения. ... ok
test_remote_ascii_setting (test_cli.CliTests.test_remote_ascii_setting)
Включение настройки дерева не запускает построение графа. ... ok
test_remote_defaults (test_cli.CliTests.test_remote_defaults)
Вывести все настройки, включая значения выключенных флагов. ... ok
test_source_mode_mismatch (test_cli.CliTests.test_source_mode_mismatch)
Отклонить URL в тестовом режиме и путь без тестового режима. ... ok
test_test_mode_flag_combinations (test_cli.CliTests.test_test_mode_flag_combinations)
Проверить тестовый источник с обоими состояниями ASCII-флага. ... ok
test_unreadable_file (test_cli.CliTests.test_unreadable_file)
Детерминированно проверить запрет чтения при любых правах ОС. ... ok
test_unsupported_options (test_cli.CliTests.test_unsupported_options)
Отклонить неизвестные опции, сокращения и поздние параметры. ... ok

----------------------------------------------------------------------
Ran 15 tests in 1.774s

OK
```

## Запуск 2

```bash
bash run.sh --package junit:junit:4.13.2 --repository https://repo.maven.apache.org/maven2/ --ascii-tree
```

Код завершения: `0`.

```text
package=junit:junit:4.13.2
repository=https://repo.maven.apache.org/maven2/
test_repository=false
ascii_tree=true
```

## Запуск 3

```bash
bash run.sh --package A --repository examples/repository.txt --test-repository
```

Код завершения: `0`.

```text
package=A
repository=examples/repository.txt
test_repository=true
ascii_tree=false
```

## Запуск 4

```bash
python3 -B src/main.py --package A --repository examples/repository.txt --test-repository
```

Код завершения: `0`.

```text
package=A
repository=examples/repository.txt
test_repository=true
ascii_tree=false
```

## Запуск 5

```bash
bash run.sh --help
```

Код завершения: `0`.

```text
usage: main.py [-h] --package PACKAGE --repository REPOSITORY
               [--test-repository] [--ascii-tree]

Maven: этап 1, только проверка и вывод конфигурации.

options:
  -h, --help            show this help message and exit
  --package PACKAGE     groupId:artifactId[:version]; в тестовом режиме буква
                        A-Z
  --repository REPOSITORY
                        HTTP(S) URL или путь к файлу при --test-repository
  --test-repository     использовать локальный тестовый файл; значение не
                        требуется
  --ascii-tree          сохранить настройку ASCII-дерева; значение не
                        требуется
```

## Запуск 6

```bash
bash run.sh --repository https://repo.maven.apache.org/maven2/
```

Код завершения: `2`.

```text
usage: main.py [-h] --package PACKAGE --repository REPOSITORY
               [--test-repository] [--ascii-tree]
Ошибка: не указаны обязательные параметры: --package
Справка: --help
```

## Запуск 7

```bash
bash run.sh --package junit:junit
```

Код завершения: `2`.

```text
usage: main.py [-h] --package PACKAGE --repository REPOSITORY
               [--test-repository] [--ascii-tree]
Ошибка: не указаны обязательные параметры: --repository
Справка: --help
```

## Запуск 8

```bash
bash run.sh --package junit:junit --repository
```

Код завершения: `2`.

```text
usage: main.py [-h] --package PACKAGE --repository REPOSITORY
               [--test-repository] [--ascii-tree]
Ошибка: параметр --repository: требуется одно значение
Справка: --help
```

## Запуск 9

```bash
bash run.sh --package /bad --repository https://repo.maven.apache.org/maven2/
```

Код завершения: `2`.

```text
usage: main.py [-h] --package PACKAGE --repository REPOSITORY
               [--test-repository] [--ascii-tree]
Ошибка: --package: ожидается groupId:artifactId[:version] без пробелов
Справка: --help
```

## Запуск 10

```bash
bash run.sh --package junit:junit --repository ftp://example.org/
```

Код завершения: `2`.

```text
usage: main.py [-h] --package PACKAGE --repository REPOSITORY
               [--test-repository] [--ascii-tree]
Ошибка: --repository: нужен HTTP(S) URL; для файла нужен тестовый режим
Справка: --help
```

## Запуск 11

```bash
bash run.sh --package A --repository missing.txt --test-repository
```

Код завершения: `2`.

```text
usage: main.py [-h] --package PACKAGE --repository REPOSITORY
               [--test-repository] [--ascii-tree]
Ошибка: --repository: файл не существует или путь указывает на каталог
Справка: --help
```

## Запуск 12

```bash
bash run.sh --package A --repository https://example.org/ --test-repository
```

Код завершения: `2`.

```text
usage: main.py [-h] --package PACKAGE --repository REPOSITORY
               [--test-repository] [--ascii-tree]
Ошибка: --repository: тестовый режим требует путь к файлу, а не URL
Справка: --help
```

## Запуск 13

```bash
bash run.sh --package junit:junit --repository examples/repository.txt
```

Код завершения: `2`.

```text
usage: main.py [-h] --package PACKAGE --repository REPOSITORY
               [--test-repository] [--ascii-tree]
Ошибка: --repository: нужен HTTP(S) URL; для файла нужен тестовый режим
Справка: --help
```

## Запуск 14

```bash
bash run.sh --package A --repository examples/repository.txt --test-repository=false
```

Код завершения: `2`.

```text
usage: main.py [-h] --package PACKAGE --repository REPOSITORY
               [--test-repository] [--ascii-tree]
Ошибка: параметр --test-repository: флаг не принимает значение 'false'
Справка: --help
```

## Запуск 15

```bash
bash run.sh --package A --repository examples/repository.txt --ascii-tree=maybe
```

Код завершения: `2`.

```text
usage: main.py [-h] --package PACKAGE --repository REPOSITORY
               [--test-repository] [--ascii-tree]
Ошибка: параметр --ascii-tree: флаг не принимает значение 'maybe'
Справка: --help
```

## Оформление кода

`pycodestyle 2.15.0`, предел 79 символов: код 0, замечаний нет.
`sh -n run.sh`: код 0.
