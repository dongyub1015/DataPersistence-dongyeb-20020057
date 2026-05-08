# PLAN: JSON 데이터 영속성 시스템 구현 계획

> 기반 문서: [PRD.md](./PRD.md)  
> 상세 설계: [docs/design/](./docs/design/)  
> 작성일: 2026-05-08

---

## 전체 Phase 개요

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5
 기반 골격    저장소 I/O   CRUD 구현    통합 테스트   마무리·검증
 (M1)        (M2)         (M3·M4)      (M5)          (M6)
```

| Phase | 마일스톤 | 핵심 산출물 | PRD 요구사항 |
|-------|---------|------------|-------------|
| 1 | M1 | `exceptions.py`, `data_store.py` 스켈레톤, 프로젝트 구조 | F-01~03 (구조) |
| 2 | M2 | `_load()`, `_save()`, 원자적 쓰기, 파일 초기화 | F-01~03, F-50~52 |
| 3 | M3·M4 | `create`, `read`, `read_all`, `update`, `delete` | F-10~41 |
| 4 | M5 | 영속성 통합 테스트, 손상 파일 복구 검증 | T-13~14 |
| 5 | M6 | 커버리지 90%+, 코드 정리, 문서 최종화 | 전체 |

---

## Phase 1 — 기반 골격 (Foundation)

**목표**: 코드가 실행 가능한 최소 뼈대와 프로젝트 구조를 확립한다.

### 작업 목록

| # | 작업 | 파일 | 완료 기준 |
|---|------|------|-----------|
| 1-1 | 프로젝트 디렉토리 구조 생성 | `tests/__init__.py` 등 | 구조 일치 |
| 1-2 | 커스텀 예외 클래스 작성 | `exceptions.py` | `DuplicateKeyError`, `RecordNotFoundError` import 가능 |
| 1-3 | `JsonDataStore` 클래스 스켈레톤 작성 | `data_store.py` | 모든 public 메서드 정의(본문 `...`), import 오류 없음 |
| 1-4 | `pytest` 설정 파일 작성 | `pytest.ini` | `pytest --collect-only` 실행 성공 |

### 의존 관계
없음 — 첫 번째 단계.

### 상세 설계
- [예외 계층 설계](./docs/design/02_exceptions.md)
- [프로젝트 구조 및 아키텍처](./docs/design/00_overview.md)

---

## Phase 2 — 저장소 I/O 레이어 (Storage Layer)

**목표**: 파일 읽기·쓰기의 안전성과 원자성을 보장하는 내부 메서드를 완성한다.

### 작업 목록

| # | 작업 | 파일 | 완료 기준 |
|---|------|------|-----------|
| 2-1 | `_load()` 구현 — 파일 없을 때 빈 dict 반환 | `data_store.py` | F-01 충족 |
| 2-2 | `_load()` — JSON 파싱 오류 시 `.bak` 백업 + 재초기화 | `data_store.py` | F-02 충족 |
| 2-3 | `_save()` 구현 — 임시 파일 기록 후 원자적 rename | `data_store.py` | F-51 충족 |
| 2-4 | JSON 인코딩 옵션 적용 (`ensure_ascii=False`, `indent=2`) | `data_store.py` | F-52 충족 |
| 2-5 | `__init__` 에서 파일 경로 설정 및 `_load()` 호출 | `data_store.py` | F-03 충족 |

### 의존 관계
Phase 1 완료 후 시작.

### 상세 설계
- [파일 I/O 및 원자적 쓰기 전략](./docs/design/04_error_handling.md)

---

## Phase 3 — CRUD 연산 구현 (CRUD Operations)

**목표**: 4가지 CRUD 연산을 완전히 구현하고 각 단위 테스트를 통과시킨다.

### Phase 3-A: Create / Read

| # | 작업 | 파일 | 완료 기준 |
|---|------|------|-----------|
| 3-1 | `create()` — UUID 자동 생성, `created_at` 추가, 중복 검사 | `data_store.py` | F-10~13 충족 |
| 3-2 | `read()` — ID 조회, 없으면 `None` | `data_store.py` | F-20, F-22 충족 |
| 3-3 | `read_all()` — 전체 리스트 반환 | `data_store.py` | F-21 충족 |
| 3-4 | Create 단위 테스트 작성 | `tests/test_create.py` | T-01, T-02, T-03 통과 |
| 3-5 | Read 단위 테스트 작성 | `tests/test_read.py` | T-04, T-05, T-06, T-07 통과 |

### Phase 3-B: Update / Delete

| # | 작업 | 파일 | 완료 기준 |
|---|------|------|-----------|
| 3-6 | `update()` — 부분 업데이트, `id` 필드 보호, `updated_at` | `data_store.py` | F-30~33 충족 |
| 3-7 | `delete()` — 레코드 제거, `True` 반환 | `data_store.py` | F-40~41 충족 |
| 3-8 | Update 단위 테스트 작성 | `tests/test_update.py` | T-08, T-09, T-10 통과 |
| 3-9 | Delete 단위 테스트 작성 | `tests/test_delete.py` | T-11, T-12 통과 |

### 의존 관계
Phase 2 완료 후 시작. 3-A와 3-B는 순차 진행(3-A 먼저).

### 상세 설계
- [CRUD 연산 상세 설계](./docs/design/03_data_store.md)
- [데이터 모델 설계](./docs/design/01_data_model.md)

---

## Phase 4 — 통합 테스트 (Integration Testing)

**목표**: 프로세스 재시작을 가정한 영속성 검증 및 파일 손상 복구 시나리오를 통과시킨다.

### 작업 목록

| # | 작업 | 파일 | 완료 기준 |
|---|------|------|-----------|
| 4-1 | 영속성 통합 테스트 — 새 인스턴스로 Read 검증 | `tests/test_persistence.py` | T-13 통과 |
| 4-2 | 손상 파일 복구 테스트 — `.bak` 생성 확인 | `tests/test_persistence.py` | T-14 통과 |
| 4-3 | 전체 테스트 스위트 실행 — 회귀 없음 확인 | — | `pytest` 전체 통과 |

### 의존 관계
Phase 3 전체 완료 후 시작.

### 상세 설계
- [테스트 전략](./docs/design/05_testing_strategy.md)

---

## Phase 5 — 마무리 및 검증 (Finalization)

**목표**: 커버리지 90% 이상 달성, 코드 품질 점검, 문서 최종화.

### 작업 목록

| # | 작업 | 완료 기준 |
|---|------|-----------|
| 5-1 | `pytest --cov` 실행 → 미달 라인 추가 테스트 작성 | 커버리지 ≥ 90% |
| 5-2 | 불필요한 주석·임시 코드 제거 | 리뷰 통과 |
| 5-3 | `data.json` `.gitignore` 등록 확인 | 런타임 파일 추적 제외 |
| 5-4 | PRD.md ↔ 구현 요구사항 대조 최종 확인 | F-01~52 전항목 충족 |

### 의존 관계
Phase 4 완료 후 시작.

---

## 파일 생성 순서 (전체)

```
Phase 1
  exceptions.py
  data_store.py          ← 스켈레톤
  pytest.ini
  tests/__init__.py

Phase 2
  data_store.py          ← _load, _save 완성

Phase 3
  data_store.py          ← create, read, read_all, update, delete 완성
  tests/test_create.py
  tests/test_read.py
  tests/test_update.py
  tests/test_delete.py

Phase 4
  tests/test_persistence.py

Phase 5
  .gitignore
  (커버리지 보완 테스트)
```

---

## 리스크 및 대응

| 리스크 | 가능성 | 대응 |
|--------|--------|------|
| Windows 파일 rename 원자성 제한 | 중 | `os.replace()` 사용 (Win32 에서도 원자적 보장) |
| `updated_at` 누락으로 타임스탬프 불일치 | 낮 | Phase 3 테스트에서 필드 존재 여부 명시 검증 |
| 대용량 파일(10k 레코드) 성능 저하 | 낮 | Phase 5에서 간단한 벤치마크 측정 후 필요 시 대응 |

---

*PLAN 버전: 1.0 | 작성일: 2026-05-08*
