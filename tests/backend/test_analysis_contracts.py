from __future__ import annotations

from contracts.analysis import (
    AnalysisTransaction,
    CategoryBucket,
    CategoryCorrection,
    CategoryState,
    DuplicateCandidate,
    DuplicateDecision,
    MonthSummary,
    TransactionSupport,
)
from tests.backend.analysis_support import AnalysisStoreTestCase


class AnalysisContractTests(AnalysisStoreTestCase):
    def test_service_returns_typed_deterministic_traceable_contracts(self) -> None:
        self.import_both()
        self.assertIsInstance(self.analysis.list_months(), tuple)
        self.assertEqual(self.analysis.list_months(), ("2026-06", "2026-05"))
        summary = self.analysis.get_month_summary("2026-06")
        self.assertIsInstance(summary, MonthSummary)
        self.assertEqual(summary, self.analysis.get_month_summary("2026-06"))
        self.assertTrue(
            all(isinstance(transaction, AnalysisTransaction) for transaction in summary.transactions)
        )
        self.assertTrue(
            all(isinstance(bucket, CategoryBucket) for bucket in summary.category_breakdown)
        )
        self.assertEqual(
            list(summary.transactions),
            sorted(
                summary.transactions,
                key=lambda transaction: (
                    transaction.transaction_date,
                    transaction.merchant,
                    transaction.amount_minor,
                    transaction.identity_id,
                ),
            ),
        )
        for transaction in summary.transactions:
            self.assertIsInstance(transaction.active_supports, tuple)
            self.assertTrue(transaction.active_supports)
            self.assertTrue(
                all(
                    isinstance(support, TransactionSupport)
                    and support.run_id
                    and support.source_fingerprint
                    and support.source_record_id
                    and support.source_locator
                    for support in transaction.active_supports
                )
            )
            self.assertIn(transaction.inclusion_reason, {"active_support"})
        for bucket in summary.category_breakdown:
            self.assertIsInstance(bucket.contributing_identity_ids, tuple)
            self.assertEqual(
                bucket.contributing_identity_ids,
                tuple(sorted(bucket.contributing_identity_ids)),
            )

        amazon = self.transaction(
            summary,
            merchant="AMAZON.CA *ORDER 702-441",
        )
        category_state = self.analysis.set_category(amazon.identity_id, "Dining")
        self.assertIsInstance(category_state, CategoryState)
        self.assertIsInstance(category_state.history[0], CategoryCorrection)
        self.assertEqual(category_state.category_source, "human")
        self.assertEqual(category_state.effective_category, "Dining")

        candidates = self.analysis.list_duplicate_candidates()
        self.assertIsInstance(candidates, tuple)
        self.assertIsInstance(candidates[0], DuplicateCandidate)
        decided = self.analysis.set_duplicate_decision(
            candidates[0].duplicate_link_id,
            "distinct",
        )
        self.assertIsInstance(decided, DuplicateCandidate)
        self.assertIsInstance(decided.history[0], DuplicateDecision)
        self.assertEqual(decided.effective_decision, "distinct")
        self.assertEqual(
            decided,
            self.analysis.get_duplicate_candidate(decided.duplicate_link_id),
        )

    def test_month_contract_rejects_noncanonical_or_unavailable_keys(self) -> None:
        self.import_csv()
        for invalid in ("2026-6", "2026-00", "2026-13", " 2026-06", "2026-06 "):
            with self.subTest(month=invalid):
                with self.assertRaises(ValueError):
                    self.analysis.get_month_summary(invalid)
        with self.assertRaises(KeyError):
            self.analysis.get_month_summary("2025-01")


if __name__ == "__main__":
    import unittest

    unittest.main()
