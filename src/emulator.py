
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
window.mainloop()
