from __future__ import annotations

import unittest
from datetime import date

from tests.backend.statement_support import StatementStoreTestCase


class StatementPdfImportTests(StatementStoreTestCase):
    def test_text_pdf_yields_twelve_field_correct_transactions(self) -> None:
        run_id = self.import_pdf()
        summary = self.store.get_import_run_summary(run_id)
        self.assertEqual(summary["source_type"], "pdf")
        self.assertEqual(
            summary["source_fingerprint"],
            "F4B6B524D7C6140EE3F3E24CE87C4A36F0B40619395B5DC17B03F1B99DBC11F8",
        )
        self.assertEqual(summary["source_record_count"], 12)
        self.assertEqual(summary["parsed_count"], 12)
        self.assertEqual(summary["failed_count"], 0)
        self.assertEqual(summary["occurrence_count"], 12)

        records = self.store.get_import_run_detail(run_id)
        self.assertEqual(
            [record["source_locator"] for record in records],
            [f"pdf-page:1:record:{number}" for number in range(1, 13)],
        )
        transactions = [record["normalized_transaction"] for record in records]
        self.assertTrue(all(transaction is not None for transaction in transactions))
        for transaction in transactions:
            parsed_date = date.fromisoformat(transaction["transaction_date"])
            self.assertEqual((parsed_date.year, parsed_date.month), (2026, 5))
            self.assertTrue(transaction["merchant"].strip())
            self.assertFalse(transaction["merchant"].strip().isnumeric())
            self.assertIs(type(transaction["amount_minor"]), int)
            self.assertEqual(transaction["currency"], "CAD")

        received = [
            transaction
            for transaction in transactions
            if transaction["merchant"] == "E-TRANSFER RECEIVED J. WU"
        ]
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["amount_minor"], 60000)
        self.assertFalse(received[0]["is_spending"])
        debits = [transaction for transaction in transactions if transaction["amount_minor"] < 0]
        self.assertEqual(len(debits), 11)
        self.assertTrue(all(transaction["is_spending"] for transaction in debits))


if __name__ == "__main__":
    unittest.main()
