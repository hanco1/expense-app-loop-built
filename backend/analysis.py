from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, cast

from backend.persistence import CoreStore
from contracts.analysis import (
    CANONICAL_CATEGORIES,
    CATEGORY_RULE_VERSION,
    AnalysisTransaction,
    CategoryBucket,
    CategoryCorrection,
    CategoryName,
    CategoryState,
    DuplicateCandidate,
    DuplicateDecision,
    DuplicateDecisionValue,
    MonthSummary,
    TransactionSupport,
)


MONTH_PATTERN = re.compile(r"[0-9]{4}-(?:0[1-9]|1[0-2])")
CATEGORY_RULES: tuple[tuple[CategoryName, tuple[str, ...]], ...] = (
    ("Housing", ("RENT", "LANDLORD")),
    ("Groceries", ("LOBLAWS", "SOBEYS")),
    ("Dining", ("TIM HORTONS", "COFFEE")),
    ("Transportation", ("PRESTO", "PETRO-CANADA", "UBER")),
    ("Shopping", ("AMAZON", "WALMART", "LCBO")),
    ("Bills & Utilities", ("BELL", "HYDRO")),
    ("Health & Fitness", ("SHOPPERS DRUG MART", "GOODLIFE")),
    ("Entertainment", ("NETFLIX",)),
    ("Fees", ("MONTHLY PLAN FEE",)),
)


@dataclass(frozen=True)
class _DuplicateLinkState:
    duplicate_link_id: str
    left_identity_id: str
    right_identity_id: str
    effective_decision: DuplicateDecisionValue
    effective_decision_id: str | None
    kept_identity_id: str | None
    history: tuple[DuplicateDecision, ...]


def automatic_category(merchant: str, amount_minor: int) -> CategoryName:
    """Apply the ordered, context-free mvp-1 category rules."""

    description = merchant.casefold()
    if amount_minor > 0:
        if "refund" in description:
            return "Refunds & Credits"
        return "Income"
    for category, needles in CATEGORY_RULES:
        if any(needle.casefold() in description for needle in needles):
            return category
    return "Uncategorized"


class AnalysisService:
    """Local typed analysis over immutable imported facts and human decisions."""

    def __init__(self, store: CoreStore) -> None:
        if not isinstance(store, CoreStore):
            raise TypeError("store must be a CoreStore")
        self.store = store

    def list_months(self) -> tuple[str, ...]:
        months = {
            transaction.transaction_date[:7]
            for transaction in self._active_transactions()
            if transaction.included
        }
        return tuple(sorted(months, reverse=True))

    def get_month_summary(self, month: str) -> MonthSummary:
        self._require_month(month)
        transactions = tuple(
            transaction
            for transaction in self._active_transactions()
            if transaction.transaction_date.startswith(f"{month}-")
        )
        included = tuple(
            transaction for transaction in transactions if transaction.included
        )
        if not included:
            raise KeyError(f"analysis month not found: {month}")

        currencies = {transaction.currency for transaction in included}
        if len(currencies) != 1:
            raise ValueError("mixed-currency monthly aggregation is not supported")
        currency = next(iter(currencies))
        spending = tuple(
            transaction for transaction in included if transaction.amount_minor < 0
        )
        credits = tuple(
            transaction for transaction in included if transaction.amount_minor > 0
        )

        buckets: list[CategoryBucket] = []
        for category in CANONICAL_CATEGORIES:
            contributors = tuple(
                transaction
                for transaction in spending
                if transaction.effective_category == category
            )
            if not contributors:
                continue
            identity_ids = tuple(
                sorted(transaction.identity_id for transaction in contributors)
            )
            buckets.append(
                CategoryBucket(
                    category=category,
                    spending_minor=sum(
                        -transaction.amount_minor for transaction in contributors
                    ),
                    transaction_count=len(contributors),
                    contributing_identity_ids=identity_ids,
                )
            )

        spending_total = sum(-transaction.amount_minor for transaction in spending)
        if spending_total != sum(bucket.spending_minor for bucket in buckets):
            raise RuntimeError("category buckets do not reconcile to monthly spending")
        return MonthSummary(
            month=month,
            currency=currency,
            spending_total_minor=spending_total,
            credit_total_minor=sum(transaction.amount_minor for transaction in credits),
            transaction_count=len(included),
            spending_transaction_count=len(spending),
            credit_transaction_count=len(credits),
            category_breakdown=tuple(buckets),
            transactions=transactions,
        )

    def set_category(self, identity_id: str, category: str) -> CategoryState:
        if category not in CANONICAL_CATEGORIES:
            raise ValueError("category must be one of the canonical category values")
        self.store.get_normalized_transaction(identity_id)
        self.store.add_manual_correction(
            identity_id,
            correction_type="category",
            value=category,
        )
        return self.get_category_state(identity_id)

    def get_category_state(self, identity_id: str) -> CategoryState:
        transaction = self.store.get_normalized_transaction(identity_id)
        return self._category_state(
            identity_id,
            str(transaction["merchant"]),
            int(transaction["amount_minor"]),
        )

    def set_duplicate_decision(
        self,
        duplicate_link_id: str,
        decision: str,
        kept_identity_id: str | None = None,
    ) -> DuplicateCandidate:
        if decision not in {"same_transaction", "distinct"}:
            raise ValueError("decision must be 'same_transaction' or 'distinct'")
        link = self.store.get_duplicate_link(duplicate_link_id)
        if decision == "same_transaction":
            if (
                not isinstance(kept_identity_id, str)
                or not kept_identity_id.strip()
            ):
                raise ValueError("kept_identity_id must be a non-empty string")
            left_identity_id = str(link["left_identity_id"])
            right_identity_id = str(link["right_identity_id"])
            if kept_identity_id not in {left_identity_id, right_identity_id}:
                raise ValueError(
                    "kept_identity_id must belong to the duplicate link"
                )
            proposed_states = tuple(
                _DuplicateLinkState(
                    duplicate_link_id=state.duplicate_link_id,
                    left_identity_id=state.left_identity_id,
                    right_identity_id=state.right_identity_id,
                    effective_decision=(
                        "same_transaction"
                        if state.duplicate_link_id == duplicate_link_id
                        else state.effective_decision
                    ),
                    effective_decision_id=(
                        None
                        if state.duplicate_link_id == duplicate_link_id
                        else state.effective_decision_id
                    ),
                    kept_identity_id=(
                        kept_identity_id
                        if state.duplicate_link_id == duplicate_link_id
                        else state.kept_identity_id
                    ),
                    history=state.history,
                )
                for state in self._duplicate_states()
            )
            active_identity_ids = {
                str(transaction["identity_id"])
                for transaction in self.store.list_effective_transactions()
            }
            self._validate_duplicate_component_representative(
                proposed_states,
                left_identity_id,
                right_identity_id,
                active_identity_ids,
            )
        elif kept_identity_id is not None:
            raise ValueError("a distinct decision cannot name a kept identity")
        self.store.add_duplicate_decision(
            duplicate_link_id,
            decision=decision,
            kept_identity_id=kept_identity_id,
        )
        return self.get_duplicate_candidate(duplicate_link_id)

    def get_duplicate_candidate(self, duplicate_link_id: str) -> DuplicateCandidate:
        for candidate in self.list_duplicate_candidates():
            if candidate.duplicate_link_id == duplicate_link_id:
                return candidate
        raise KeyError(f"duplicate link not found: {duplicate_link_id}")

    def list_duplicate_candidates(self) -> tuple[DuplicateCandidate, ...]:
        states = self._duplicate_states()
        active_identity_ids = {
            str(transaction["identity_id"])
            for transaction in self.store.list_effective_transactions()
        }
        excluded_identity_ids = self._duplicate_exclusions(states)
        return tuple(
            DuplicateCandidate(
                duplicate_link_id=state.duplicate_link_id,
                left_identity_id=state.left_identity_id,
                right_identity_id=state.right_identity_id,
                effective_decision=state.effective_decision,
                effective_decision_id=state.effective_decision_id,
                kept_identity_id=state.kept_identity_id,
                left_included=(
                    state.left_identity_id in active_identity_ids
                    and state.left_identity_id not in excluded_identity_ids
                ),
                right_included=(
                    state.right_identity_id in active_identity_ids
                    and state.right_identity_id not in excluded_identity_ids
                ),
                history=state.history,
            )
            for state in states
        )

    def _active_transactions(self) -> tuple[AnalysisTransaction, ...]:
        duplicate_states = self._duplicate_states()
        excluded_identity_ids = self._duplicate_exclusions(duplicate_states)
        states_by_identity: dict[str, list[_DuplicateLinkState]] = {}
        for state in duplicate_states:
            states_by_identity.setdefault(state.left_identity_id, []).append(state)
            states_by_identity.setdefault(state.right_identity_id, []).append(state)

        transactions: list[AnalysisTransaction] = []
        for row in self.store.list_effective_transactions():
            identity_id = str(row["identity_id"])
            category_state = self._category_state(
                identity_id,
                str(row["merchant"]),
                int(row["amount_minor"]),
            )
            linked_states = tuple(
                sorted(
                    states_by_identity.get(identity_id, []),
                    key=lambda state: state.duplicate_link_id,
                )
            )
            duplicate_decision, duplicate_decision_id = self._identity_decision(
                identity_id,
                linked_states,
            )
            included = identity_id not in excluded_identity_ids
            supports = tuple(
                TransactionSupport(
                    occurrence_id=str(support["occurrence_id"]),
                    run_id=str(support["run_id"]),
                    source_name=str(support["source_name"]),
                    source_type=str(support["source_type"]),
                    source_fingerprint=str(support["source_fingerprint"]),
                    source_record_id=str(support["source_record_id"]),
                    source_locator=str(support["source_locator"]),
                )
                for support in row["active_supports"]
            )
            transactions.append(
                AnalysisTransaction(
                    identity_id=identity_id,
                    transaction_date=str(row["transaction_date"]),
                    merchant=str(row["merchant"]),
                    amount_minor=int(row["amount_minor"]),
                    currency=str(row["currency"]),
                    is_spending=bool(row["is_spending"]),
                    included=included,
                    inclusion_reason=(
                        "active_support"
                        if included
                        else "human_duplicate_same_transaction"
                    ),
                    auto_category=category_state.auto_category,
                    effective_category=category_state.effective_category,
                    category_source=category_state.category_source,
                    category_rule_version=category_state.category_rule_version,
                    effective_correction_id=(
                        category_state.effective_correction_id
                    ),
                    correction_ids=tuple(
                        correction.correction_id
                        for correction in category_state.history
                    ),
                    duplicate_decision=duplicate_decision,
                    duplicate_decision_id=duplicate_decision_id,
                    duplicate_link_ids=tuple(
                        state.duplicate_link_id for state in linked_states
                    ),
                    active_supports=supports,
                )
            )
        return tuple(
            sorted(
                transactions,
                key=lambda transaction: (
                    transaction.transaction_date,
                    transaction.merchant,
                    transaction.amount_minor,
                    transaction.identity_id,
                ),
            )
        )

    def _category_state(
        self,
        identity_id: str,
        merchant: str,
        amount_minor: int,
    ) -> CategoryState:
        auto_category = automatic_category(merchant, amount_minor)
        history = tuple(
            CategoryCorrection(
                correction_id=str(row["correction_id"]),
                identity_id=str(row["identity_id"]),
                category=cast(CategoryName, row["value"]),
                created_at=str(row["created_at"]),
            )
            for row in self.store.list_category_corrections(identity_id)
        )
        effective_correction = history[-1] if history else None
        return CategoryState(
            identity_id=identity_id,
            auto_category=auto_category,
            effective_category=(
                effective_correction.category
                if effective_correction is not None
                else auto_category
            ),
            category_source="human" if effective_correction is not None else "auto",
            category_rule_version=CATEGORY_RULE_VERSION,
            effective_correction_id=(
                None
                if effective_correction is None
                else effective_correction.correction_id
            ),
            history=history,
        )

    def _duplicate_states(self) -> tuple[_DuplicateLinkState, ...]:
        states: list[_DuplicateLinkState] = []
        for pair in self.store.list_suspected_duplicate_pairs():
            history = tuple(
                DuplicateDecision(
                    decision_id=str(row["decision_id"]),
                    duplicate_link_id=str(row["duplicate_link_id"]),
                    decision=cast(
                        Literal["same_transaction", "distinct"],
                        row["decision"],
                    ),
                    kept_identity_id=(
                        None
                        if row["kept_identity_id"] is None
                        else str(row["kept_identity_id"])
                    ),
                    created_at=str(row["created_at"]),
                )
                for row in self.store.list_duplicate_decisions(
                    str(pair["duplicate_link_id"])
                )
            )
            effective = history[-1] if history else None
            states.append(
                _DuplicateLinkState(
                    duplicate_link_id=str(pair["duplicate_link_id"]),
                    left_identity_id=str(pair["left_identity_id"]),
                    right_identity_id=str(pair["right_identity_id"]),
                    effective_decision=(
                        "pending" if effective is None else effective.decision
                    ),
                    effective_decision_id=(
                        None if effective is None else effective.decision_id
                    ),
                    kept_identity_id=(
                        None if effective is None else effective.kept_identity_id
                    ),
                    history=history,
                )
            )
        return tuple(states)

    @staticmethod
    def _duplicate_exclusions(
        states: tuple[_DuplicateLinkState, ...],
    ) -> set[str]:
        excluded: set[str] = set()
        for state in states:
            if state.effective_decision != "same_transaction":
                continue
            if state.kept_identity_id == state.left_identity_id:
                excluded.add(state.right_identity_id)
            else:
                excluded.add(state.left_identity_id)
        return excluded

    @staticmethod
    def _validate_duplicate_component_representative(
        states: tuple[_DuplicateLinkState, ...],
        left_identity_id: str,
        right_identity_id: str,
        active_identity_ids: set[str],
    ) -> None:
        adjacency: dict[str, set[str]] = {}
        excluded_identity_ids: set[str] = set()
        for state in states:
            if state.effective_decision != "same_transaction":
                continue
            adjacency.setdefault(state.left_identity_id, set()).add(
                state.right_identity_id
            )
            adjacency.setdefault(state.right_identity_id, set()).add(
                state.left_identity_id
            )
            if state.kept_identity_id == state.left_identity_id:
                excluded_identity_ids.add(state.right_identity_id)
            elif state.kept_identity_id == state.right_identity_id:
                excluded_identity_ids.add(state.left_identity_id)
            else:
                raise RuntimeError("same-transaction decision has no valid keeper")

        component: set[str] = set()
        pending = [left_identity_id, right_identity_id]
        while pending:
            identity_id = pending.pop()
            if identity_id in component:
                continue
            component.add(identity_id)
            pending.extend(adjacency.get(identity_id, ()))

        active_component = component & active_identity_ids
        if component <= excluded_identity_ids or (
            active_component and active_component <= excluded_identity_ids
        ):
            raise ValueError(
                "same_transaction decision would exclude every representative "
                "in its connected component"
            )

    @staticmethod
    def _identity_decision(
        identity_id: str,
        states: tuple[_DuplicateLinkState, ...],
    ) -> tuple[DuplicateDecisionValue | Literal["none"], str | None]:
        if not states:
            return "none", None
        for state in states:
            if (
                state.effective_decision == "same_transaction"
                and state.kept_identity_id != identity_id
            ):
                return "same_transaction", state.effective_decision_id
        for decision in ("same_transaction", "distinct", "pending"):
            for state in states:
                if state.effective_decision == decision:
                    return state.effective_decision, state.effective_decision_id
        raise RuntimeError("duplicate decision state is invalid")

    @staticmethod
    def _require_month(month: str) -> None:
        if not isinstance(month, str) or MONTH_PATTERN.fullmatch(month) is None:
            raise ValueError("month must be a strict YYYY-MM calendar value")
