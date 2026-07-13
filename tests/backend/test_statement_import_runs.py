from __future__ import annotations

import unittest

from tests.backend.statement_support import StatementStoreTestCase


class StatementImportRunTests(StatementStoreTestCase):
    def test_run_inspection_undo_support_and_corrections_survive_reimport(self) -> None:
        first_run = self.import_csv()
        second_run = self.import_csv("same-bytes-new-name.csv")
        self.assertNotEqual(first_run, second_run)

        first_summary = self.store.get_import_run_summary(first_run)
        second_summary = self.store.get_import_run_summary(second_run)
        self.assertEqual(second_summary["exact_reimport_of_run_id"], first_run)
        for summary in (first_summary, second_summary):
            self.assertEqual(
                set(summary),
                {
                    "run_id",
                    "created_at",
                    "source_name",
                    "source_type",
                    "source_fingerprint",
                    "state",
                    "exact_reimport_of_run_id",
                    "source_record_count",
                    "parsed_count",
                    "failed_count",
                    "occurrence_count",
                },
            )

        first_detail = self.store.get_import_run_detail(first_run)
        second_detail = self.store.get_import_run_detail(second_run)
        self.assertEqual({record["run_id"] for record in first_detail}, {first_run})
        self.assertEqual({record["run_id"] for record in second_detail}, {second_run})
        required_record_fields = {
            "source_record_id",
            "run_id",
            "source_name",
            "source_type",
            "source_fingerprint",
            "exact_reimport_of_run_id",
            "source_locator",
            "retained_input",
            "parse_status",
            "error_code",
            "occurrence_id",
            "identity_id",
            "normalized_transaction",
            "duplicate_state",
            "suspected_duplicate_identity_ids",
            "inclusion_state",
            "inclusion_reason",
        }
        self.assertTrue(all(set(record) == required_record_fields for record in first_detail))
        self.assertTrue(
            all(
                record["source_fingerprint"] == first_summary["source_fingerprint"]
                for record in first_detail
            )
        )

        supported_record = next(
            record for record in first_detail if record["source_locator"] == "csv-row:2"
        )
        identity_id = supported_record["identity_id"]
        correction_id = self.store.add_manual_correction(
            identity_id,
            correction_type="note",
            value="synthetic human correction",
        )
        counts_before_undo = self.store.entity_counts()
        effective_record = next(
            transaction
            for transaction in self.store.list_effective_transactions()
            if transaction["identity_id"] == identity_id
        )
        self.assertEqual(effective_record["active_support_count"], 2)
        self.assertEqual(
            {support["run_id"] for support in effective_record["active_supports"]},
            {first_run, second_run},
        )
        for support in effective_record["active_supports"]:
            self.assertEqual(
                {
                    "occurrence_id",
                    "run_id",
                    "source_name",
                    "source_type",
                    "source_fingerprint",
                    "source_record_id",
                    "source_locator",
                    "inclusion_state",
                    "inclusion_reason",
                },
                set(support),
            )

        self.store.undo_import_run(first_run)
        effective_after_first_undo = self.store.list_effective_transactions()
        self.assertEqual(len(effective_after_first_undo), 22)
        self.assertTrue(
            all(
                transaction["active_support_count"] == 1
                and len(transaction["active_supports"]) == 1
                and transaction["active_supports"][0]["run_id"] == second_run
                for transaction in effective_after_first_undo
            )
        )
        self.assertEqual(self.store.get_import_run_summary(first_run)["state"], "undone")
        self.assertEqual(self.store.get_import_run_summary(second_run)["state"], "active")
        self.assertTrue(
            all(
                record["inclusion_state"] == "excluded"
                for record in self.store.get_import_run_detail(first_run)
                if record["occurrence_id"] is not None
            )
        )
        self.assertTrue(
            all(
                record["inclusion_state"] == "included"
                for record in self.store.get_import_run_detail(second_run)
                if record["occurrence_id"] is not None
            )
        )

        self.store.undo_import_run(second_run)
        self.assertEqual(self.store.list_effective_transactions(), [])
        self.assertEqual(counts_before_undo, self.store.entity_counts())
        self.assertEqual(
            [row["correction_id"] for row in self.store.list_manual_corrections(identity_id)],
            [correction_id],
        )

        third_run = self.import_csv("restored-support.csv")
        self.assertEqual(len(self.store.list_effective_transactions()), 22)
        third_record = next(
            record
            for record in self.store.get_import_run_detail(third_run)
            if record["source_locator"] == "csv-row:2"
        )
        self.assertEqual(third_record["identity_id"], identity_id)
        self.assertEqual(
            [row["correction_id"] for row in self.store.list_manual_corrections(identity_id)],
            [correction_id],
        )

        provenance = self.store.get_statement_occurrence_provenance(
            third_record["occurrence_id"]
        )
        self.assertEqual(provenance["run_id"], third_run)
        self.assertEqual(provenance["source_fingerprint"], first_summary["source_fingerprint"])
        self.assertEqual(provenance["source_locator"], "csv-row:2")
        self.assertEqual(provenance["transaction_identity_id"], identity_id)
        self.assertEqual(provenance["duplicate_state"], "none")
        self.assertEqual(provenance["inclusion_state"], "included")
        self.assertEqual(provenance["inclusion_reason"], "active_support")


if __name__ == "__main__":
    unittest.main()
