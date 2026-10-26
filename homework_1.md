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
