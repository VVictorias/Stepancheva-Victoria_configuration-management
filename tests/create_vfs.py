
from pathlib import Path
from zipfile import ZipFile
# Создание папки для архивов
Path("data").mkdir(exist_ok=True)
# Создание ZIP-архива с файлами и папками
with ZipFile("data/filesystem.zip", "w") as archive:
    archive.writestr("home/", "")
    archive.writestr("home/student/", "")
    archive.writestr("home/student/notes.txt", "Hello from VFS!")
    archive.writestr("home/student/documents/", "")
    archive.writestr(
        "home/student/documents/report.txt",
        "Test report"
    )
print("Создан архив data/filesystem.zip")


# Создание минимальной VFS
with ZipFile("data/minimal.zip", "w") as archive:
    archive.writestr("empty/", "")

print("Создан архив data/minimal.zip")


# Создание VFS с несколькими файлами
with ZipFile("data/multiple.zip", "w") as archive:
    archive.writestr("readme.txt", "Information about VFS")
    archive.writestr("notes.txt", "Student notes")
    archive.writestr("tasks.txt", "Task 1\nTask 2")
    archive.writestr("documents/", "")
    archive.writestr("documents/report.txt", "Report content")

print("Создан архив data/multiple.zip")

