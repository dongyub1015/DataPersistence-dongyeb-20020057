import warnings
from pathlib import Path

from data_store import JsonDataStore


# T-13: 프로세스 재시작을 가정한 영속성 검증
def test_data_survives_new_instance(tmp_path):
    path = str(tmp_path / "persist.json")
    store1 = JsonDataStore(file_path=path)
    record_id = store1.create({"name": "영속성"})

    store2 = JsonDataStore(file_path=path)
    record = store2.read(record_id)
    assert record is not None
    assert record["name"] == "영속성"
    assert record["id"] == record_id


def test_update_survives_new_instance(tmp_path):
    path = str(tmp_path / "persist.json")
    store1 = JsonDataStore(file_path=path)
    record_id = store1.create({"name": "초기값"})
    store1.update(record_id, {"name": "변경값"})

    store2 = JsonDataStore(file_path=path)
    assert store2.read(record_id)["name"] == "변경값"


def test_delete_survives_new_instance(tmp_path):
    path = str(tmp_path / "persist.json")
    store1 = JsonDataStore(file_path=path)
    record_id = store1.create({"name": "삭제대상"})
    store1.delete(record_id)

    store2 = JsonDataStore(file_path=path)
    assert store2.read(record_id) is None
    assert store2.read_all() == []


def test_multiple_records_survive_new_instance(tmp_path):
    path = str(tmp_path / "persist.json")
    store1 = JsonDataStore(file_path=path)
    ids = [store1.create({"index": i}) for i in range(5)]

    store2 = JsonDataStore(file_path=path)
    assert len(store2.read_all()) == 5
    for record_id in ids:
        assert store2.read(record_id) is not None


# T-14: 손상된 JSON 파일 복구 검증
def test_corrupted_file_recovery(tmp_path):
    path = tmp_path / "corrupt.json"
    path.write_text("{ invalid json !!!", encoding="utf-8")

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        store = JsonDataStore(file_path=str(path))
        result = store.read_all()

    assert result == []
    assert len(w) == 1
    assert "백업" in str(w[0].message)


def test_corrupted_file_creates_bak(tmp_path):
    path = tmp_path / "corrupt.json"
    path.write_text("{ broken", encoding="utf-8")

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        store = JsonDataStore(file_path=str(path))
        store.read_all()

    bak = tmp_path / "corrupt.json.bak"
    assert bak.exists()
    assert bak.read_text(encoding="utf-8") == "{ broken"


def test_corrupted_file_allows_new_writes(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("not json", encoding="utf-8")

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        store = JsonDataStore(file_path=str(path))
        record_id = store.create({"name": "복구후생성"})

    assert store.read(record_id)["name"] == "복구후생성"
