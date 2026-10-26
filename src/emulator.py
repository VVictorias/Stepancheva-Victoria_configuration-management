
import tkinter as tk
import getpass
import socket
import os
import argparse


# Получение параметров командной строки
parser = argparse.ArgumentParser()
parser.add_argument("--vfs", help="Путь к архиву VFS")
parser.add_argument("--script", help="Путь к стартовому скрипту")
config = parser.parse_args()


username = getpass.getuser()
hostname = socket.gethostname()

window = tk.Tk()
window.title(f"Эмулятор - [{username}@{hostname}]")
window.geometry("600x400")
output = tk.Text(window)
output.pack(fill=tk.BOTH, expand=True)
output.insert(tk.END, f"VFS: {config.vfs}\n")
output.insert(tk.END, f"Стартовый скрипт: {config.script}\n\n")
entry = tk.Entry(window)
entry.pack(fill=tk.X)

def execute_command(event=None, text=None):
    if text is None:
        text = entry.get()
        entry.delete(0, tk.END)
    if not text.strip():
        return
    parts = os.path.expandvars(text).split()
    command = parts[0]
    args = parts[1:]
    output.insert(tk.END, f"> {text}\n")
    if command == "ls":
        output.insert(tk.END, f"Команда: ls\n")
        output.insert(tk.END, f"Аргументы: {args}\n\n")
    elif command == "cd":
        output.insert(tk.END, f"Команда: cd\n")
        output.insert(tk.END, f"Аргументы: {args}\n\n")
    elif command == "exit":
        window.destroy()
    else:
        output.insert(tk.END,f"Ошибка: неизвестная команда '{command}'\n\n")

entry.bind("<Return>", execute_command)

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
        
window.mainloop()
