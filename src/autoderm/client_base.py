import logging
import os
from abc import ABC
from typing import Optional

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=os.getenv("LOG_LEVEL", "ERROR"),
)


class ClientBase(ABC):
    def __init__(
        self,
        endpoint: str,
        api_key: Optional[str] = None,
        max_retries: int = 5,
        timeout: int = 120,
    ):
        self._max_retries = max_retries
        self._timeout = timeout

        self._endpoint = endpoint
        self._api_key = api_key
        self._logger = logging.getLogger(__name__)

        # This should be automatically updated by the deploy script
        self._version = "0.0.1"


   