
# Домашняя работа №1

**Вариант:** 22

## Этап 1. REPL

**Цель:** Создать минимальный прототип эмулятора командной оболочки с поддержкой диалога с пользователем.

### 1. Графический интерфейс

Для реализации эмулятора выбран язык Python и библиотека Tkinter. Создано графическое окно размером 600 × 400 пикселей с областью вывода и полем ввода команд. Программа запускается через скрипт `run.sh`.

### 2. Заголовок окна

Заголовок формируется автоматически на основе данных операционной системы. Для получения имени пользователя используется `getpass.getuser()`, для имени компьютера — `socket.gethostname()`.

Результат:

```text
Эмулятор - [macbook@MacBook-Pro-macbook-5.local]
```

### 3. Парсер команд

Реализован разбор введённой строки на команду и аргументы. Для раскрытия переменных окружения используется `os.path.expandvars()`, а для разделения строки на части — `split()`.

Пример работы:

```text
> ls $HOME
Команда: ls
Аргументы: ['/Users/macbook']
```

Переменная `$HOME` автоматически заменяется на путь к домашней директории пользователя.

### 4. Команды-заглушки

Реализованы команды `ls` и `cd`. На данном этапе они выводят своё название и аргументы, не выполняя операций с файловой системой.

Проверка команды `ls`:

```text
> ls Documents
Команда: ls
Аргументы: ['Documents']
```

Проверка команды `cd`:

```text
> cd Downloads
Команда: cd
Аргументы: ['Downloads']
```

### 5. Команда exit

Реализована команда `exit`, которая завершает работу эмулятора с помощью метода `window.destroy()`.

При вводе команды `exit` графическое окно закрывается, программа завершает работу.

### 6. Демонстрация работы

Эмулятор запущен в интерактивном режиме. Проверена работа команд `ls`, `cd`, раскрытие переменной окружения `$HOME`, обработка неизвестной команды и завершение работы через `exit`.

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

После ввода `exit` окно эмулятора закрывается.

Все предусмотренные проверки выполнены успешно.

### 7. Сохранение результата в репозитории

Исходный код эмулятора размещён в файле `src/emulator.py`. Для запуска используется скрипт `run.sh`.

Для сохранения выполненного этапа используются команды Git:

```bash
git add homework_1.md src/emulator.py run.sh .gitignore tests/test_emulator.py
git commit -m "feat(emulator): implement stage 1 repl"
git push
```

### Исходный код программы

Файл `src/emulator.py`:

```python
import tkinter as tk
import getpass
import socket
import os

username = getpass.getuser()
hostname = socket.gethostname()

window = tk.Tk()
window.title(f"Эмулятор - [{username}@{hostname}]")
window.geometry("600x400")

output = tk.Text(window)
output.pack(fill=tk.BOTH, expand=True)

entry = tk.Entry(window)
entry.pack(fill=tk.X)


def execute_command(event=None):
    text = entry.get()
    entry.delete(0, tk.END)

    if not text.strip():
        return

    parts = os.path.expandvars(text).split()
    command = parts[0]
    args = parts[1:]

    output.insert(tk.END, f"> {text}\n")

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

### Запуск программы

Для запуска эмулятора используется файл `run.sh`:

```bash
#!/bin/bash
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 src/emulator.py
```

Запуск из терминала:

```bash
bash run.sh
```

После запуска открывается графическое окно эмулятора, в котором можно вводить команды.

### Вывод

В ходе первого этапа разработан графический прототип эмулятора командной оболочки. Реализованы ввод и обработка команд, раскрытие переменных окружения, команды-заглушки `ls` и `cd`, завершение работы через `exit` и вывод сообщений об ошибках. Работа программы проверена в интерактивном режиме.
