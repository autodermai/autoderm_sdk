from __future__ import annotations

from typing import Any, Dict, Optional

from httpx import Response


class AutodermException(Exception):
    """Base Exception class, returned when nothing more specific applies"""

    def __init__(self, message: Optional[str] = None) -> None:
        super(AutodermException, self).__init__(message)

        self.message = message

    def __str__(self) -> str:
        msg = self.message or "<empty message>"
        return msg

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={str(self)})"


class AutodermAPIException(AutodermException):
    """Returned when the API responds with an error message"""

    def __init__(
        self,
        message: Optional[str] = None,
        http_status: Optional[int] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.headers = headers or {}

    @classmethod
    def from_response(
        cls, response: Response, message: Optional[str] = None
    ) -> AutodermAPIException:
        return cls(
            message=message or response.text,
            http_status=response.status_code,
            headers=dict(response.headers),
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={str(self)}, http_status={self.http_status})"

class AutodermAPIStatusException(AutodermAPIException):
    """Returned when we receive a non-200 response from the API that we should retry"""

class AutodermConnectionException(AutodermException):
    """Returned when the SDK can not reach the API server for any reason"""