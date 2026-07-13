from __future__ import annotations

import unittest

from tests.backend.statement_support import StatementStoreTestCase


class StatementImportIdempotencyTests(StatementStoreTestCase):
    def test_exact_reimports_share_identities_and_legal_lookalikes_remain_distinct(self) -> None:
        first_csv_run = self.import_csv()
        self.assertEqual(len(self.store.list_effective_transactions()), 22)
        identity_count = self.store.entity_counts()["transaction_identities"]

        renamed_csv_run = self.import_csv("renamed-june.csv")
        self.assertNotEqual(first_csv_run, renamed_csv_run)
        renamed_summary = self.store.get_import_run_summary(renamed_csv_run)
        self.assertEqual(renamed_summary["exact_reimport_of_run_id"], first_csv_run)
        effective_csv = self.store.list_effective_transactions()
        self.assertEqual(len(effective_csv), 22)
        self.assertTrue(
            all(transaction["active_support_count"] == 2 for transaction in effective_csv)
        )
        self.assertTrue(
            all(len(transaction["active_supports"]) == 2 for transaction in effective_csv)
        )
        self.assertEqual(
            self.store.entity_counts()["transaction_identities"],
            identity_count,
        )

        tim_hortons = [
            transaction
            for transaction in self.store.list_effective_transactions()
            if transaction["transaction_date"] == "2026-06-01"
            and transaction["merchant"] == "TIM HORTONS #2214 TORONTO ON"
            and transaction["amount_minor"] == -450
        ]
        self.assertEqual(len(tim_hortons), 2)
        self.assertEqual(len({transaction["identity_id"] for transaction in tim_hortons}), 2)
        self.assertTrue(all(transaction["inclusion_state"] == "included" for transaction in tim_hortons))

        suspected_pairs = self.store.list_suspected_duplicate_pairs()
        self.assertEqual(len(suspected_pairs), 1)
        self.assertEqual(suspected_pairs[0]["state"], "suspected_pending")
        self.assertTrue(suspected_pairs[0]["both_included"])
        self.assertEqual(
            {
                suspected_pairs[0]["left_identity_id"],
                suspected_pairs[0]["right_identity_id"],
            },
            {transaction["identity_id"] for transaction in tim_hortons},
        )
        reimported_tim_records = [
            record
            for record in self.store.get_import_run_detail(renamed_csv_run)
            if record["normalized_transaction"] is not None
            and record["normalized_transaction"]["transaction_date"] == "2026-06-01"
            and record["normalized_transaction"]["merchant"]
            == "TIM HORTONS #2214 TORONTO ON"
        ]
        self.assertEqual(len(reimported_tim_records), 2)
        self.assertTrue(
            all(
                record["duplicate_state"] == "suspected_pending"
                and record["inclusion_state"] == "included"
                and record["exact_reimport_of_run_id"] == first_csv_run
                for record in reimported_tim_records
            )
        )

        first_pdf_run = self.import_pdf()
        self.assertEqual(len(self.store.list_effective_transactions()), 34)
        renamed_pdf_run = self.import_pdf("renamed-may.pdf")
        self.assertEqual(
            self.store.get_import_run_summary(renamed_pdf_run)["exact_reimport_of_run_id"],
            first_pdf_run,
        )
        effective = self.store.list_effective_transactions()
        self.assertEqual(len(effective), 34)

        loblaws = [transaction for transaction in effective if transaction["merchant"] == "LOBLAWS 1049 TORONTO ON"]
        self.assertEqual(len(loblaws), 3)
        self.assertEqual(len({transaction["identity_id"] for transaction in loblaws}), 3)
        self.assertEqual(
            {transaction["transaction_date"] for transaction in loblaws},
            {"2026-05-02", "2026-06-02", "2026-06-21"},
        )


if __name__ == "__main__":
    unittest.main()
