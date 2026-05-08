import pytest

from exceptions import RecordNotFoundError


def test_delete_returns_true(store_with_record):
    store, record_id = store_with_record
    result = store.delete(record_id)
    assert result is True


def test_delete_removes_record(store_with_record):
    store, record_id = store_with_record
    store.delete(record_id)
    assert store.read(record_id) is None


def test_delete_nonexistent_raises(store):
    with pytest.raises(RecordNotFoundError) as exc_info:
        store.delete("ghost-id")
    assert exc_info.value.record_id == "ghost-id"


def test_delete_only_removes_target(store):
    id_a = store.create({"name": "A"})
    id_b = store.create({"name": "B"})
    store.delete(id_a)
    assert store.read(id_a) is None
    assert store.read(id_b) is not None   # B는 유지
