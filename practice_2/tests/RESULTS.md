# Фактический протокол проверки этапа 1

Дата: 11.11.2026. Рабочий каталог — корень репозитория.
Python: `3.14.9`. Все команды выполнены локально.
Ниже stdout и stderr показаны в одном блоке; ошибки CLI идут в stderr.

## Запуск 1

```sh
python3 -m unittest discover -s practice_2/tests -v
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
Ran 15 tests in 1.756s

OK
```

## Запуск 2

```sh
sh practice_2/run.sh --package org.apache.commons:commons-lang3:3.12.0 \
  --repository https://repo.maven.apache.org/maven2/ --ascii-tree
```

Код завершения: `0`.

```text
package=org.apache.commons:commons-lang3:3.12.0
repository=https://repo.maven.apache.org/maven2/
test_repository=false
ascii_tree=true
```

## Запуск 3

```sh
sh practice_2/run.sh --package A --repository practice_2/tests/fixtures/repository.txt --test-repository
```

Код завершения: `0`.

```text
package=A
repository=practice_2/tests/fixtures/repository.txt
test_repository=true
ascii_tree=false
```

## Запуск 4

```sh
sh practice_2/run.sh --repository https://repo.example.org/
```

Код завершения: `2`.

```text
usage: cli.py [-h] --package PACKAGE --repository REPOSITORY
              [--test-repository] [--ascii-tree]
Ошибка: не указаны обязательные параметры: --package
Справка: --help
```

## Запуск 5

```sh
sh practice_2/run.sh --package 'bad name' --repository https://repo.example.org/
```

Код завершения: `2`.

```text
usage: cli.py [-h] --package PACKAGE --repository REPOSITORY
              [--test-repository] [--ascii-tree]
Ошибка: --package: ожидается groupId:artifactId[:version] без пробелов
Справка: --help
```

## Запуск 6

```sh
sh practice_2/run.sh --package g:a --repository
```

Код завершения: `2`.

```text
usage: cli.py [-h] --package PACKAGE --repository REPOSITORY
              [--test-repository] [--ascii-tree]
Ошибка: параметр --repository: требуется одно значение
Справка: --help
```

## Запуск 7

```sh
sh practice_2/run.sh --package g:a --repository https://repo.example.org:70000
```

Код завершения: `2`.

```text
usage: cli.py [-h] --package PACKAGE --repository REPOSITORY
              [--test-repository] [--ascii-tree]
Ошибка: --repository: порт должен быть числом от 1 до 65535
Справка: --help
```

## Запуск 8

```sh
sh practice_2/run.sh --package A --repository practice_2/tests/fixtures/missing.txt --test-repository
```

Код завершения: `2`.

```text
usage: cli.py [-h] --package PACKAGE --repository REPOSITORY
              [--test-repository] [--ascii-tree]
Ошибка: --repository: файл не существует или путь указывает на каталог
Справка: --help
```

## Запуск 9

```sh
sh practice_2/run.sh --package A --repository https://repo.example.org/ --test-repository
```

Код завершения: `2`.

```text
usage: cli.py [-h] --package PACKAGE --repository REPOSITORY
              [--test-repository] [--ascii-tree]
Ошибка: --repository: тестовый режим требует путь к файлу, а не URL
Справка: --help
```

## Запуск 10

```sh
sh practice_2/run.sh --package g:a --repository practice_2/tests/fixtures/repository.txt
```

Код завершения: `2`.

```text
usage: cli.py [-h] --package PACKAGE --repository REPOSITORY
              [--test-repository] [--ascii-tree]
Ошибка: --repository: нужен HTTP(S) URL; для файла нужен тестовый режим
Справка: --help
```

## Запуск 11

```sh
sh practice_2/run.sh --package g:a --repository https://repo.example.org/ --test-repository=false
```

Код завершения: `2`.

```text
usage: cli.py [-h] --package PACKAGE --repository REPOSITORY
              [--test-repository] [--ascii-tree]
Ошибка: параметр --test-repository: флаг не принимает значение 'false'
Справка: --help
```

## Запуск 12

```sh
sh practice_2/run.sh --package g:a --repository https://repo.example.org/ --ascii-tree yes
```

Код завершения: `2`.

```text
usage: cli.py [-h] --package PACKAGE --repository REPOSITORY
              [--test-repository] [--ascii-tree]
Ошибка: неизвестные параметры или значения: yes
Справка: --help
```

## Дополнительные проверки

Проверка PEP8: `pycodestyle 2.15.0`, предел 79 символов.
Код завершения 0, замечаний нет. Проверка `sh -n practice_2/run.sh`: код 0.
Проверены docstring модулей, классов и функций; длина функций не превышает 40 строк.
