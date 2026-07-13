from __future__ import annotations

import unittest
from datetime import date

from tests.backend.statement_support import StatementStoreTestCase


class StatementCsvImportTests(StatementStoreTestCase):
    def test_csv_preserves_all_rows_and_normalizes_field_correct_transactions(self) -> None:
        run_id = self.import_csv()
        summary = self.store.get_import_run_summary(run_id)
        self.assertEqual(summary["source_name"], "td-mock-2026-06.csv")
        self.assertEqual(summary["source_type"], "csv")
        self.assertEqual(
            summary["source_fingerprint"],
            "9F93F107DDD02AEE2FB0A0AE19EB962180C680D1FB06D4D90959C96ED8CD7BAA",
        )
        self.assertEqual(summary["source_record_count"], 23)
        self.assertEqual(summary["parsed_count"], 22)
        self.assertEqual(summary["failed_count"], 1)
        self.assertEqual(summary["occurrence_count"], 22)

        records = self.store.get_import_run_detail(run_id)
        self.assertEqual(len(records), 23)
        self.assertEqual(
            [record["source_locator"] for record in records],
            [f"csv-row:{row}" for row in range(2, 25)],
        )
        failures = [record for record in records if record["parse_status"] == "failed"]
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["source_locator"], "csv-row:21")
        self.assertEqual(failures[0]["error_code"], "missing_amount")
        self.assertIn("BROKEN ROW NO AMOUNT", failures[0]["retained_input"])
        self.assertIsNone(failures[0]["normalized_transaction"])
        self.assertEqual(
            failures[0]["inclusion_reason"],
            "parse_failed:missing_amount",
        )

        transactions = [
            record["normalized_transaction"]
            for record in records
            if record["normalized_transaction"] is not None
        ]
        self.assertEqual(len(transactions), 22)
        for transaction in transactions:
            date.fromisoformat(transaction["transaction_date"])
            self.assertTrue(transaction["merchant"].strip())
            self.assertFalse(transaction["merchant"].strip().isnumeric())
            self.assertIs(type(transaction["amount_minor"]), int)
            self.assertEqual(transaction["currency"], "CAD")
            self.assertEqual(
                transaction["is_spending"],
                transaction["amount_minor"] < 0,
            )

        by_merchant = {transaction["merchant"]: transaction for transaction in transactions}
        self.assertEqual(by_merchant["AMAZON.CA REFUND 702-441"]["amount_minor"], 12999)
        self.assertFalse(by_merchant["AMAZON.CA REFUND 702-441"]["is_spending"])
        self.assertEqual(by_merchant["E-TRANSFER RECEIVED J. WU"]["amount_minor"], 60000)
        self.assertFalse(by_merchant["E-TRANSFER RECEIVED J. WU"]["is_spending"])
        self.assertEqual(sum(transaction["amount_minor"] < 0 for transaction in transactions), 20)


if __name__ == "__main__":
    unittest.main()
