from __future__ import annotations

import sqlite3
from contextlib import closing

from tests.backend.support import StoreTestCase


class ImportRunTests(StoreTestCase):
    def test_runs_are_opaque_distinct_and_membership_is_isolated(self) -> None:
        first_run = self.store.create_import_run("sha256:first-statement")
        second_run = self.store.create_import_run("sha256:second-statement")
        self.assertNotEqual(first_run, second_run)
        self.assertNotIn("first-statement", first_run)
        self.assertNotIn("second-statement", second_run)

        first_source, _, first_occurrence = self.add_parsed_occurrence(
            first_run,
            locator="csv-row:2",
            identity_fingerprint="txn:first",
        )
        second_source, _, second_occurrence = self.add_parsed_occurrence(
            second_run,
            locator="csv-row:8",
            identity_fingerprint="txn:second",
        )

        self.assertEqual(
            [row["source_record_id"] for row in self.store.list_source_records(first_run)],
            [first_source],
        )
        self.assertEqual(
            [row["occurrence_id"] for row in self.store.list_occurrences(first_run)],
            [first_occurrence],
        )
        self.assertEqual(
            [row["source_record_id"] for row in self.store.list_source_records(second_run)],
            [second_source],
        )
        self.assertEqual(
            [row["occurrence_id"] for row in self.store.list_occurrences(second_run)],
            [second_occurrence],
        )

    def test_undo_is_state_based_and_corrections_survive_reimport(self) -> None:
        run_id = self.store.create_import_run("sha256:statement-v1")
        _, identity_id, _ = self.add_parsed_occurrence(
            run_id,
            locator="pdf-page:1:record:3",
            identity_fingerprint="txn:coffee-2026-06-04",
        )
        correction_id = self.store.add_manual_correction(
            identity_id,
            correction_type="category",
            value="Dining",
        )
        counts_before = self.store.entity_counts()

        self.store.undo_import_run(run_id)

        self.assertEqual(self.store.get_import_run(run_id)["state"], "undone")
        self.assertEqual(
            {row["inclusion_state"] for row in self.store.list_occurrences(run_id)},
            {"excluded"},
        )
        self.assertEqual(counts_before, self.store.entity_counts())
        self.assertEqual(
            [row["correction_id"] for row in self.store.list_manual_corrections(identity_id)],
            [correction_id],
        )

        reimport_run = self.store.create_import_run("sha256:statement-v1")
        reimport_source = self.store.add_source_record(
            reimport_run,
            source_locator="pdf-page:1:record:3",
            retained_input="synthetic re-import",
            parse_status="parsed",
        )
        reimport_identity = self.store.get_or_create_identity(
            "txn:coffee-2026-06-04"
        )
        self.assertEqual(reimport_identity, identity_id)
        self.store.add_occurrence(
            reimport_run,
            source_record_id=reimport_source,
            identity_id=reimport_identity,
            amount_minor=-475,
            currency="CAD",
        )
        self.assertEqual(
            [row["correction_id"] for row in self.store.list_manual_corrections(identity_id)],
            [correction_id],
        )

    def test_undo_rolls_back_all_changes_if_any_occurrence_cannot_update(self) -> None:
        run_id = self.store.create_import_run("sha256:atomic-statement")
        self.add_parsed_occurrence(
            run_id,
            locator="csv-row:2",
            identity_fingerprint="txn:atomic-1",
        )
        _, _, blocked_occurrence = self.add_parsed_occurrence(
            run_id,
            locator="csv-row:3",
            identity_fingerprint="txn:atomic-2",
        )
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.execute(
                "CREATE TRIGGER test_abort_undo BEFORE UPDATE ON imported_occurrences "
                f"WHEN OLD.occurrence_id = '{blocked_occurrence}' "
                "BEGIN SELECT RAISE(ABORT, 'test abort'); END"
            )

        with self.assertRaises(sqlite3.IntegrityError):
            self.store.undo_import_run(run_id)

        self.assertEqual(self.store.get_import_run(run_id)["state"], "active")
        self.assertEqual(
            {row["inclusion_state"] for row in self.store.list_occurrences(run_id)},
            {"included"},
        )

    def test_undone_run_rejects_late_records_and_included_occurrences(self) -> None:
        run_id = self.store.create_import_run("sha256:terminal-run")
        existing_source_id = self.store.add_source_record(
            run_id,
            source_locator="csv-row:2",
            retained_input="synthetic,existing-before-undo",
            parse_status="parsed",
        )
        existing_identity_id = self.store.get_or_create_identity(
            "txn:existing-before-undo"
        )
        existing_occurrence_id = self.store.add_occurrence(
            run_id,
            source_record_id=existing_source_id,
            identity_id=existing_identity_id,
            amount_minor=-50,
            currency="CAD",
        )
        pending_source_id = self.store.add_source_record(
            run_id,
            source_locator="csv-row:3",
            retained_input="synthetic,pending-before-undo",
            parse_status="parsed",
        )
        pending_identity_id = self.store.get_or_create_identity(
            "txn:pending-before-undo"
        )

        self.store.undo_import_run(run_id)

        with self.assertRaises(sqlite3.IntegrityError):
            self.store.add_source_record(
                run_id,
                source_locator="csv-row:4",
                retained_input="synthetic,late-source",
                parse_status="parsed",
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.add_occurrence(
                run_id,
                source_record_id=pending_source_id,
                identity_id=pending_identity_id,
                amount_minor=-100,
                currency="CAD",
            )

        # Simulate an inconsistent row written before terminal-state guards existed.
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.execute(
                "UPDATE imported_occurrences "
                "SET inclusion_state = 'included', exclusion_reason = NULL "
                "WHERE occurrence_id = ?",
                (existing_occurrence_id,),
            )

        self.store.undo_import_run(run_id)

        self.assertEqual(self.store.get_import_run(run_id)["state"], "undone")
        self.assertEqual(len(self.store.list_source_records(run_id)), 2)
        self.assertFalse(
            any(
                occurrence["inclusion_state"] == "included"
                for occurrence in self.store.list_occurrences(run_id)
            )
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
