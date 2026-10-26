import os
from pathlib import Path
from uuid import uuid4


class LocalPhotoStorage:
    """Local filesystem storage; replace this adapter for persistent hosted storage."""

    def __init__(self, directory: str | Path | None = None):
        default_directory = Path(__file__).resolve().parents[1] / "uploads"
        self.directory = Path(directory or os.getenv("PLANT_UPLOAD_DIR", default_directory)).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, extension: str) -> str:
        storage_key = f"{uuid4().hex}.{extension}"
        self.path_for(storage_key).write_bytes(content)
        return storage_key

    def path_for(self, storage_key: str) -> Path:
        if Path(storage_key).name != storage_key:
            raise ValueError("Invalid photo storage key")
        path = (self.directory / storage_key).resolve()
        if path.parent != self.directory:
            raise ValueError("Invalid photo storage key")
        return path

    def delete(self, storage_key: str) -> None:
        self.path_for(storage_key).unlink(missing_ok=True)


def get_photo_storage() -> LocalPhotoStorage:
    return LocalPhotoStorage()
