# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Any

class CCConfigType(ABC):
    @abstractmethod
    def to_dict(self) -> dict[str, Any | None]:
        pass

    @property
    @abstractmethod
    def alloc_columns(self) -> list | None:
        pass

    @property
    @abstractmethod
    def alloc_columns_map(self) -> dict | None:
        pass
