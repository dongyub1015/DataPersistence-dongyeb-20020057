import datetime
import json
import os
import shutil
import uuid
import warnings
from pathlib import Path

from exceptions import DuplicateKeyError, RecordNotFoundError


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class JsonDataStore:
    def __init__(self, file_path: str = "data.json") -> None:
        self._path = Path(file_path)

    def _load(self) -> dict[str, dict]:
        ...

    def _save(self, data: dict[str, dict]) -> None:
        ...

    def create(self, record: dict) -> str:
        ...

    def read(self, record_id: str) -> dict | None:
        ...

    def read_all(self) -> list[dict]:
        ...

    def update(self, record_id: str, fields: dict) -> dict:
        ...

    def delete(self, record_id: str) -> bool:
        ...
