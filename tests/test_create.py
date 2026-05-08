import uuid

import pytest

from exceptions import DuplicateKeyError


def test_create_returns_id(store):
    record_id = store.create({"id": "abc", "name": "테스트"})
    assert record_id == "abc"
    assert store.read("abc")["name"] == "테스트"


def test_create_duplicate_raises(store):
    store.create({"id": "abc"})
    with pytest.raises(DuplicateKeyError) as exc_info:
        store.create({"id": "abc"})
    assert exc_info.value.record_id == "abc"


def test_create_auto_uuid(store):
    record_id = store.create({"name": "자동ID"})
    uuid.UUID(record_id)  # 유효한 UUID면 예외 없음
    assert store.read(record_id) is not None


def test_create_adds_created_at(store):
    record_id = store.create({"name": "타임스탬프"})
    assert "created_at" in store.read(record_id)


def test_create_does_not_mutate_input(store):
    original = {"name": "원본"}
    store.create(original)
    assert "id" not in original
    assert "created_at" not in original
