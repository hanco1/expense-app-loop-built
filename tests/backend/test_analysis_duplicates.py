from __future__ import annotations

import sqlite3
from contextlib import closing

from tests.backend.analysis_support import AnalysisStoreTestCase


class AnalysisDuplicateDecisionTests(AnalysisStoreTestCase):
    def test_duplicate_decisions_are_append_only_latest_wins_and_reversible(self) -> None:
        run_id = self.import_csv()
        raw_counts = self.store.entity_counts()
        candidate = self.analysis.list_duplicate_candidates()[0]
        self.assertEqual(candidate.effective_decision, "pending")
        self.assertTrue(candidate.left_included)
        self.assertTrue(candidate.right_included)
        self.assertEqual(candidate.history, ())

        with self.assertRaises(ValueError):
            self.analysis.set_duplicate_decision(
                candidate.duplicate_link_id,
                "same_transaction",
            )
        with self.assertRaises(ValueError):
            self.analysis.set_duplicate_decision(
                candidate.duplicate_link_id,
                "merge",
            )
        unrelated_identity = next(
            transaction["identity_id"]
            for transaction in self.store.list_effective_transactions()
            if transaction["identity_id"]
            not in {candidate.left_identity_id, candidate.right_identity_id}
        )
        with self.assertRaises(ValueError):
            self.analysis.set_duplicate_decision(
                candidate.duplicate_link_id,
                "same_transaction",
                unrelated_identity,
            )
        self.assertEqual(
            self.store.list_duplicate_decisions(candidate.duplicate_link_id),
            [],
        )

        same = self.analysis.set_duplicate_decision(
            candidate.duplicate_link_id,
            "same_transaction",
            candidate.left_identity_id,
        )
        self.assertEqual(same.effective_decision, "same_transaction")
        self.assertEqual(same.kept_identity_id, candidate.left_identity_id)
        self.assertTrue(same.left_included)
        self.assertFalse(same.right_included)
        self.assertEqual(len(same.history), 1)
        june = self.analysis.get_month_summary("2026-06")
        self.assertEqual(june.transaction_count, 21)
        self.assertEqual(june.spending_total_minor, 277_167)
        self.assertEqual(self.category_map(june)["Dining"], 1_650)
        tim_hortons = [
            transaction
            for transaction in june.transactions
            if transaction.merchant == "TIM HORTONS #2214 TORONTO ON"
            and transaction.amount_minor == -450
        ]
        self.assertEqual(len(tim_hortons), 2)
        self.assertEqual(sum(transaction.included for transaction in tim_hortons), 1)
        excluded = next(
            transaction for transaction in tim_hortons if not transaction.included
        )
        self.assertEqual(
            excluded.inclusion_reason,
            "human_duplicate_same_transaction",
        )
        self.assertEqual(excluded.duplicate_decision, "same_transaction")

        decision_id = same.history[0].decision_id
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "UPDATE duplicate_decisions SET decision = 'distinct', "
                    "kept_identity_id = NULL WHERE decision_id = ?",
                    (decision_id,),
                )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "DELETE FROM duplicate_decisions WHERE decision_id = ?",
                    (decision_id,),
                )

        distinct = self.analysis.set_duplicate_decision(
            candidate.duplicate_link_id,
            "distinct",
        )
        self.assertEqual(distinct.effective_decision, "distinct")
        self.assertIsNone(distinct.kept_identity_id)
        self.assertTrue(distinct.left_included)
        self.assertTrue(distinct.right_included)
        self.assertEqual(
            [decision.decision for decision in distinct.history],
            ["same_transaction", "distinct"],
        )
        restored = self.analysis.get_month_summary("2026-06")
        self.assertEqual(restored.transaction_count, 22)
        self.assertEqual(restored.spending_total_minor, 277_617)
        self.assertEqual(self.category_map(restored)["Dining"], 2_100)
        counts_after = self.store.entity_counts()
        for table, count in raw_counts.items():
            if table != "duplicate_decisions":
                self.assertEqual(counts_after[table], count)
        self.assertEqual(counts_after["duplicate_decisions"], 2)

        self.store.undo_import_run(run_id)
        self.assertEqual(self.analysis.list_months(), ())
        self.import_csv("duplicate-decision-restored.csv")
        reimported = self.analysis.get_duplicate_candidate(
            candidate.duplicate_link_id
        )
        self.assertEqual(reimported.effective_decision, "distinct")
        self.assertEqual(reimported.history, distinct.history)
        self.assertTrue(reimported.left_included)
        self.assertTrue(reimported.right_included)


if __name__ == "__main__":
    import unittest

    unittest.main()
