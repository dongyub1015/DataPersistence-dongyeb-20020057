# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 프로젝트 개요

외부 DB 없이 단일 JSON 파일로 CRUD를 제공하는 Python 라이브러리. 표준 라이브러리(`json`, `uuid`, `datetime`, `pathlib`, `shutil`, `os`)만 사용한다.

핵심 설계 문서: `PRD.md` (요구사항), `PLAN.md` (Phase별 구현 계획), `docs/design/` (상세 설계).

---

## 명령어

```bash
# 전체 테스트
pytest

# 단일 테스트 파일
pytest tests/test_create.py

# 단일 테스트 함수
pytest tests/test_create.py::test_create_returns_id

# 커버리지 측정 (목표 90%+)
pytest --cov=data_store --cov=exceptions --cov-report=term-missing

# HTML 커버리지 리포트
pytest --cov=data_store --cov=exceptions --cov-report=html
```

---

## 아키텍처

```
호출자
  └─► JsonDataStore (data_store.py)  ← 유일한 Public API 진입점
            │
       _load() / _save()             ← 모든 연산이 매번 파일을 읽고 씀 (인메모리 버퍼 없음)
            │
       data.json                     ← 최상위 키가 레코드 ID인 단일 JSON 객체
```

**두 개의 소스 파일만 존재한다**:
- `exceptions.py` — `JsonDataStoreError` → `DuplicateKeyError` / `RecordNotFoundError` 계층
- `data_store.py` — `JsonDataStore` 클래스 전체 (초기화, CRUD, 파일 I/O)

---

## 핵심 불변 규칙

| 규칙 | 위치 |
|------|------|
| 쓰기는 항상 `임시파일 → os.replace()` 원자적 rename | `_save()` |
| 파일 손상 시 `.bak` 백업 후 빈 저장소 복구, 예외 미발생 | `_load()` |
| `update()` 에서 `id` 필드 변경은 무시(silently drop) | `update()` |
| `read()` 는 ID 없을 때 예외 없이 `None` 반환 | `read()` |
| `update()` / `delete()` 는 ID 없을 때 `RecordNotFoundError` | 두 메서드 |
| `created_at` 은 `create()` 가 항상 덮어씀 (호출자 지정값 무시) | `create()` |

---

## 테스트 작성 규칙

모든 테스트는 `tmp_path` fixture로 임시 파일을 사용한다. 실제 `data.json`을 직접 열거나 쓰지 않는다.

```python
# 올바른 fixture 사용 패턴
@pytest.fixture
def store(tmp_path):
    return JsonDataStore(file_path=str(tmp_path / "test_data.json"))
```

공통 fixture는 `tests/conftest.py`에 둔다. `store` (빈 저장소)와 `store_with_record` (레코드 1개 포함) 두 가지 기본 fixture를 제공한다.

---

## 구현 Phase 상태

| Phase | 내용 | 산출 파일 |
|-------|------|-----------|
| 1 | 예외 클래스 + 클래스 스켈레톤 | `exceptions.py`, `data_store.py` |
| 2 | `_load` / `_save` + 원자적 쓰기 | `data_store.py` 완성 |
| 3 | CRUD 4개 연산 + 단위 테스트 | `tests/test_*.py` |
| 4 | 영속성·손상 파일 통합 테스트 | `tests/test_persistence.py` |
| 5 | 커버리지 90%+, 정리 | `.gitignore` 포함 |

현재 어느 Phase까지 완료되었는지는 `tests/` 디렉토리 내 파일 존재 여부로 확인한다.

---

## 런타임 파일 (`data.json`)

`data.json`은 `.gitignore`에 등록해야 한다. `__init__` 시점에는 생성되지 않으며, 첫 번째 `create()` 호출 시 `_save()`가 생성한다. 손상 시 `data.json.bak`으로 백업된다.
