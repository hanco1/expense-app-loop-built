from __future__ import annotations

import sqlite3
from contextlib import closing

from tests.backend.support import StoreTestCase


class IngestInvariantTests(StoreTestCase):
    def test_failed_source_input_is_retained_with_explicit_error(self) -> None:
        run_id = self.store.create_import_run("sha256:invalid-synthetic")
        source_id = self.store.add_source_record(
            run_id,
            source_locator="csv-row:4",
            retained_input="synthetic,not-an-amount",
            parse_status="failed",
            error_code="INVALID_AMOUNT",
        )

        record = self.store.get_source_record(source_id)
        self.assertEqual(record["retained_input"], "synthetic,not-an-amount")
        self.assertEqual(record["parse_status"], "failed")
        self.assertEqual(record["error_code"], "INVALID_AMOUNT")

    def test_source_records_cannot_be_overwritten_or_deleted(self) -> None:
        run_id = self.store.create_import_run("sha256:add-only")
        source_id = self.store.add_source_record(
            run_id,
            source_locator="csv-row:2",
            retained_input="synthetic,original",
            parse_status="parsed",
        )
        with closing(sqlite3.connect(self.database_path)) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "UPDATE source_records SET retained_input = ? "
                    "WHERE source_record_id = ?",
                    ("synthetic,overwritten", source_id),
                )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "DELETE FROM source_records WHERE source_record_id = ?",
                    (source_id,),
                )

        self.assertEqual(
            self.store.get_source_record(source_id)["retained_input"],
            "synthetic,original",
        )

    def test_failed_status_requires_error_and_undo_never_deletes(self) -> None:
        run_id = self.store.create_import_run("sha256:explicit-failure")
        with self.assertRaises(ValueError):
            self.store.add_source_record(
                run_id,
                source_locator="csv-row:9",
                retained_input="synthetic,bad",
                parse_status="failed",
            )
        self.add_parsed_occurrence(
            run_id,
            locator="csv-row:2",
            identity_fingerprint="txn:preserved",
        )
        before = self.store.entity_counts()
        self.store.undo_import_run(run_id)
        self.assertEqual(before, self.store.entity_counts())


if __name__ == "__main__":
    import unittest

    unittest.main()
