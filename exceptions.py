class JsonDataStoreError(Exception):
    """JSON 데이터 저장소 도메인 예외의 베이스 클래스."""


class DuplicateKeyError(JsonDataStoreError):
    """동일 ID의 레코드가 이미 존재할 때 발생."""

    def __init__(self, record_id: str) -> None:
        super().__init__(f"Record with id '{record_id}' already exists.")
        self.record_id = record_id


class RecordNotFoundError(JsonDataStoreError):
    """지정한 ID의 레코드가 존재하지 않을 때 발생."""

    def __init__(self, record_id: str) -> None:
        super().__init__(f"Record with id '{record_id}' not found.")
        self.record_id = record_id
