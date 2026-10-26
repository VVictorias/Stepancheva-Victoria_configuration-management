
import hashlib
import zipfile
from io import BytesIO
from pathlib import Path

def load_vfs(path):
    """Загружает ZIP-архив в оперативную память."""
    archive_path = Path(path)
    archive_data = archive_path.read_bytes()
    files = {}
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
