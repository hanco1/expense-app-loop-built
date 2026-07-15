from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class LocalWebRequest:
    """In-process request shape used by a later loopback-only adapter."""

    method: str
    path: str
    headers: Mapping[str, str] = field(default_factory=dict)
    body: bytes = b""


@dataclass(frozen=True)
class LocalWebResponse:
    """JSON-ready response without any listener or network dependency."""

    status: int
    headers: Mapping[str, str]
    body: bytes

    def json(self) -> dict[str, Any]:
        decoded = json.loads(self.body.decode("utf-8"))
        if not isinstance(decoded, dict):
            raise ValueError("local web response must contain a JSON object")
        return decoded
