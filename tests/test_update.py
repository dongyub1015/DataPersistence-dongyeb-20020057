import pytest

from exceptions import RecordNotFoundError


def test_update_modifies_field(store_with_record):
    store, record_id = store_with_record
    updated = store.update(record_id, {"name": "김철수"})
    assert updated["name"] == "김철수"
    assert store.read(record_id)["name"] == "김철수"


def test_update_nonexistent_raises(store):
    with pytest.raises(RecordNotFoundError) as exc_info:
        store.update("ghost-id", {"name": "없음"})
    assert exc_info.value.record_id == "ghost-id"


def test_update_ignores_id_change(store_with_record):
    store, record_id = store_with_record
    store.update(record_id, {"id": "new-id", "name": "변경"})
    assert store.read(record_id) is not None   # 원래 ID 유지
    assert store.read("new-id") is None        # 새 ID 생성 안 됨


def test_update_adds_updated_at(store_with_record):
    store, record_id = store_with_record
    updated = store.update(record_id, {"name": "갱신"})
    assert "updated_at" in updated


def test_update_preserves_other_fields(store_with_record):
    store, record_id = store_with_record
    store.update(record_id, {"age": 30})
    record = store.read(record_id)
    assert record["name"] == "홍길동"   # 기존 필드 유지
    assert record["age"] == 30
