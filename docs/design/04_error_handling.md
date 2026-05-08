# 설계 문서 04: 오류 처리 및 파일 안전성 전략

> 관련 PRD 항목: §8, §5.6  
> Phase: 2

---

## 1. 오류 분류

| 분류 | 예시 | 처리 방침 |
|------|------|-----------|
| **도메인 오류** | ID 중복, ID 없음 | 커스텀 예외 발생 후 호출자에게 위임 |
| **파일 복구 가능 오류** | JSON 파싱 실패 | 백업 후 빈 저장소 초기화, 경고 출력 |
| **시스템 오류** | 디스크 풀, 권한 없음 | `OSError` 그대로 전파 |

---

## 2. 파일 초기화 시나리오

### 2.1 파일 없음 (정상 첫 실행)

```
_load() 호출
  │
  ├─ self._path.exists() == False
  │
  └─ return {}          ← 빈 dict 반환, 파일 생성은 첫 _save() 시점
```

첫 번째 쓰기 연산(`create`)이 발생할 때 `_save()`가 파일을 생성한다.  
`__init__` 시점에는 파일을 생성하지 않는다 (불필요한 빈 파일 방지).

### 2.2 JSON 파싱 실패 (손상 파일)

```
_load() 호출
  │
  ├─ 파일 존재
  ├─ json.load() → JSONDecodeError
  │
  ├─ shutil.copy2(original, original.bak)   ← 기존 파일 보존
  ├─ warnings.warn(...)                      ← 경고 출력
  └─ return {}                               ← 빈 dict, 프로그램 계속 실행
```

백업 파일명: `data.json` → `data.json.bak`  
`.bak` 파일이 이미 존재해도 `copy2()`로 덮어씀 (최신 손상본 보존).

---

## 3. 원자적 파일 쓰기

### 3.1 문제 상황

```
# 원자적 쓰기 없이 직접 쓸 경우:
with open("data.json", "w") as f:
    json.dump(data, f)   ← 프로세스가 여기서 죽으면 파일이 반만 쓰인 채로 남음
```

반만 쓰인 JSON 파일은 파싱 불가 → 다음 실행 시 데이터 전체 손실.

### 3.2 해결책: 임시 파일 + `os.replace()`

```
1. data.json.tmp 에 전체 내용 기록 완료
2. os.replace("data.json.tmp", "data.json")
   └─ POSIX: rename(2) 시스템 콜 → 원자적
   └─ Windows: MoveFileEx(MOVEFILE_REPLACE_EXISTING) → 원자적
```

`os.replace()`는 Python 3.3+에서 플랫폼 무관하게 원자적 rename을 보장한다.

### 3.3 임시 파일 위치

임시 파일은 반드시 최종 파일과 **동일 파티션·볼륨**에 위치해야 한다.  
(다른 파티션이면 rename 대신 copy+delete가 일어나 원자성 깨짐)

```python
tmp = self._path.with_suffix(".json.tmp")
# data.json → data.json.tmp (동일 디렉토리, 동일 파티션 보장)
```

### 3.4 `_save()` 전체 흐름

```
_save(data)
  │
  ├─ tmp = path.with_suffix(".json.tmp")
  ├─ open(tmp, "w", encoding="utf-8")
  ├─ json.dump(data, f, ensure_ascii=False, indent=2)
  ├─ f.close()                         ← 버퍼 플러시 보장
  │
  └─ os.replace(tmp, path)             ← 원자적 교체
       ├─ 성공: data.json 갱신 완료
       └─ 실패: OSError 전파 (tmp 파일은 남아있어 디버깅 가능)
```

---

## 4. 각 CRUD 연산의 오류 경로

### 4.1 Create

| 상황 | 오류 | 처리 |
|------|------|------|
| 동일 ID 존재 | `DuplicateKeyError` | 발생 |
| 디스크 풀 (`_save` 실패) | `OSError` | 전파 |

### 4.2 Read / read_all

| 상황 | 처리 |
|------|------|
| ID 없음 | `None` 반환 (예외 없음) |
| 파일 없음 | 빈 리스트 / None 반환 |
| 파일 손상 | `_load()` 내부에서 복구 후 빈 결과 반환 |

### 4.3 Update

| 상황 | 오류 | 처리 |
|------|------|------|
| ID 없음 | `RecordNotFoundError` | 발생 |
| 디스크 풀 | `OSError` | 전파 |

### 4.4 Delete

| 상황 | 오류 | 처리 |
|------|------|------|
| ID 없음 | `RecordNotFoundError` | 발생 |
| 디스크 풀 | `OSError` | 전파 |

---

## 5. 로깅 전략

`warnings.warn()`을 사용하여 복구 이벤트를 알린다.  
이유: `logging` 설정 없이도 기본 출력되며, 호출자가 `warnings.filterwarnings()`로 제어 가능.

```python
import warnings

warnings.warn(
    f"손상된 JSON 파일 {self._path}을 {bak}으로 백업하고 초기화합니다.",
    stacklevel=2,
)
```

`stacklevel=2`는 경고 위치를 `_load()` 내부가 아닌 호출자 코드로 표시한다.

---

## 6. 정리: 오류 처리 결정 기준

```
오류 복구 가능?
  YES (파일 손상)  →  백업 + 초기화, warnings.warn, 실행 계속
  NO (도메인 오류) →  커스텀 예외 발생, 호출자가 처리
  NO (시스템 오류) →  OSError 그대로 전파, 라이브러리가 숨기지 않음
```

---

*버전: 1.0 | 작성일: 2026-05-08*
