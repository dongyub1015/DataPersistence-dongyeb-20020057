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
        if not self._path.exists():
            return {}
        try:
            with self._path.open(encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            bak = self._path.with_suffix(".json.bak")
            shutil.copy2(self._path, bak)
            warnings.warn(
                f"손상된 JSON 파일 {self._path}을 {bak}으로 백업하고 초기화합니다.",
                stacklevel=2,
            )
            return {}

    def _save(self, data: dict[str, dict]) -> None:
        tmp = self._path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self._path)

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
