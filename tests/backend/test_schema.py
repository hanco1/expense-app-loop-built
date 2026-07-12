from __future__ import annotations

import sqlite3
from contextlib import closing

from tests.backend.support import StoreTestCase


class SchemaTests(StoreTestCase):
    def test_required_entities_and_foreign_keys_exist(self) -> None:
        with closing(sqlite3.connect(self.database_path)) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            self.assertTrue(
                {
                    "import_runs",
                    "source_records",
                    "transaction_identities",
                    "imported_occurrences",
                    "manual_corrections",
                }.issubset(tables)
            )

            occurrence_targets = {
                row[2]
                for row in connection.execute(
                    "PRAGMA foreign_key_list(imported_occurrences)"
                )
            }
            self.assertEqual(
                occurrence_targets,
                {"import_runs", "source_records", "transaction_identities"},
            )
            correction_targets = {
                row[2]
                for row in connection.execute(
                    "PRAGMA foreign_key_list(manual_corrections)"
                )
            }
            self.assertEqual(correction_targets, {"transaction_identities"})

    def test_identity_fingerprint_source_locator_and_occurrence_are_unique(self) -> None:
        run_id = self.store.create_import_run("sha256:statement-a")
        source_id = self.store.add_source_record(
            run_id,
            source_locator="csv-row:2",
            retained_input="synthetic,row",
            parse_status="parsed",
        )
        identity_id = self.store.get_or_create_identity("txn:stable-a")

        with self.assertRaises(sqlite3.IntegrityError):
            self.store.add_source_record(
                run_id,
                source_locator="csv-row:2",
                retained_input="different synthetic value",
                parse_status="parsed",
            )

        occurrence_id = self.store.add_occurrence(
            run_id,
            source_record_id=source_id,
            identity_id=identity_id,
            amount_minor=-100,
            currency="CAD",
        )
        self.assertTrue(occurrence_id)
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.add_occurrence(
                run_id,
                source_record_id=source_id,
                identity_id=identity_id,
                amount_minor=-100,
                currency="CAD",
            )

        with closing(sqlite3.connect(self.database_path)) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO transaction_identities "
                    "(identity_id, fingerprint, created_at) VALUES (?, ?, ?)",
                    ("other-id", "txn:stable-a", "2026-01-01T00:00:00Z"),
                )


if __name__ == "__main__":
    import unittest

    unittest.main()
