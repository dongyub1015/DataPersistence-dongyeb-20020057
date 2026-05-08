# 설계 문서 02: 예외 계층 설계

> 관련 PRD 항목: §7.4, §8  
> Phase: 1

---

## 1. 예외 계층 구조

```
Exception
└── JsonDataStoreError          # 모든 도메인 예외의 베이스
    ├── DuplicateKeyError       # Create: 이미 존재하는 ID
    └── RecordNotFoundError     # Update / Delete: 존재하지 않는 ID
```

시스템 예외(`OSError`, `PermissionError` 등)는 별도로 정의하지 않고 그대로 전파한다.

---

## 2. 각 예외 명세

### 2.1 `JsonDataStoreError`

| 항목 | 내용 |
|------|------|
| 상속 | `Exception` |
| 역할 | 라이브러리 전체의 베이스 예외. `except JsonDataStoreError`로 모든 도메인 오류를 한 번에 포착 가능 |
| 직접 발생 여부 | 없음 (서브클래스만 발생) |

### 2.2 `DuplicateKeyError`

| 항목 | 내용 |
|------|------|
| 상속 | `JsonDataStoreError` |
| 발생 시점 | `create()` 호출 시 동일 `id`가 이미 저장소에 존재할 때 |
| 메시지 형식 | `"Record with id '{id}' already exists."` |
| PRD 참조 | F-12 |

### 2.3 `RecordNotFoundError`

| 항목 | 내용 |
|------|------|
| 상속 | `JsonDataStoreError` |
| 발생 시점 | `update()` 또는 `delete()` 호출 시 지정 `id`가 저장소에 없을 때 |
| 메시지 형식 | `"Record with id '{id}' not found."` |
| PRD 참조 | F-32, F-41 |

---

## 3. 구현 코드 (`exceptions.py`)

```python
class JsonDataStoreError(Exception):
    """JSON 데이터 저장소 도메인 예외의 베이스 클래스."""


class DuplicateKeyError(JsonDataStoreError):
    """동일 ID의 레코드가 이미 존재할 때 발생."""

    def __init__(self, record_id: str) -> None:
        super().__init__(f"Record with id '{record_id}' already exists.")
        self.record_id = record_id


class RecordNotFoundError(JsonDataStoreError):
    """지정한 ID의 레코드가 존재하지 않을 때 발생."""

    def __init__(self, record_id: str) -> None:
        super().__init__(f"Record with id '{record_id}' not found.")
        self.record_id = record_id
```

---

## 4. 예외 처리 흐름

### Create 시

```
create(record)
  ├─ id 이미 존재  →  raise DuplicateKeyError(id)
  └─ 정상          →  저장 후 id 반환
```

### Update 시

```
update(id, fields)
  ├─ id 없음  →  raise RecordNotFoundError(id)
  └─ 정상     →  업데이트 후 레코드 반환
```

### Delete 시

```
delete(id)
  ├─ id 없음  →  raise RecordNotFoundError(id)
  └─ 정상     →  삭제 후 True 반환
```

### Read 시 (예외 없음)

```
read(id)
  ├─ id 없음  →  None 반환  (예외 미발생, PRD F-22)
  └─ 정상     →  dict 반환
```

---

## 5. 호출자 사용 예시

```python
from exceptions import DuplicateKeyError, RecordNotFoundError, JsonDataStoreError

# 특정 예외만 처리
try:
    store.create({"id": "abc", "name": "홍길동"})
except DuplicateKeyError as e:
    print(f"중복 ID: {e.record_id}")

# 모든 도메인 예외 포착
try:
    store.delete("not-exist")
except JsonDataStoreError as e:
    print(f"저장소 오류: {e}")

# 시스템 예외는 별도 처리
try:
    store.create({"name": "테스트"})
except OSError as e:
    print(f"파일 시스템 오류: {e}")
```

---

*버전: 1.0 | 작성일: 2026-05-08*
