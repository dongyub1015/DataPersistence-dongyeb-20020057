# 설계 문서 05: 테스트 전략

> 관련 PRD 항목: §9  
> Phase: 3, 4, 5

---

## 1. 테스트 환경

| 항목 | 내용 |
|------|------|
| 프레임워크 | `pytest` |
| 파일 격리 | `tmp_path` fixture (pytest 내장) — 각 테스트마다 임시 디렉토리 사용 |
| 커버리지 도구 | `pytest-cov` |
| 목표 커버리지 | 90% 이상 |
| 외부 의존성 | 없음 (`pytest`, `pytest-cov`만 개발 의존성) |

### `pytest.ini` 설정

```ini
[pytest]
testpaths = tests
addopts = --tb=short
```

---

## 2. 공통 Fixture

모든 테스트 파일에서 공유할 픽스처:

```python
# tests/conftest.py 또는 각 파일 내 정의

import pytest
from data_store import JsonDataStore

@pytest.fixture
def store(tmp_path):
    """임시 파일 경로를 사용하는 격리된 저장소 인스턴스."""
    return JsonDataStore(file_path=str(tmp_path / "test_data.json"))

@pytest.fixture
def store_with_record(store):
    """레코드 하나가 미리 저장된 저장소."""
    record_id = store.create({"name": "홍길동", "email": "hong@example.com"})
    return store, record_id
```

---

## 3. 테스트 파일별 시나리오

### 3.1 `tests/test_create.py`

| 테스트 ID | 함수명 | 시나리오 |
|-----------|--------|----------|
| T-01 | `test_create_returns_id` | 정상 레코드 생성 후 반환값이 str이고 레코드에 저장됨 확인 |
| T-02 | `test_create_duplicate_raises` | 동일 ID로 두 번 create → `DuplicateKeyError` 발생 |
| T-03 | `test_create_auto_uuid` | `id` 미지정 시 UUID 형식의 ID가 자동 생성됨 |
| T-bonus | `test_create_adds_created_at` | 생성된 레코드에 `created_at` 필드 존재 확인 |

```python
def test_create_returns_id(store):
    record_id = store.create({"id": "abc", "name": "테스트"})
    assert record_id == "abc"
    assert store.read("abc")["name"] == "테스트"

def test_create_duplicate_raises(store):
    store.create({"id": "abc"})
    with pytest.raises(DuplicateKeyError):
        store.create({"id": "abc"})

def test_create_auto_uuid(store):
    record_id = store.create({"name": "자동ID"})
    import uuid
    uuid.UUID(record_id)   # 유효한 UUID면 예외 없음

def test_create_adds_created_at(store):
    record_id = store.create({"name": "타임스탬프"})
    record = store.read(record_id)
    assert "created_at" in record
```

---

### 3.2 `tests/test_read.py`

| 테스트 ID | 함수명 | 시나리오 |
|-----------|--------|----------|
| T-04 | `test_read_existing` | 존재하는 ID 조회 → 올바른 레코드 반환 |
| T-05 | `test_read_nonexistent_returns_none` | 없는 ID → None 반환, 예외 없음 |
| T-06 | `test_read_all_returns_list` | 여러 레코드 저장 후 read_all → 전체 리스트 반환 |
| T-07 | `test_read_all_empty_store` | 빈 저장소 → 빈 리스트 반환 |

```python
def test_read_existing(store_with_record):
    store, record_id = store_with_record
    record = store.read(record_id)
    assert record is not None
    assert record["id"] == record_id

def test_read_nonexistent_returns_none(store):
    assert store.read("does-not-exist") is None

def test_read_all_returns_list(store):
    store.create({"name": "A"})
    store.create({"name": "B"})
    records = store.read_all()
    assert len(records) == 2

def test_read_all_empty_store(store):
    assert store.read_all() == []
```

---

### 3.3 `tests/test_update.py`

| 테스트 ID | 함수명 | 시나리오 |
|-----------|--------|----------|
| T-08 | `test_update_modifies_field` | 필드 수정 후 갱신된 레코드 반환 |
| T-09 | `test_update_nonexistent_raises` | 없는 ID → `RecordNotFoundError` |
| T-10 | `test_update_ignores_id_change` | `id` 필드 변경 시도 → 원래 ID 유지 |
| T-bonus | `test_update_adds_updated_at` | `updated_at` 필드 자동 추가 확인 |

```python
def test_update_modifies_field(store_with_record):
    store, record_id = store_with_record
    updated = store.update(record_id, {"name": "김철수"})
    assert updated["name"] == "김철수"

def test_update_nonexistent_raises(store):
    with pytest.raises(RecordNotFoundError):
        store.update("ghost-id", {"name": "없음"})

def test_update_ignores_id_change(store_with_record):
    store, record_id = store_with_record
    store.update(record_id, {"id": "new-id", "name": "변경"})
    assert store.read(record_id) is not None     # 원래 ID 유지
    assert store.read("new-id") is None          # 새 ID 생성 안 됨

def test_update_adds_updated_at(store_with_record):
    store, record_id = store_with_record
    updated = store.update(record_id, {"name": "갱신"})
    assert "updated_at" in updated
```

---

### 3.4 `tests/test_delete.py`

| 테스트 ID | 함수명 | 시나리오 |
|-----------|--------|----------|
| T-11 | `test_delete_returns_true` | 정상 삭제 → True 반환, 이후 read는 None |
| T-12 | `test_delete_nonexistent_raises` | 없는 ID → `RecordNotFoundError` |

```python
def test_delete_returns_true(store_with_record):
    store, record_id = store_with_record
    result = store.delete(record_id)
    assert result is True
    assert store.read(record_id) is None

def test_delete_nonexistent_raises(store):
    with pytest.raises(RecordNotFoundError):
        store.delete("ghost-id")
```

---

### 3.5 `tests/test_persistence.py`

| 테스트 ID | 함수명 | 시나리오 |
|-----------|--------|----------|
| T-13 | `test_data_survives_new_instance` | 쓰기 후 새 인스턴스 생성 → 동일 데이터 읽기 |
| T-14 | `test_corrupted_file_recovery` | 손상 JSON 파일 → 경고 발생, 백업 파일 생성, 빈 저장소 초기화 |

```python
def test_data_survives_new_instance(tmp_path):
    path = str(tmp_path / "persist.json")
    store1 = JsonDataStore(file_path=path)
    record_id = store1.create({"name": "영속성"})

    store2 = JsonDataStore(file_path=path)   # 새 인스턴스
    record = store2.read(record_id)
    assert record is not None
    assert record["name"] == "영속성"

def test_corrupted_file_recovery(tmp_path):
    path = tmp_path / "corrupt.json"
    path.write_text("{ invalid json !!!", encoding="utf-8")

    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        store = JsonDataStore(file_path=str(path))
        store.read_all()   # _load() 트리거

    assert len(w) == 1                                  # 경고 1개
    bak = tmp_path / "corrupt.json.bak"
    assert bak.exists()                                  # 백업 파일 생성
    assert store.read_all() == []                        # 빈 저장소 초기화
```

---

## 4. 커버리지 실행 방법

```bash
# 커버리지 측정 + 리포트
pytest --cov=data_store --cov=exceptions --cov-report=term-missing

# HTML 리포트 (선택)
pytest --cov=data_store --cov=exceptions --cov-report=html
```

---

## 5. 테스트 격리 보장

| 수단 | 효과 |
|------|------|
| `tmp_path` fixture | 각 테스트가 독립된 임시 디렉토리 사용 |
| 모든 fixture는 function scope | 테스트 간 상태 공유 없음 |
| `data.json` 직접 사용 안 함 | 실 데이터 오염 없음 |

---

## 6. 테스트 실행 순서 의존성

각 테스트는 독립적으로 실행 가능해야 한다.  
`store_with_record` fixture는 내부에서 `create()`를 직접 호출하므로 외부 상태에 의존하지 않는다.

---

*버전: 1.0 | 작성일: 2026-05-08*
