from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WebApiError(RuntimeError):
    status_code: int
    message: str

    def __str__(self) -> str:
        return self.message
