# Домашняя работа №1

**Вариант:** №22

## Этап 1. REPL

**Цель:** Создать минимальный прототип эмулятора командной оболочки с поддержкой диалога с пользователем.

### 1. Графический интерфейс

Эмулятор реализован на языке Python с использованием библиотеки Tkinter. Создано графическое окно размером 600 × 400 пикселей с областью вывода результатов и полем для ввода команд.

### 2. Заголовок окна

Заголовок формируется автоматически на основе данных операционной системы. Для получения имени пользователя используется `getpass.getuser()`, а для получения имени компьютера — `socket.gethostname()`.

Результат:

```text
Эмулятор - [macbook@MacBook-Pro-macbook-5.local]
```

### 3. Парсер команд

Реализован разбор введённой строки на команду и аргументы. Для раскрытия переменных окружения используется `os.path.expandvars()`, а для разделения строки на части — `split()`.

При вводе `ls $HOME` переменная `$HOME` автоматически заменяется на путь к домашней директории пользователя.

### 4. Команды-заглушки

Реализованы команды `ls` и `cd`. На данном этапе они выводят своё название и аргументы без выполнения операций с файловой системой.

Также реализована обработка неизвестных команд с выводом соответствующей ошибки.

### 5. Команда exit

Реализована команда `exit`, которая завершает работу эмулятора с помощью метода `window.destroy()`.

После ввода команды графическое окно закрывается.

### 6. Демонстрация работы

Работа эмулятора проверена в интерактивном режиме. Выполнены команды `ls`, `cd`, проверены раскрытие переменной окружения `$HOME`, обработка неизвестной команды и завершение программы.

Результаты проверки:

```text
> ls Documents
Команда: ls
Аргументы: ['Documents']

> cd Downloads
Команда: cd
Аргументы: ['Downloads']

> ls $HOME
Команда: ls
Аргументы: ['/Users/macbook']

> hello
Ошибка: неизвестная команда 'hello'
```

При вводе команды `exit` окно эмулятора закрывается.

### Исходный код программы

Файл `src/emulator.py`:

```python
import tkinter as tk
import getpass
import socket
import os

# Получение данных операционной системы
username = getpass.getuser()
hostname = socket.gethostname()

# Создание графического окна
window = tk.Tk()
window.title(f"Эмулятор - [{username}@{hostname}]")
window.geometry("600x400")

# Создание области вывода и поля ввода
output = tk.Text(window)
output.pack(fill=tk.BOTH, expand=True)

entry = tk.Entry(window)
entry.pack(fill=tk.X)


def execute_command(event=None):
    text = entry.get()
    entry.delete(0, tk.END)

    if not text.strip():
        return

    # Разбор команды и раскрытие переменных окружения
    parts = os.path.expandvars(text).split()
    command = parts[0]
    args = parts[1:]

    output.insert(tk.END, f"> {text}\n")

    # Обработка команд
    if command == "ls":
        output.insert(tk.END, "Команда: ls\n")
        output.insert(tk.END, f"Аргументы: {args}\n\n")

    elif command == "cd":
        output.insert(tk.END, "Команда: cd\n")
        output.insert(tk.END, f"Аргументы: {args}\n\n")

    elif command == "exit":
        window.destroy()

    else:
        output.insert(
            tk.END,
            f"Ошибка: неизвестная команда '{command}'\n\n"
        )


entry.bind("<Return>", execute_command)

window.mainloop()
```

### Вывод по этапу 1

В ходе первого этапа разработан графический прототип эмулятора командной оболочки. Реализованы обработка пользовательского ввода, раскрытие переменных окружения, команды-заглушки `ls` и `cd`, команда `exit` и обработка ошибок. Работа программы проверена в интерактивном режиме.

---

## Этап 2. Конфигурация

**Цель:** Реализовать настройку эмулятора с помощью параметров командной строки и автоматическое выполнение команд из стартового скрипта.

### 1. Параметры командной строки

В эмулятор добавлена возможность передачи двух параметров при запуске: пути к виртуальной файловой системе (VFS) и пути к стартовому скрипту.

Для обработки параметров используется модуль `argparse`.

В файл `src/emulator.py` добавлен следующий код:

```python
import argparse

# Получение параметров командной строки
parser = argparse.ArgumentParser()
parser.add_argument("--vfs", help="Путь к архиву VFS")
parser.add_argument("--script", help="Путь к стартовому скрипту")
config = parser.parse_args()
```

Для отображения полученных параметров в графическом окне добавлены строки:

```python
# Вывод параметров запуска
output.insert(tk.END, f"VFS: {config.vfs}\n")
output.insert(tk.END, f"Стартовый скрипт: {config.script}\n\n")
```

Также изменён файл `run.sh`, чтобы переданные при запуске аргументы поступали в Python-программу:

```bash
#!/bin/bash
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 src/emulator.py "$@"
```

Проверка передачи параметров:

```bash
bash run.sh --vfs data/filesystem.zip --script startup.txt
```

Результат:

```text
VFS: data/filesystem.zip
Стартовый скрипт: startup.txt
```

Таким образом, эмулятор получает оба параметра и отображает их значения при запуске.

### 2. Стартовый скрипт

Реализовано автоматическое выполнение команд из текстового файла. Стартовый скрипт поддерживает комментарии, начинающиеся с символа `#`, и пустые строки.

В корневой папке проекта создан файл `startup.txt`:

```text
# Проверка работы стартового скрипта
ls Documents
cd Downloads
ls $HOME

# Проверка неизвестной команды
hello
```

Для выполнения команд из файла изменена функция `execute_command()`. Теперь она может получать команды как из поля ввода, так и из стартового скрипта.

Начало функции:

```python
def execute_command(event=None, text=None):
    if text is None:
        text = entry.get()
        entry.delete(0, tk.END)

    if not text.strip():
        return
```

В конце файла `src/emulator.py`, перед `window.mainloop()`, добавлено чтение стартового скрипта:

```python
# Выполнение команд из стартового скрипта
if config.script:
    try:
        with open(config.script, "r", encoding="utf-8") as file:
            for line in file:
                command_line = line.split("#", 1)[0].strip()

                if command_line:
                    execute_command(text=command_line)

    except OSError as error:
        output.insert(
            tk.END,
            f"Ошибка чтения стартового скрипта: {error}\n\n"
        )
```

При запуске программа читает файл построчно, пропускает комментарии и выполняет команды через существующую функцию `execute_command()`.

Команда проверки:

```bash
bash run.sh --script startup.txt
```

Результат:

```text
VFS: None
Стартовый скрипт: startup.txt

> ls Documents
Команда: ls
Аргументы: ['Documents']

> cd Downloads
Команда: cd
Аргументы: ['Downloads']

> ls $HOME
Команда: ls
Аргументы: ['/Users/macbook']

> hello
Ошибка: неизвестная команда 'hello'
```

Все команды выполнились автоматически, без ручного ввода. Комментарии из файла не выполнялись.

Дополнительно проверена обработка ошибки при отсутствии стартового скрипта:

```bash
bash run.sh --script missing.txt
```

Программа вывела сообщение о невозможности найти файл `missing.txt` и продолжила работу.

### 3. Проверочные скрипты ОС

Для проверки параметров командной строки созданы три Bash-скрипта в папке `tests`.

**Файл `tests/test_vfs.sh`**

```bash
#!/bin/bash

bash run.sh --vfs data/filesystem.zip
```

Команда проверки:

```bash
bash tests/test_vfs.sh
```

Результат:

```text
VFS: data/filesystem.zip
Стартовый скрипт: None
```

Проверена передача только пути к VFS.

**Файл `tests/test_script.sh`**

```bash
#!/bin/bash

bash run.sh --script startup.txt
```

Команда проверки:

```bash
bash tests/test_script.sh
```

Результат: эмулятор получил путь к `startup.txt` и автоматически выполнил команды `ls Documents`, `cd Downloads`, `ls $HOME` и `hello`.

**Файл `tests/test_all.sh`**

```bash
#!/bin/bash

bash run.sh --vfs data/filesystem.zip --script startup.txt
```

Команда проверки:

```bash
bash tests/test_all.sh
```

Результат:

```text
VFS: data/filesystem.zip
Стартовый скрипт: startup.txt

> ls Documents
Команда: ls
Аргументы: ['Documents']

> cd Downloads
Команда: cd
Аргументы: ['Downloads']

> ls $HOME
Команда: ls
Аргументы: ['/Users/macbook']

> hello
Ошибка: неизвестная команда 'hello'
```

Проверена одновременная передача двух параметров. Все три проверочных скрипта выполнились успешно.

### Вывод по этапу 2

В ходе второго этапа реализована передача параметров командной строки и автоматическое выполнение команд из стартового скрипта. Добавлена поддержка комментариев и обработка ошибок чтения файла. Работа программы проверена с помощью трёх Bash-скриптов с различными параметрами запуска.

---

## Этап 3. VFS

**Цель:** Подключить виртуальную файловую систему (VFS) на основе ZIP-архива и реализовать получение информации о ней.

### 1. Работа с VFS в оперативной памяти

Для загрузки виртуальной файловой системы создан отдельный модуль `src/vfs.py`.

Архив считывается в оперативную память с помощью `read_bytes()`. Для работы с его содержимым используются `BytesIO` и `zipfile.ZipFile`.

Файлы и папки сохраняются в словаре `files`. Для папок используется значение `None`, для файлов — их содержимое в виде байтов.

Таким образом, данные VFS обрабатываются в памяти без распаковки и изменения исходного ZIP-архива.

### 2. Загрузка виртуальной файловой системы

Источником VFS является ZIP-архив, путь к которому передаётся через параметр `--vfs`.

В файле `src/vfs.py` реализована функция загрузки:

```python
import hashlib
import zipfile
from io import BytesIO
from pathlib import Path


def load_vfs(path):
    """Загружает ZIP-архив в оперативную память."""
    archive_path = Path(path)
    archive_data = archive_path.read_bytes()

    files = {}

    # Чтение содержимого архива
    with zipfile.ZipFile(BytesIO(archive_data)) as archive:
        for item in archive.infolist():
            if item.is_dir():
                files[item.filename] = None
            else:
                files[item.filename] = archive.read(item)

    return {
        "name": archive_path.name,
        "hash": hashlib.sha256(archive_data).hexdigest(),
        "files": files,
    }
```

Для подключения VFS в `src/emulator.py` добавлены импорты:

```python
from zipfile import BadZipFile
from vfs import load_vfs
```

После получения параметров запуска выполняется загрузка архива:

```python
# Загрузка виртуальной файловой системы
vfs = None

if config.vfs:
    try:
        vfs = load_vfs(config.vfs)
        output.insert(tk.END, f"VFS загружена: {vfs['name']}\n")
        output.insert(
            tk.END,
            f"Количество элементов: {len(vfs['files'])}\n\n"
        )

    except (OSError, BadZipFile) as error:
        output.insert(tk.END, f"Ошибка загрузки VFS: {error}\n\n")
```

При успешной загрузке отображаются название архива и количество элементов. При ошибке открытия файла или неправильном формате ZIP выводится сообщение об ошибке.

Пример результата:

```text
VFS: data/filesystem.zip
Стартовый скрипт: None

VFS загружена: filesystem.zip
Количество элементов: 5
```

### 3. Служебная команда vfs-info

Реализована команда `vfs-info`, которая выводит имя загруженной виртуальной файловой системы и хеш SHA-256 её данных.

Для вычисления хеша используется функция `hashlib.sha256()`.

В функцию `execute_command()` добавлена обработка новой команды:

```python
elif command == "vfs-info":
    if args:
        output.insert(
            tk.END,
            "Ошибка: vfs-info не принимает аргументы\n\n"
        )
    elif vfs is None:
        output.insert(tk.END, "Ошибка: VFS не загружена\n\n")
    else:
        output.insert(tk.END, f"Имя VFS: {vfs['name']}\n")
        output.insert(tk.END, f"SHA-256: {vfs['hash']}\n\n")
```

Результат выполнения команды:

```text
> vfs-info
Имя VFS: filesystem.zip
SHA-256: 7c5ffd34b47ca3df4e303e739c66493b12701b9606fc13221885aaeb33869156
```

Также проверены случаи неправильного использования команды.

Передача лишнего аргумента:

```text
> vfs-info hello
Ошибка: vfs-info не принимает аргументы
```

Выполнение без загруженной VFS:

```text
> vfs-info
Ошибка: VFS не загружена
```

Все проверки выполнены успешно.

### 4. Проверка различных вариантов VFS

Для тестирования подготовлены три ZIP-архива с разной структурой. Их создание выполняется с помощью файла `tests/create_vfs.py`.

**Минимальная VFS — `minimal.zip`**

Архив содержит одну пустую папку:

```text
minimal.zip
└── empty/
```

**VFS с несколькими файлами — `multiple.zip`**

```text
multiple.zip
├── readme.txt
├── notes.txt
├── tasks.txt
└── documents/
    └── report.txt
```

**VFS с тремя уровнями вложенности — `filesystem.zip`**

```text
filesystem.zip
└── home/
    └── student/
        ├── notes.txt
        └── documents/
            └── report.txt
```

Архивы создаются с помощью `zipfile.ZipFile` и метода `writestr()`.

Для проверки каждого варианта в папке `tests` созданы отдельные Bash-скрипты.

**Файл `tests/test_vfs_minimal.sh`:**

```bash
#!/bin/bash

bash run.sh --vfs data/minimal.zip --script startup.txt
```

**Файл `tests/test_vfs_multiple.sh`:**

```bash
#!/bin/bash

bash run.sh --vfs data/multiple.zip --script startup.txt
```

**Файл `tests/test_vfs_nested.sh`:**

```bash
#!/bin/bash

bash run.sh --vfs data/filesystem.zip --script startup.txt
```

Результаты проверок:

| Архив | Количество элементов | Результат |
|---|---:|---|
| `minimal.zip` | 1 | Успешно |
| `multiple.zip` | 5 | Успешно |
| `filesystem.zip` | 5 | Успешно |

Для всех вариантов VFS проверены загрузка архива, подсчёт элементов и работа команды `vfs-info`.

### 5. Проверка команд через стартовый скрипт

Для проверки всех реализованных команд обновлён файл `startup.txt`.

Его содержимое:

```text
# Проверка команд-заглушек
ls
ls Documents
cd
cd Downloads

# Проверка переменных окружения
ls $HOME

# Проверка виртуальной файловой системы
vfs-info
vfs-info hello

# Проверка неизвестной команды
hello
```

Стартовый скрипт выполняет команды последовательно. Комментарии и пустые строки пропускаются.

Результаты проверки:

```text
> ls
Команда: ls
Аргументы: []

> ls Documents
Команда: ls
Аргументы: ['Documents']

> cd
Команда: cd
Аргументы: []

> cd Downloads
Команда: cd
Аргументы: ['Downloads']

> ls $HOME
Команда: ls
Аргументы: ['/Users/macbook']

> vfs-info
Имя VFS: filesystem.zip
SHA-256: 7c5ffd34b47ca3df4e303e739c66493b12701b9606fc13221885aaeb33869156

> vfs-info hello
Ошибка: vfs-info не принимает аргументы

> hello
Ошибка: неизвестная команда 'hello'
```

Для отдельной проверки завершения программы создан файл `tests/startup_exit.txt`:

```text
# Проверка завершения работы эмулятора
exit
```

При выполнении этого скрипта эмулятор автоматически закрывает графическое окно.

Также предусмотрена обработка ошибок загрузки VFS: отсутствующего файла и архива неправильного формата.

### Вывод по этапу 3

В ходе третьего этапа реализована загрузка виртуальной файловой системы из ZIP-архива в оперативную память. Добавлена команда `vfs-info` для вывода имени архива и его SHA-256. Работа эмулятора проверена с тремя вариантами VFS, а также через стартовые скрипты с обработкой ошибок.
