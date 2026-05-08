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
        data = self._load()
        record = dict(record)
        record_id = record.get("id") or str(uuid.uuid4())
        if record_id in data:
            raise DuplicateKeyError(record_id)
        record["id"] = record_id
        record["created_at"] = _utc_now()
        data[record_id] = record
        self._save(data)
        return record_id

    def read(self, record_id: str) -> dict | None:
        return self._load().get(record_id)

    def read_all(self) -> list[dict]:
        return list(self._load().values())

    def update(self, record_id: str, fields: dict) -> dict:
        data = self._load()
        if record_id not in data:
            raise RecordNotFoundError(record_id)
        safe_fields = {k: v for k, v in fields.items() if k != "id"}
        data[record_id].update(safe_fields)
        data[record_id]["updated_at"] = _utc_now()
        self._save(data)
        return dict(data[record_id])

    def delete(self, record_id: str) -> bool:
        data = self._load()
        if record_id not in data:
            raise RecordNotFoundError(record_id)
        del data[record_id]
        self._save(data)
        return True
