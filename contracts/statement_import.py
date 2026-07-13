from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ParsedTransaction:
    transaction_date: str
    merchant: str
    amount_minor: int
    currency: str = "CAD"

    @property
    def is_spending(self) -> bool:
        return self.amount_minor < 0


@dataclass(frozen=True)
class ParsedSourceRecord:
    source_locator: str
    retained_input: str
    parse_status: str
    error_code: str | None
    transaction: ParsedTransaction | None


@runtime_checkable
class StatementParser(Protocol):
    """Text-parser extension point; implementations consume local bytes only."""

    source_type: str
    mode: str

    def parse(self, content: bytes) -> list[ParsedSourceRecord]: ...
