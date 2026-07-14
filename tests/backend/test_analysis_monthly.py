from __future__ import annotations

from contracts.analysis import CANONICAL_CATEGORIES
from tests.backend.analysis_support import (
    EXPECTED_MONTHLY_CATEGORIES,
    AnalysisStoreTestCase,
)


class AnalysisMonthlyTests(AnalysisStoreTestCase):
    def test_fixture_months_match_exact_totals_and_category_oracles(self) -> None:
        self.import_both()
        self.assertEqual(self.analysis.list_months(), ("2026-06", "2026-05"))
        expected = {
            "2026-05": (12, 11, 1, 50_340, 60_000),
            "2026-06": (22, 20, 2, 277_617, 72_999),
        }
        for month, expected_totals in expected.items():
            with self.subTest(month=month):
                summary = self.analysis.get_month_summary(month)
                self.assertEqual(summary.currency, "CAD")
                self.assertEqual(
                    (
                        summary.transaction_count,
                        summary.spending_transaction_count,
                        summary.credit_transaction_count,
                        summary.spending_total_minor,
                        summary.credit_total_minor,
                    ),
                    expected_totals,
                )
                self.assertEqual(
                    self.category_map(summary),
                    EXPECTED_MONTHLY_CATEGORIES[month],
                )
                self.assertEqual(
                    sum(
                        bucket.spending_minor
                        for bucket in summary.category_breakdown
                    ),
                    summary.spending_total_minor,
                )
                self.assertEqual(
                    sum(
                        bucket.transaction_count
                        for bucket in summary.category_breakdown
                    ),
                    summary.spending_transaction_count,
                )
                order = {category: index for index, category in enumerate(CANONICAL_CATEGORIES)}
                self.assertEqual(
                    [bucket.category for bucket in summary.category_breakdown],
                    sorted(
                        (bucket.category for bucket in summary.category_breakdown),
                        key=order.__getitem__,
                    ),
                )

                spending_identity_ids = {
                    transaction.identity_id
                    for transaction in summary.transactions
                    if transaction.included and transaction.amount_minor < 0
                }
                contributing_identity_ids = [
                    identity_id
                    for bucket in summary.category_breakdown
                    for identity_id in bucket.contributing_identity_ids
                ]
                self.assertEqual(
                    set(contributing_identity_ids),
                    spending_identity_ids,
                )
                self.assertEqual(
                    len(contributing_identity_ids),
                    len(set(contributing_identity_ids)),
                )
                self.assertEqual(
                    len([transaction for transaction in summary.transactions if transaction.included]),
                    summary.transaction_count,
                )


if __name__ == "__main__":
    import unittest

    unittest.main()
