# PRD: JSON 기반 데이터 영속성 시스템 (CRUD 포함)

## 1. 개요

### 1.1 목적
파일 시스템에 JSON 형식으로 데이터를 저장하고 불러오는 영속성 레이어를 구현한다.
Create / Read / Update / Delete (CRUD) 네 가지 연산을 일관된 인터페이스로 제공하여,
외부 데이터베이스 없이 구조화된 데이터를 관리할 수 있도록 한다.

### 1.2 범위
- Python 기반 단독 실행 모듈
- 단일 JSON 파일을 저장소로 사용
- 레코드 단위(딕셔너리) CRUD 연산 지원
- CLI 또는 다른 모듈에서 임포트하여 사용 가능

---

## 2. 배경 및 문제 정의

| 문제 | 영향 |
|------|------|
| 런타임 메모리만 사용하면 프로세스 종료 시 데이터 소멸 | 재실행 시 데이터 손실 |
| 외부 DB를 쓰면 설치·설정 비용 발생 | 소규모 프로젝트에서 과도한 의존성 |
| 임의 파일 I/O는 일관성·오류 처리가 없음 | 파일 손상, 중복 코드 |

JSON 파일 기반 저장소는 설치 없이 사용 가능하고, 사람이 직접 읽을 수 있으며,
Python 표준 라이브러리만으로 구현할 수 있어 위 문제를 해결한다.

---

## 3. 목표 및 성공 지표

| 목표 | 측정 방법 |
|------|-----------|
| CRUD 4개 연산 모두 동작 | 각 연산 단위 테스트 통과 |
| 잘못된 입력에도 프로그램 비정상 종료 없음 | 예외 처리 커버리지 100% |
| 저장된 데이터가 재실행 후에도 유지 | 프로세스 재시작 후 Read 검증 |
| 코드 의존성: 표준 라이브러리만 사용 | `pip freeze` 결과 비어 있음 |

---

## 4. 사용자 스토리

```
US-01  개발자로서 새 레코드를 추가할 수 있다.
       → 동일 ID 중복 시 오류를 반환한다.

US-02  개발자로서 ID로 특정 레코드를 조회할 수 있다.
       → 존재하지 않는 ID 조회 시 None을 반환한다.

US-03  개발자로서 전체 레코드 목록을 조회할 수 있다.
       → 저장소가 비어 있으면 빈 리스트를 반환한다.

US-04  개발자로서 기존 레코드의 필드를 수정할 수 있다.
       → 존재하지 않는 ID 수정 시 오류를 반환한다.

US-05  개발자로서 레코드를 삭제할 수 있다.
       → 존재하지 않는 ID 삭제 시 오류를 반환한다.

US-06  개발자로서 저장소 파일이 없거나 손상되어도 안전하게 초기화된다.
```

---

## 5. 기능 요구사항

### 5.1 저장소 초기화

| ID | 요구사항 |
|----|----------|
| F-01 | 지정 경로에 JSON 파일이 없으면 빈 저장소(`{}`)로 자동 생성한다. |
| F-02 | JSON 파싱 오류 발생 시 기존 파일을 백업(`.bak`)하고 빈 저장소로 초기화한다. |
| F-03 | 저장소 파일 경로는 인스턴스 생성 시 인자로 지정하며, 기본값은 `data.json`이다. |

### 5.2 Create

| ID | 요구사항 |
|----|----------|
| F-10 | `create(record: dict) -> str` — 레코드를 저장하고 생성된 ID를 반환한다. |
| F-11 | ID는 호출자가 `record["id"]`로 명시할 수 있으며, 미지정 시 UUID v4를 자동 생성한다. |
| F-12 | 동일 ID가 이미 존재하면 `DuplicateKeyError`를 발생시킨다. |
| F-13 | 레코드에 `created_at` 타임스탬프(ISO 8601)를 자동 추가한다. |

### 5.3 Read

| ID | 요구사항 |
|----|----------|
| F-20 | `read(record_id: str) -> dict \| None` — ID로 단일 레코드를 반환한다. |
| F-21 | `read_all() -> list[dict]` — 전체 레코드 리스트를 반환한다. |
| F-22 | 존재하지 않는 ID 조회 시 `None`을 반환한다(예외 미발생). |

### 5.4 Update

| ID | 요구사항 |
|----|----------|
| F-30 | `update(record_id: str, fields: dict) -> dict` — 지정 필드만 덮어쓰고 갱신된 레코드를 반환한다. |
| F-31 | `id` 필드 변경은 허용하지 않는다(무시 처리). |
| F-32 | 존재하지 않는 ID 수정 시 `RecordNotFoundError`를 발생시킨다. |
| F-33 | 레코드에 `updated_at` 타임스탬프를 자동 갱신한다. |

### 5.5 Delete

| ID | 요구사항 |
|----|----------|
| F-40 | `delete(record_id: str) -> bool` — 레코드를 삭제하고 `True`를 반환한다. |
| F-41 | 존재하지 않는 ID 삭제 시 `RecordNotFoundError`를 발생시킨다. |

### 5.6 영속성

| ID | 요구사항 |
|----|----------|
| F-50 | 쓰기 연산(Create / Update / Delete) 완료 시 즉시 파일에 플러시한다. |
| F-51 | 파일 쓰기는 임시 파일 → 원자적 rename 방식으로 수행하여 부분 쓰기를 방지한다. |
| F-52 | JSON 인코딩은 `ensure_ascii=False`, `indent=2`를 사용한다. |

---

## 6. 비기능 요구사항

| 항목 | 기준 |
|------|------|
| 언어 | Python 3.10 이상 |
| 외부 의존성 | 표준 라이브러리만 사용 (`json`, `uuid`, `datetime`, `pathlib`, `shutil`) |
| 동시성 | 단일 프로세스·스레드 환경 지원 (멀티스레드 잠금은 범위 외) |
| 파일 크기 | 레코드 수 10,000개 이하에서 응답 시간 1초 미만 |
| 테스트 | `pytest` 단위 테스트, 커버리지 90% 이상 |

---

## 7. 아키텍처 설계

### 7.1 디렉토리 구조

```
DataPersistence/
├── PRD.md
├── data_store.py          # 핵심 저장소 클래스
├── exceptions.py          # 커스텀 예외 정의
├── models.py              # 데이터 모델 (dataclass)
├── tests/
│   ├── __init__.py
│   ├── test_create.py
│   ├── test_read.py
│   ├── test_update.py
│   └── test_delete.py
└── data.json              # 런타임 생성 (gitignore 권장)
```

### 7.2 클래스 설계

```
JsonDataStore
├── __init__(file_path: str = "data.json")
├── _load() -> dict          # 파일 → 메모리
├── _save(data: dict)        # 메모리 → 파일 (원자적)
│
├── create(record: dict) -> str
├── read(record_id: str) -> dict | None
├── read_all() -> list[dict]
├── update(record_id: str, fields: dict) -> dict
└── delete(record_id: str) -> bool
```

### 7.3 데이터 포맷 (JSON)

```json
{
  "a1b2c3d4-...": {
    "id": "a1b2c3d4-...",
    "name": "홍길동",
    "email": "hong@example.com",
    "created_at": "2026-05-08T10:00:00+09:00",
    "updated_at": "2026-05-08T11:30:00+09:00"
  }
}
```

최상위 키는 레코드 ID, 값은 레코드 딕셔너리.

### 7.4 커스텀 예외 계층

```
JsonDataStoreError (base)
├── DuplicateKeyError    # Create 시 ID 중복
└── RecordNotFoundError  # Update / Delete 시 ID 없음
```

---

## 8. 오류 처리 전략

| 상황 | 처리 방식 |
|------|-----------|
| 파일 없음 | 빈 저장소로 자동 초기화 |
| JSON 파싱 실패 | `.bak` 백업 후 빈 저장소로 초기화, 경고 로그 출력 |
| ID 중복 (Create) | `DuplicateKeyError` 발생 |
| ID 없음 (Update/Delete) | `RecordNotFoundError` 발생 |
| 디스크 쓰기 실패 | `OSError` 전파 (복구 불가 시스템 오류) |

---

## 9. 테스트 계획

### 9.1 단위 테스트 시나리오

| 테스트 ID | 대상 | 시나리오 |
|-----------|------|----------|
| T-01 | create | 정상 레코드 생성 → ID 반환 확인 |
| T-02 | create | 중복 ID → `DuplicateKeyError` |
| T-03 | create | ID 미지정 → UUID 자동 생성 |
| T-04 | read | 존재하는 ID 조회 → 레코드 반환 |
| T-05 | read | 존재하지 않는 ID → `None` 반환 |
| T-06 | read_all | 전체 조회 → 리스트 반환 |
| T-07 | read_all | 빈 저장소 → 빈 리스트 |
| T-08 | update | 필드 수정 → 갱신된 레코드 반환 |
| T-09 | update | 존재하지 않는 ID → `RecordNotFoundError` |
| T-10 | update | `id` 필드 변경 시도 → 무시 확인 |
| T-11 | delete | 정상 삭제 → `True` 반환 |
| T-12 | delete | 존재하지 않는 ID → `RecordNotFoundError` |
| T-13 | 영속성 | 쓰기 후 새 인스턴스로 Read → 데이터 유지 확인 |
| T-14 | 초기화 | 손상된 JSON 파일 → 백업 후 초기화 |

### 9.2 테스트 환경

- `pytest` + `tmp_path` fixture로 임시 파일 사용 (실제 `data.json` 오염 방지)
- 각 테스트는 독립적인 임시 저장소를 생성하여 격리

---

## 10. 구현 단계 (마일스톤)

| 단계 | 작업 항목 | 산출물 |
|------|-----------|--------|
| M1 | 예외 클래스 및 기본 골격 작성 | `exceptions.py`, `data_store.py` 스켈레톤 |
| M2 | `_load` / `_save` 구현 + 파일 초기화 로직 | F-01 ~ F-03, F-50 ~ F-52 충족 |
| M3 | Create / Read 구현 | F-10 ~ F-22 충족, T-01 ~ T-07 통과 |
| M4 | Update / Delete 구현 | F-30 ~ F-41 충족, T-08 ~ T-12 통과 |
| M5 | 영속성 통합 테스트 + 손상 파일 처리 | T-13 ~ T-14 통과 |
| M6 | 코드 정리 및 커버리지 90% 확보 | 최종 검증 |

---

## 11. 제외 범위 (Out of Scope)

- 멀티스레드 / 멀티프로세스 동시 접근 제어
- 네트워크 원격 저장소 연동
- 쿼리·필터링 기능 (전체 조회 후 Python 코드로 필터링)
- 스키마 유효성 검사 (JSON Schema 등)
- 마이그레이션 도구

---

*문서 버전: 1.0 | 작성일: 2026-05-08*
