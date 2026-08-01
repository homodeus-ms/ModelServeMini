from typing import Any


class AppException(Exception):
    def __init__(self, status_code: int, detail: str, **data: Any):
        self.status_code = status_code
        self.detail = detail
        self.data = data

        super().__init__(detail)