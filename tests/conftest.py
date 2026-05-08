import pytest
from data_store import JsonDataStore


@pytest.fixture
def store(tmp_path):
    return JsonDataStore(file_path=str(tmp_path / "test_data.json"))


@pytest.fixture
def store_with_record(store):
    record_id = store.create({"name": "홍길동", "email": "hong@example.com"})
    return store, record_id
