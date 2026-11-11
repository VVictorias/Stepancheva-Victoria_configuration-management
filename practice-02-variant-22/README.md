# Практическое занятие №2. Вариант 22

Выполнила Степанчева Виктория Александровна.

Группа ИКБО-16-25.

**Тема работы**\
Граф зависимостей пакетов Java Maven.

Выполнен этап 1 — «Минимальный прототип с конфигурацией».
Программа принимает четыре параметра командной строки, проверяет
их и выводит настройки в формате `ключ=значение`.

---

<details>
<summary>Перейти к разделу</summary>

1. [Запуск и проверка](#запуск-и-проверка)
2. [Этап 1. Параметры командной строки](#этап-1-параметры-командной-строки)
3. [Обработка ошибок](#обработка-ошибок)
4. [Структура работы](#структура-работы)
5. [Отчёт](stage_1.md) и [результаты запусков](tests/RESULTS.md)

</details>

## Запуск и проверка

Команды выполняются в каталоге `practice-02-variant-22`.
Для запуска нужен Python 3.9 или новее. Сторонние пакеты и Maven
не требуются.

```bash
bash run.sh --package junit:junit:4.13.2 --repository https://repo.maven.apache.org/maven2/ --ascii-tree
python3 -B -m unittest discover -s tests -v
```

Первая команда выводит настройки, вторая запускает автоматические тесты.
На macOS с Python 3.14.9 прошли 15 тестовых методов.
Полный вывод сохранён в [протоколе проверки](tests/RESULTS.md).

Прямой запуск и справка:

```bash
python3 -B src/main.py --package A --repository examples/repository.txt --test-repository
bash run.sh --help
```

## Этап 1. Параметры командной строки

| Параметр | Значение |
| --- | --- |
| `--package ИМЯ` | Обязательные координаты Maven `groupId:artifactId[:version]`. В тестовом режиме — буква A–Z. |
| `--repository ИСТОЧНИК` | Обязательный HTTP(S) URL. В тестовом режиме — путь к существующему файлу. |
| `--test-repository` | Включает режим локального тестового репозитория. По умолчанию выключен. |
| `--ascii-tree` | Включает настройку ASCII-дерева. По умолчанию выключен. |

Запуск с репозиторием Maven:

```bash
bash run.sh --package junit:junit:4.13.2 --repository https://repo.maven.apache.org/maven2/ --ascii-tree
```

```text
package=junit:junit:4.13.2
repository=https://repo.maven.apache.org/maven2/
test_repository=false
ascii_tree=true
```

Запуск с локальным файлом:

```bash
bash run.sh --package A --repository examples/repository.txt --test-repository
```

```text
package=A
repository=examples/repository.txt
test_repository=true
ascii_tree=false
```

Оба флага задаются без значения: наличие означает `true`, отсутствие — `false`.
Флаг ASCII-дерева на первом этапе только отражается в конфигурации.
Загрузка зависимостей, разбор тестового графа и визуализация относятся
к этапам 2–5 и в этой версии отсутствуют.

## Обработка ошибок

Имя Maven должно содержать непустые groupId и artifactId, версия необязательна.
В частях координат допускаются латинские буквы, цифры, `_`, `-` и точки;
сегменты groupId разделяются точками. Пробелы и пустые сегменты запрещены.
В тестовом режиме принимается одна большая латинская буква.

У URL проверяются схема HTTP(S), имя сервера, порт и экранирование.
Авторизация в URL, query и fragment не поддерживаются.
Проверка синтаксическая: сетевые запросы не выполняются.
Локальный источник должен быть обычным файлом, доступным для чтения.
Относительные пути отсчитываются от текущего каталога; поддерживается `~`.
Содержимое и расширение файла на первом этапе не проверяются.

| Ошибка | Пример запуска |
| --- | --- |
| Нет имени пакета | `bash run.sh --repository https://repo.maven.apache.org/maven2/` |
| Нет источника | `bash run.sh --package junit:junit` |
| Нет значения опции | `bash run.sh --package junit:junit --repository` |
| Неверное имя | `bash run.sh --package /bad --repository https://repo.maven.apache.org/maven2/` |
| Неверный URL | `bash run.sh --package junit:junit --repository ftp://example.org/` |
| Файл не найден | `bash run.sh --package A --repository missing.txt --test-repository` |
| URL в тестовом режиме | `bash run.sh --package A --repository https://example.org/ --test-repository` |
| Файл без тестового режима | `bash run.sh --package junit:junit --repository examples/repository.txt` |
| Значение у тестового флага | `bash run.sh --package A --repository examples/repository.txt --test-repository=false` |
| Значение у ASCII-флага | `bash run.sh --package A --repository examples/repository.txt --ascii-tree=maybe` |

Ошибка печатается в stderr с кодом завершения `2`. При успешном запуске
код равен `0`, в stdout выводятся все четыре настройки.
Неизвестные и сокращённые опции отклоняются.
В [протоколе](tests/RESULTS.md) приведены фактические сообщения ошибок.

## Структура работы

```text
practice-02-variant-22/
├── README.md
├── stage_1.md
├── .gitignore
├── run.sh
├── src/
│   ├── main.py
│   └── depgraph/
│       ├── __init__.py
│       ├── cli.py
│       └── config.py
├── examples/
│   └── repository.txt
└── tests/
    ├── test_cli.py
    └── RESULTS.md
```

`main.py` — точка входа. В `config.py` находятся описание аргументов
и проверки значений, в `cli.py` — вывод конфигурации.
`examples/repository.txt` используется для проверки передачи локального пути.

Задание: «ИКБО-16-25-1.pdf», вариант 22, страницы 71–73.
Правила оформления репозитория — страницы 5–6.
