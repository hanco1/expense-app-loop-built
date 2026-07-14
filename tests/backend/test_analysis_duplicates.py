from __future__ import annotations

import sqlite3
from contextlib import closing

from tests.backend.analysis_support import AnalysisStoreTestCase


class AnalysisDuplicateDecisionTests(AnalysisStoreTestCase):
    def _import_duplicate_identity(
        self,
        label: str,
        *,
        group: str = "ONE",
    ) -> tuple[str, str]:
        balance = ord(label) - ord("A")
        content = (
            "Date,Description,Debit,Credit,Balance\r\n"
            f"06/01/2026,COMPONENT {group} COFFEE,4.50,,{balance}.00\r\n"
        ).encode("ascii")
        run_id = self.importer.import_bytes(
            content,
            filename=f"component-{label}.csv",
            source_type="csv",
        )
        identity_id = str(self.store.list_occurrences(run_id)[0]["identity_id"])
        return run_id, identity_id

    def _candidate_for(self, left_identity_id: str, right_identity_id: str):
        expected = {left_identity_id, right_identity_id}
        matches = [
            candidate
            for candidate in self.analysis.list_duplicate_candidates()
            if {candidate.left_identity_id, candidate.right_identity_id} == expected
        ]
        self.assertEqual(len(matches), 1)
        return matches[0]

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

    def test_cycle_closing_decision_is_rejected_before_history_append(self) -> None:
        content = (
            b"Date,Description,Debit,Credit,Balance\r\n"
            b"06/01/2026,TRIPLE COFFEE,4.50,,0.00\r\n"
            b"06/01/2026,TRIPLE COFFEE,4.50,,0.00\r\n"
            b"06/01/2026,TRIPLE COFFEE,4.50,,0.00\r\n"
        )
        run_id = self.importer.import_bytes(
            content,
            filename="synthetic-triple-duplicate.csv",
            source_type="csv",
        )
        candidates = self.analysis.list_duplicate_candidates()
        self.assertEqual(len(candidates), 3)
        identities = sorted(
            {
                identity_id
                for candidate in candidates
                for identity_id in (
                    candidate.left_identity_id,
                    candidate.right_identity_id,
                )
            }
        )
        first, second, third = identities
        candidates_by_pair = {
            (candidate.left_identity_id, candidate.right_identity_id): candidate
            for candidate in candidates
        }

        self.analysis.set_duplicate_decision(
            candidates_by_pair[(first, second)].duplicate_link_id,
            "same_transaction",
            first,
        )
        self.analysis.set_duplicate_decision(
            candidates_by_pair[(second, third)].duplicate_link_id,
            "same_transaction",
            second,
        )
        cycle_link = candidates_by_pair[(first, third)]
        with self.assertRaisesRegex(ValueError, "structural keeper"):
            self.analysis.set_duplicate_decision(
                cycle_link.duplicate_link_id,
                "same_transaction",
                third,
            )

        self.assertEqual(
            self.store.list_duplicate_decisions(cycle_link.duplicate_link_id),
            [],
        )
        summary = self.analysis.get_month_summary("2026-06")
        self.assertEqual(summary.transaction_count, 1)
        self.assertEqual(summary.spending_total_minor, 450)
        self.assertEqual(
            sum(transaction.included for transaction in summary.transactions),
            1,
        )
        self.assertEqual(len(self.store.list_effective_transactions()), 3)

        self.store.undo_import_run(run_id)
        self.assertEqual(self.analysis.list_months(), ())
        self.importer.import_bytes(
            content,
            filename="renamed-triple-duplicate.csv",
            source_type="csv",
        )
        restored = self.analysis.get_month_summary("2026-06")
        self.assertEqual(restored.transaction_count, 1)
        self.assertEqual(restored.spending_total_minor, 450)
        self.assertEqual(
            len(
                self.store.list_duplicate_decisions(
                    candidates_by_pair[(first, second)].duplicate_link_id
                )
            ),
            1,
        )
        self.assertEqual(
            len(
                self.store.list_duplicate_decisions(
                    candidates_by_pair[(second, third)].duplicate_link_id
                )
            ),
            1,
        )
        self.assertEqual(
            self.store.list_duplicate_decisions(cycle_link.duplicate_link_id),
            [],
        )

    def test_component_proposals_reject_multiple_keepers_and_nonbridge_distinct(self) -> None:
        identities = {
            label: self._import_duplicate_identity(label)[1]
            for label in "ABCD"
        }

        def decide(
            left: str,
            right: str,
            decision: str,
            keeper: str | None = None,
        ):
            candidate = self._candidate_for(identities[left], identities[right])
            return self.analysis.set_duplicate_decision(
                candidate.duplicate_link_id,
                decision,
                None if keeper is None else identities[keeper],
            )

        decide("A", "B", "same_transaction", "A")
        bc = self._candidate_for(identities["B"], identities["C"])
        with self.assertRaisesRegex(ValueError, "exactly one structural keeper"):
            decide("B", "C", "same_transaction", "C")
        self.assertEqual(self.store.list_duplicate_decisions(bc.duplicate_link_id), [])

        decide("B", "C", "same_transaction", "B")
        decide("A", "C", "same_transaction", "A")
        ab = self._candidate_for(identities["A"], identities["B"])
        ab_history = tuple(decision.decision_id for decision in ab.history)
        with self.assertRaisesRegex(ValueError, "alternate same_transaction path"):
            decide("A", "B", "distinct")
        self.assertEqual(
            tuple(
                decision["decision_id"]
                for decision in self.store.list_duplicate_decisions(
                    ab.duplicate_link_id
                )
            ),
            ab_history,
        )

    def test_component_merge_rejects_two_structural_keepers_without_history(self) -> None:
        identities = {
            label: self._import_duplicate_identity(label)[1]
            for label in "ABCD"
        }
        ab = self._candidate_for(identities["A"], identities["B"])
        cd = self._candidate_for(identities["C"], identities["D"])
        bd = self._candidate_for(identities["B"], identities["D"])
        self.analysis.set_duplicate_decision(
            ab.duplicate_link_id,
            "same_transaction",
            identities["A"],
        )
        self.analysis.set_duplicate_decision(
            cd.duplicate_link_id,
            "same_transaction",
            identities["C"],
        )

        before = self.store.entity_counts()["duplicate_decisions"]
        with self.assertRaisesRegex(ValueError, "exactly one structural keeper"):
            self.analysis.set_duplicate_decision(
                bd.duplicate_link_id,
                "same_transaction",
                identities["B"],
            )
        self.assertEqual(self.store.list_duplicate_decisions(bd.duplicate_link_id), [])
        self.assertEqual(
            self.store.entity_counts()["duplicate_decisions"],
            before,
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
