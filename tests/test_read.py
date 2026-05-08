def test_read_existing(store_with_record):
    store, record_id = store_with_record
    record = store.read(record_id)
    assert record is not None
    assert record["id"] == record_id
    assert record["name"] == "홍길동"


def test_read_nonexistent_returns_none(store):
    assert store.read("does-not-exist") is None


def test_read_all_returns_list(store):
    store.create({"name": "A"})
    store.create({"name": "B"})
    records = store.read_all()
    assert len(records) == 2


def test_read_all_empty_store(store):
    assert store.read_all() == []


def test_read_all_contains_all_fields(store):
    store.create({"id": "x1", "name": "철수", "age": 20})
    records = store.read_all()
    assert records[0]["name"] == "철수"
    assert records[0]["age"] == 20
