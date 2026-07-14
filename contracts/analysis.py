from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias


CategoryName: TypeAlias = Literal[
    "Housing",
    "Groceries",
    "Dining",
    "Transportation",
    "Shopping",
    "Bills & Utilities",
    "Health & Fitness",
    "Entertainment",
    "Fees",
    "Income",
    "Refunds & Credits",
    "Uncategorized",
]
CategorySource: TypeAlias = Literal["auto", "human"]
DuplicateDecisionValue: TypeAlias = Literal[
    "pending",
    "same_transaction",
    "distinct",
]


CANONICAL_CATEGORIES: tuple[CategoryName, ...] = (
    "Housing",
    "Groceries",
    "Dining",
    "Transportation",
    "Shopping",
    "Bills & Utilities",
    "Health & Fitness",
    "Entertainment",
    "Fees",
    "Income",
    "Refunds & Credits",
    "Uncategorized",
)
CATEGORY_RULE_VERSION = "mvp-1"


@dataclass(frozen=True)
class TransactionSupport:
    occurrence_id: str
    run_id: str
    source_name: str
    source_type: str
    source_fingerprint: str
    source_record_id: str
    source_locator: str


@dataclass(frozen=True)
class CategoryCorrection:
    correction_id: str
    identity_id: str
    category: CategoryName
    created_at: str


@dataclass(frozen=True)
class CategoryState:
    identity_id: str
    auto_category: CategoryName
    effective_category: CategoryName
    category_source: CategorySource
    category_rule_version: str
    effective_correction_id: str | None
    history: tuple[CategoryCorrection, ...]


@dataclass(frozen=True)
class DuplicateDecision:
    decision_id: str
    duplicate_link_id: str
    decision: Literal["same_transaction", "distinct"]
    kept_identity_id: str | None
    created_at: str


@dataclass(frozen=True)
class DuplicateCandidate:
    duplicate_link_id: str
    left_identity_id: str
    right_identity_id: str
    effective_decision: DuplicateDecisionValue
    effective_decision_id: str | None
    kept_identity_id: str | None
    left_included: bool
    right_included: bool
    history: tuple[DuplicateDecision, ...]


@dataclass(frozen=True)
class AnalysisTransaction:
    identity_id: str
    transaction_date: str
    merchant: str
    amount_minor: int
    currency: str
    is_spending: bool
    included: bool
    inclusion_reason: str
    auto_category: CategoryName
    effective_category: CategoryName
    category_source: CategorySource
    category_rule_version: str
    effective_correction_id: str | None
    correction_ids: tuple[str, ...]
    duplicate_decision: DuplicateDecisionValue | Literal["none"]
    duplicate_decision_id: str | None
    duplicate_link_ids: tuple[str, ...]
    active_supports: tuple[TransactionSupport, ...]


@dataclass(frozen=True)
class CategoryBucket:
    category: CategoryName
    spending_minor: int
    transaction_count: int
    contributing_identity_ids: tuple[str, ...]


@dataclass(frozen=True)
class MonthSummary:
    month: str
    currency: str
    spending_total_minor: int
    credit_total_minor: int
    transaction_count: int
    spending_transaction_count: int
    credit_transaction_count: int
    category_breakdown: tuple[CategoryBucket, ...]
    transactions: tuple[AnalysisTransaction, ...]
