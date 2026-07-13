from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

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

    def test_out_of_range_amount_is_retained_as_an_explicit_failure(self) -> None:
        content = (
            b"Date,Description,Debit,Credit,Balance\r\n"
            b"06/01/2026,FIRST GOOD ROW,1.00,,99.00\r\n"
            b"06/02/2026,OVERSIZED ROW,999999999999999999999999999999.00,,0.00\r\n"
        )

        run_id = self.importer.import_bytes(
            content,
            filename="supported-shape.csv",
            source_type="csv",
        )

        summary = self.store.get_import_run_summary(run_id)
        self.assertEqual(summary["state"], "active")
        self.assertEqual(
            (
                summary["source_record_count"],
                summary["parsed_count"],
                summary["failed_count"],
                summary["occurrence_count"],
            ),
            (2, 1, 1, 1),
        )
        failure = self.store.get_import_run_detail(run_id)[1]
        self.assertEqual(failure["parse_status"], "failed")
        self.assertEqual(failure["error_code"], "invalid_amount")
        self.assertIsNone(failure["normalized_transaction"])
        self.assertEqual(failure["inclusion_reason"], "parse_failed:invalid_amount")

    def test_unexpected_persistence_failure_leaves_no_active_support(self) -> None:
        content = (
            b"Date,Description,Debit,Credit,Balance\r\n"
            b"06/01/2026,FIRST ROW,1.00,,99.00\r\n"
            b"06/02/2026,SECOND ROW,2.00,,97.00\r\n"
        )
        original_add_occurrence = self.store.add_occurrence
        occurrence_calls = 0

        def fail_second_occurrence(*args: object, **kwargs: object) -> str:
            nonlocal occurrence_calls
            occurrence_calls += 1
            if occurrence_calls == 2:
                raise RuntimeError("synthetic persistence failure")
            return original_add_occurrence(*args, **kwargs)

        with patch.object(
            self.store,
            "add_occurrence",
            side_effect=fail_second_occurrence,
        ):
            with self.assertRaises(RuntimeError) as raised:
                self.importer.import_bytes(
                    content,
                    filename="later-persistence-failure.csv",
                    source_type="csv",
                )

        run_id = getattr(raised.exception, "run_id", None)
        self.assertIsInstance(run_id, str)
        summary = self.store.get_import_run_summary(run_id)
        self.assertEqual(summary["state"], "failed")
        self.assertEqual(self.store.list_effective_transactions(), [])
        detail = self.store.get_import_run_detail(run_id)
        self.assertEqual(detail[0]["inclusion_state"], "excluded")
        self.assertEqual(detail[0]["inclusion_reason"], "import_failed")
        self.assertEqual(detail[1]["parse_status"], "parsed")
        self.assertIsNone(detail[1]["occurrence_id"])
        self.assertEqual(detail[1]["inclusion_reason"], "persistence_incomplete")


if __name__ == "__main__":
    unittest.main()
