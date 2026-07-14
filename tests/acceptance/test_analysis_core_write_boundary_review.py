from __future__ import annotations

from tests.backend.analysis_support import AnalysisStoreTestCase


class DuplicateDecisionWriteBoundaryReviewTests(AnalysisStoreTestCase):
    def _import_identity(self, label: str) -> str:
        balance = ord(label) - ord("A")
        content = (
            "Date,Description,Debit,Credit,Balance\r\n"
            f"06/01/2026,WRITE BOUNDARY COFFEE,4.50,,{balance}.00\r\n"
        ).encode("ascii")
        run_id = self.importer.import_bytes(
            content,
            filename=f"write-boundary-{label}.csv",
            source_type="csv",
        )
        return str(self.store.list_occurrences(run_id)[0]["identity_id"])

    def _link_id(self, left_identity_id: str, right_identity_id: str) -> str:
        expected = {left_identity_id, right_identity_id}
        matches = [
            pair
            for pair in self.store.list_suspected_duplicate_pairs()
            if {str(pair["left_identity_id"]), str(pair["right_identity_id"])}
            == expected
        ]
        self.assertEqual(len(matches), 1)
        return str(matches[0]["duplicate_link_id"])

    def test_public_store_write_rejects_zero_keeper_before_history_append(self) -> None:
        identities = {
            label: self._import_identity(label)
            for label in "ABC"
        }
        ab_link_id = self._link_id(identities["A"], identities["B"])
        bc_link_id = self._link_id(identities["B"], identities["C"])
        ac_link_id = self._link_id(identities["A"], identities["C"])

        self.store.add_duplicate_decision(
            ab_link_id,
            decision="same_transaction",
            kept_identity_id=identities["A"],
        )
        self.store.add_duplicate_decision(
            bc_link_id,
            decision="same_transaction",
            kept_identity_id=identities["B"],
        )
        before = self.store.entity_counts()["duplicate_decisions"]

        with self.assertRaisesRegex(ValueError, "structural keeper"):
            self.store.add_duplicate_decision(
                ac_link_id,
                decision="same_transaction",
                kept_identity_id=identities["C"],
            )

        self.assertEqual(
            self.store.entity_counts()["duplicate_decisions"],
            before,
        )
        self.assertEqual(self.store.list_duplicate_decisions(ac_link_id), [])


if __name__ == "__main__":
    import unittest

    unittest.main()
