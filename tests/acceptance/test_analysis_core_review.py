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


if __name__ == "__main__":
    import unittest

    unittest.main()
