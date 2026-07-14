from __future__ import annotations

from backend.analysis import automatic_category
from contracts.analysis import CATEGORY_RULE_VERSION
from tests.backend.analysis_support import (
    EXPECTED_CATEGORY_BY_MERCHANT,
    AnalysisStoreTestCase,
)


class AnalysisCategoryTests(AnalysisStoreTestCase):
    def test_every_fixture_transaction_has_the_exact_mvp_1_category(self) -> None:
        self.import_both()
        transactions = tuple(
            transaction
            for month in self.analysis.list_months()
            for transaction in self.analysis.get_month_summary(month).transactions
        )
        self.assertEqual(len(transactions), 34)
        self.assertEqual(
            {transaction.merchant for transaction in transactions},
            set(EXPECTED_CATEGORY_BY_MERCHANT),
        )
        for transaction in transactions:
            with self.subTest(
                transaction_date=transaction.transaction_date,
                merchant=transaction.merchant,
            ):
                expected = EXPECTED_CATEGORY_BY_MERCHANT[transaction.merchant]
                self.assertEqual(transaction.auto_category, expected)
                self.assertEqual(transaction.effective_category, expected)
                self.assertEqual(transaction.category_source, "auto")
                self.assertEqual(
                    transaction.category_rule_version,
                    CATEGORY_RULE_VERSION,
                )
                self.assertIsNone(transaction.effective_correction_id)
                self.assertEqual(transaction.correction_ids, ())

    def test_refund_and_income_are_visible_credits_but_never_spending(self) -> None:
        self.import_both()
        may = self.analysis.get_month_summary("2026-05")
        june = self.analysis.get_month_summary("2026-06")
        income = self.transaction(
            may,
            merchant="E-TRANSFER RECEIVED J. WU",
            amount_minor=60_000,
        )
        refund = self.transaction(
            june,
            merchant="AMAZON.CA REFUND 702-441",
            amount_minor=12_999,
        )
        self.assertEqual(income.auto_category, "Income")
        self.assertEqual(refund.auto_category, "Refunds & Credits")
        self.assertFalse(income.is_spending)
        self.assertFalse(refund.is_spending)
        self.assertEqual(may.credit_total_minor, 60_000)
        self.assertEqual(june.credit_total_minor, 72_999)
        self.assertNotIn("Income", self.category_map(may))
        self.assertNotIn("Refunds & Credits", self.category_map(june))

    def test_category_matching_is_case_insensitive_and_rule_ordered(self) -> None:
        self.assertEqual(automatic_category("coffee refund", 100), "Refunds & Credits")
        self.assertEqual(automatic_category("coffee refund", -100), "Dining")
        self.assertEqual(automatic_category("LandLord rent", -100), "Housing")
        self.assertEqual(automatic_category("unknown merchant", -100), "Uncategorized")


if __name__ == "__main__":
    import unittest

    unittest.main()
