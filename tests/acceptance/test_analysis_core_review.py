from __future__ import annotations

from backend.analysis import AnalysisService
from tests.backend.statement_support import StatementStoreTestCase


class AnalysisCoreReviewTests(StatementStoreTestCase):
    def test_same_transaction_cycle_keeps_one_active_representative(self) -> None:
        content = (
            b"Date,Description,Debit,Credit,Balance\r\n"
            b"06/01/2026,TRIPLE COFFEE,4.50,,0.00\r\n"
            b"06/01/2026,TRIPLE COFFEE,4.50,,0.00\r\n"
            b"06/01/2026,TRIPLE COFFEE,4.50,,0.00\r\n"
        )
        self.importer.import_bytes(
            content,
            filename="synthetic-triple-duplicate.csv",
            source_type="csv",
        )
        analysis = AnalysisService(self.store)
        candidates = analysis.list_duplicate_candidates()
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

        analysis.set_duplicate_decision(
            candidates_by_pair[(first, second)].duplicate_link_id,
            "same_transaction",
            first,
        )
        analysis.set_duplicate_decision(
            candidates_by_pair[(second, third)].duplicate_link_id,
            "same_transaction",
            second,
        )
        try:
            analysis.set_duplicate_decision(
                candidates_by_pair[(first, third)].duplicate_link_id,
                "same_transaction",
                third,
            )
        except ValueError:
            # Rejecting the cycle before appending is a valid safeguard.
            pass

        self.assertEqual(len(self.store.list_effective_transactions()), 3)
        self.assertEqual(analysis.list_months(), ("2026-06",))
        summary = analysis.get_month_summary("2026-06")
        self.assertEqual(summary.transaction_count, 1)
        self.assertEqual(summary.spending_total_minor, 450)
        self.assertEqual(
            sum(transaction.included for transaction in summary.transactions),
            1,
        )

    def test_undoing_keeper_support_falls_back_to_active_duplicate(self) -> None:
        first_content = (
            b"Date,Description,Debit,Credit,Balance\r\n"
            b"06/01/2026,PARTIAL SUPPORT COFFEE,4.50,,0.00\r\n"
        )
        second_content = (
            b"Date,Description,Debit,Credit,Balance\r\n"
            b"06/01/2026,PARTIAL SUPPORT COFFEE,4.50,,1.00\r\n"
        )
        first_run = self.importer.import_bytes(
            first_content,
            filename="first-support.csv",
            source_type="csv",
        )
        second_run = self.importer.import_bytes(
            second_content,
            filename="second-support.csv",
            source_type="csv",
        )
        analysis = AnalysisService(self.store)
        candidate = analysis.list_duplicate_candidates()[0]
        accepted = analysis.set_duplicate_decision(
            candidate.duplicate_link_id,
            "same_transaction",
            candidate.left_identity_id,
        )
        self.assertEqual(len(accepted.history), 1)

        active_transactions = self.store.list_effective_transactions()
        support_run_by_identity = {
            str(transaction["identity_id"]): str(
                transaction["active_supports"][0]["run_id"]
            )
            for transaction in active_transactions
        }
        content_by_run = {
            first_run: first_content,
            second_run: second_content,
        }
        kept_run = support_run_by_identity[candidate.left_identity_id]
        other_identity_id = candidate.right_identity_id
        self.store.undo_import_run(kept_run)

        self.assertEqual(
            {
                str(transaction["identity_id"])
                for transaction in self.store.list_effective_transactions()
            },
            {other_identity_id},
        )
        self.assertEqual(analysis.list_months(), ("2026-06",))
        fallback = analysis.get_month_summary("2026-06")
        self.assertEqual(fallback.transaction_count, 1)
        self.assertEqual(fallback.spending_total_minor, 450)
        fallback_candidate = analysis.get_duplicate_candidate(
            candidate.duplicate_link_id
        )
        self.assertEqual(
            int(fallback_candidate.left_included)
            + int(fallback_candidate.right_included),
            1,
        )
        self.assertEqual(fallback_candidate.history, accepted.history)

        self.importer.import_bytes(
            content_by_run[kept_run],
            filename="restored-keeper-support.csv",
            source_type="csv",
        )
        restored = analysis.get_duplicate_candidate(candidate.duplicate_link_id)
        self.assertTrue(restored.left_included)
        self.assertFalse(restored.right_included)
        self.assertEqual(restored.history, accepted.history)
        self.assertEqual(
            analysis.get_month_summary("2026-06").spending_total_minor,
            450,
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
