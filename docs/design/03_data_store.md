# 설계 문서 03: JsonDataStore 클래스 상세 설계

> 관련 PRD 항목: §5, §7.2  
> Phase: 2, 3

---

## 1. 클래스 시그니처 전체

```python
class JsonDataStore:
    def __init__(self, file_path: str = "data.json") -> None: ...

    # 내부 메서드
    def _load(self) -> dict[str, dict]: ...
    def _save(self, data: dict[str, dict]) -> None: ...

    # Public API
    def create(self, record: dict) -> str: ...
    def read(self, record_id: str) -> dict | None: ...
    def read_all(self) -> list[dict]: ...
    def update(self, record_id: str, fields: dict) -> dict: ...
    def delete(self, record_id: str) -> bool: ...
```

---

## 2. `__init__`

```
인자: file_path (str) — 저장소 파일 경로. 기본값 "data.json"
반환: 없음
```

**동작**

1. `self._path = Path(file_path)` 로 경로 저장.
2. 추가 초기화 불필요 — `_load()`는 각 연산 시점에 호출.

> Phase 2에서 `_load()`를 `__init__`에서 미리 호출하는 대신, 각 연산마다 호출하는 방식을 채택. 이유: 파일이 외부에서 수정되어도 항상 최신 상태를 읽는다.

---

## 3. `_load()` — 내부 메서드

```
반환: dict[str, dict]  (저장소 전체 데이터)
예외: 없음 (파싱 오류는 내부 처리)
```

**동작 순서**

```
파일 존재?
  NO  →  return {}

파일 읽기 → JSON 파싱 성공?
  YES →  return 파싱된 dict
  NO  →  기존 파일을 .bak으로 복사
          경고 메시지 출력 (warnings.warn)
          return {}
```

**구현 스케치**

```python
def _load(self) -> dict:
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
```

---

## 4. `_save()` — 내부 메서드

```
인자: data (dict) — 저장할 전체 저장소 데이터
반환: 없음
예외: OSError (디스크 오류 시 전파)
```

**원자적 쓰기 전략**

```
1. 동일 디렉토리에 임시 파일 생성 (data.json.tmp)
2. JSON 직렬화 후 임시 파일에 쓰기
3. os.replace(tmp, target)  ← 원자적 rename
   (실패 시 임시 파일만 손상, 원본 보존)
```

`os.replace()`는 Windows에서도 원자적 rename을 지원한다.

**구현 스케치**

```python
def _save(self, data: dict) -> None:
    tmp = self._path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, self._path)
```

---

## 5. `create(record)` — Public API

```
인자: record (dict) — 저장할 레코드. "id" 키 선택적
반환: str — 생성된 레코드 ID
예외: DuplicateKeyError — 동일 ID 존재 시
```

**동작 순서**

```
1. data = _load()
2. id = record.get("id") or str(uuid.uuid4())
3. id in data?  →  raise DuplicateKeyError(id)
4. record["id"] = id
5. record["created_at"] = utc_now_iso()
6. data[id] = record
7. _save(data)
8. return id
```

**주의**
- `record` 원본 dict를 직접 수정하지 않도록 `record = dict(record)` 복사 후 처리.
- `created_at`은 덮어쓰지 않음 — 호출자가 이미 지정한 경우에도 자동 설정값이 우선.  
  (타임스탬프 신뢰성 보장. 필요 시 향후 옵션화 검토)

---

## 6. `read(record_id)` — Public API

```
인자: record_id (str)
반환: dict | None — 레코드 또는 None (예외 없음)
```

**동작 순서**

```
1. data = _load()
2. return data.get(record_id)
```

반환된 dict는 내부 저장소의 참조가 아닌 값이므로 호출자가 수정해도 안전.  
(`_load()`가 매번 새 dict를 파싱하므로 자동 보장)

---

## 7. `read_all()` — Public API

```
반환: list[dict] — 전체 레코드 리스트 (순서 미보장)
```

**동작 순서**

```
1. data = _load()
2. return list(data.values())
```

빈 저장소일 때 `[]` 반환.

---

## 8. `update(record_id, fields)` — Public API

```
인자: record_id (str), fields (dict) — 덮어쓸 필드들
반환: dict — 갱신된 레코드 전체
예외: RecordNotFoundError — ID 없을 때
```

**동작 순서**

```
1. data = _load()
2. record_id not in data?  →  raise RecordNotFoundError(record_id)
3. fields = {k: v for k, v in fields.items() if k != "id"}  ← id 보호
4. data[record_id].update(fields)
5. data[record_id]["updated_at"] = utc_now_iso()
6. _save(data)
7. return dict(data[record_id])  ← 복사본 반환
```

---

## 9. `delete(record_id)` — Public API

```
인자: record_id (str)
반환: bool — 항상 True (성공 시)
예외: RecordNotFoundError — ID 없을 때
```

**동작 순서**

```
1. data = _load()
2. record_id not in data?  →  raise RecordNotFoundError(record_id)
3. del data[record_id]
4. _save(data)
5. return True
```

---

## 10. 타임스탬프 헬퍼

공통 유틸리티로 모듈 내부에 아래 함수를 정의한다:

```python
def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
```

외부로 노출하지 않으므로 이름 앞에 `_` 접두사.

---

## 11. 임포트 목록

```python
import datetime
import json
import os
import shutil
import uuid
import warnings
from pathlib import Path

from exceptions import DuplicateKeyError, RecordNotFoundError
```

표준 라이브러리만 사용 (PRD §6 충족).

---

*버전: 1.0 | 작성일: 2026-05-08*
