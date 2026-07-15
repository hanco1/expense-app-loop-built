from __future__ import annotations

from typing import Any

from tests.backend.local_web_api_support import LocalWebApiTestCase


class LocalWebApiMonthTests(LocalWebApiTestCase):
    def test_fixture_months_use_exact_string_money_and_reconcile(self) -> None:
        self.import_fixture("csv")
        self.import_fixture("pdf")

        self.assertEqual(
            self.data(self.api.dispatch("GET", "/api/months")),
            ["2026-06", "2026-05"],
        )
        expected = {
            "2026-05": {
                "spending": "50340",
                "credits": "60000",
                "count": 12,
                "categories": {
                    "Bills & Utilities": "16774",
                    "Groceries": "16378",
                    "Transportation": "6437",
                    "Shopping": "5423",
                    "Health & Fitness": "1984",
                    "Entertainment": "1799",
                    "Fees": "1095",
                    "Dining": "450",
                },
            },
            "2026-06": {
                "spending": "277617",
                "credits": "72999",
                "count": 22,
                "categories": {
                    "Housing": "185000",
                    "Shopping": "30521",
                    "Groceries": "25727",
                    "Bills & Utilities": "16774",
                    "Transportation": "8047",
                    "Health & Fitness": "6554",
                    "Dining": "2100",
                    "Entertainment": "1799",
                    "Fees": "1095",
                },
            },
        }
        for month, oracle in expected.items():
            summary = self.data(
                self.api.dispatch("GET", f"/api/months/{month}")
            )
            self.assertEqual(summary["spending_total_minor"], oracle["spending"])
            self.assertEqual(summary["credit_total_minor"], oracle["credits"])
            self.assertEqual(summary["transaction_count"], oracle["count"])
            category_map = {
                bucket["category"]: bucket["spending_minor"]
                for bucket in summary["category_breakdown"]
            }
            self.assertEqual(category_map, oracle["categories"])
            self.assertEqual(
                sum(int(value) for value in category_map.values()),
                int(summary["spending_total_minor"]),
            )
            self._assert_minor_units_are_strings(summary)

        june = self.data(self.api.dispatch("GET", "/api/months/2026-06"))
        refund = next(
            row for row in june["transactions"] if "AMAZON.CA REFUND" in row["merchant"]
        )
        income = next(
            row
            for row in june["transactions"]
            if row["merchant"].startswith("E-TRANSFER RECEIVED")
        )
        self.assertEqual(refund["amount_minor"], "12999")
        self.assertEqual(refund["effective_category"], "Refunds & Credits")
        self.assertEqual(income["amount_minor"], "60000")
        self.assertEqual(income["effective_category"], "Income")
        self.assertFalse(refund["is_spending"])
        self.assertFalse(income["is_spending"])

    def _assert_minor_units_are_strings(self, value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key.endswith("_minor"):
                    self.assertIsInstance(item, str, key)
                self._assert_minor_units_are_strings(item)
        elif isinstance(value, list):
            for item in value:
                self._assert_minor_units_are_strings(item)


if __name__ == "__main__":
    import unittest

    unittest.main()
