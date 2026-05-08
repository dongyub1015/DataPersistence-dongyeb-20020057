# 설계 문서 00: 프로젝트 구조 및 아키텍처 개요

> 관련 PRD 항목: §1, §6, §7.1  
> Phase: 1

---

## 1. 시스템 목적 요약

외부 데이터베이스 없이 JSON 파일 하나로 데이터를 영속 보관하는 Python 라이브러리.  
`JsonDataStore` 클래스를 임포트하면 CRUD 4개 연산을 즉시 사용할 수 있다.

---

## 2. 최종 디렉토리 구조

```
DataPersistence/
│
├── PRD.md                     # 제품 요구사항
├── PLAN.md                    # 구현 계획
│
├── exceptions.py              # 커스텀 예외 (Phase 1)
├── data_store.py              # 핵심 저장소 클래스 (Phase 1~3)
│
├── tests/
│   ├── __init__.py
│   ├── test_create.py         # T-01~03 (Phase 3-A)
│   ├── test_read.py           # T-04~07 (Phase 3-A)
│   ├── test_update.py         # T-08~10 (Phase 3-B)
│   ├── test_delete.py         # T-11~12 (Phase 3-B)
│   └── test_persistence.py    # T-13~14 (Phase 4)
│
├── docs/
│   └── design/
│       ├── 00_overview.md          ← 이 문서
│       ├── 01_data_model.md
│       ├── 02_exceptions.md
│       ├── 03_data_store.md
│       ├── 04_error_handling.md
│       └── 05_testing_strategy.md
│
├── pytest.ini                 # pytest 설정
├── .gitignore                 # data.json 제외
└── data.json                  # 런타임 생성 (git 추적 제외)
```

---

## 3. 레이어 구조

```
┌─────────────────────────────────────────┐
│            호출자 (CLI / 다른 모듈)        │
└────────────────────┬────────────────────┘
                     │  create / read / update / delete
┌────────────────────▼────────────────────┐
│           JsonDataStore                  │
│  (data_store.py)                         │
│                                          │
│  Public API   →  _load / _save          │
│                       │                  │
│               in-memory dict             │
└────────────────────┬────────────────────┘
                     │  read / write (원자적)
┌────────────────────▼────────────────────┐
│           파일 시스템                     │
│   data.json  /  data.json.tmp            │
│   data.json.bak  (손상 시 백업)           │
└─────────────────────────────────────────┘
```

---

## 4. 모듈별 책임 요약

| 파일 | 책임 |
|------|------|
| `exceptions.py` | 도메인 예외 정의. 비즈니스 오류를 `OSError` 등 시스템 예외와 분리 |
| `data_store.py` | 저장소 생명주기 전체 관리: 초기화, CRUD, 파일 I/O |
| `tests/` | 각 연산의 정상·오류 경로 검증, 영속성 통합 검증 |

`models.py`는 현재 범위에서 제외. 레코드는 순수 `dict`로 처리하며, 필요 시 Phase 5 이후 추가 검토.

---

## 5. 핵심 설계 원칙

| 원칙 | 적용 |
|------|------|
| **표준 라이브러리만** | `json`, `uuid`, `datetime`, `pathlib`, `shutil`, `os` |
| **원자적 쓰기** | 임시 파일 → `os.replace()` — 부분 쓰기로 인한 파일 손상 방지 |
| **fail-safe 초기화** | 파일 손상 시 백업 후 빈 저장소로 복구, 프로그램 중단 없음 |
| **불변 ID** | `update()` 시 `id` 필드 변경 불허 |
| **즉시 플러시** | 쓰기 연산마다 `_save()` 호출 — 인메모리 버퍼 없음 |

---

## 6. 데이터 흐름 요약

### Create
```
호출자 → create(record)
  → UUID 생성 (없을 때)
  → 중복 검사
  → created_at 추가
  → _save()
  → ID 반환
```

### Read
```
호출자 → read(id) / read_all()
  → _load()
  → dict 조회
  → 레코드 또는 None 반환
```

### Update
```
호출자 → update(id, fields)
  → 존재 검사
  → id 필드 제거 (보호)
  → dict.update(fields)
  → updated_at 추가
  → _save()
  → 갱신된 레코드 반환
```

### Delete
```
호출자 → delete(id)
  → 존재 검사
  → dict.pop(id)
  → _save()
  → True 반환
```

---

*버전: 1.0 | 작성일: 2026-05-08*
