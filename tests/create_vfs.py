"""Создать три тестовых ZIP-архива для первой домашней работы."""

from pathlib import Path
from zipfile import ZipFile

Path("data").mkdir(exist_ok=True)
with ZipFile("data/filesystem.zip", "w") as archive:
    archive.writestr("home/", "")
    archive.writestr("home/student/", "")
    archive.writestr("home/student/notes.txt", "Hello from VFS!")
    archive.writestr("home/student/documents/", "")
    archive.writestr("home/student/documents/report.txt", "Test report")
print("Создан архив data/filesystem.zip")


with ZipFile("data/minimal.zip", "w") as archive:
    archive.writestr("empty/", "")

print("Создан архив data/minimal.zip")


with ZipFile("data/multiple.zip", "w") as archive:
    archive.writestr("readme.txt", "Information about VFS")
    archive.writestr("notes.txt", "Student notes")
    archive.writestr("tasks.txt", "Task 1\nTask 2")
    archive.writestr("documents/", "")
    archive.writestr("documents/report.txt", "Report content")

print("Создан архив data/multiple.zip")
