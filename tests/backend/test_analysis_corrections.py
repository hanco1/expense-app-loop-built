from __future__ import annotations

import sqlite3

from tests.backend.analysis_support import AnalysisStoreTestCase


class AnalysisCorrectionTests(AnalysisStoreTestCase):
    def test_category_corrections_are_append_only_latest_wins_and_survive_runs(self) -> None:
        first_run = self.import_csv()
        second_run = self.import_csv("same-june-new-name.csv")
        before = self.transaction(
            self.analysis.get_month_summary("2026-06"),
            merchant="SQ *COFFEE CO TORONTO ON",
        )
        identity_id = before.identity_id
        normalized_before = self.store.get_normalized_transaction(identity_id)
        self.assertEqual(before.auto_category, "Dining")
        self.assertEqual(before.category_source, "auto")

        with self.assertRaises(ValueError):
            self.analysis.set_category(identity_id, "Travel")
        self.assertEqual(self.store.list_category_corrections(identity_id), [])
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.add_manual_correction(
                identity_id,
                correction_type="category",
                value="Travel",
            )
        self.assertEqual(self.store.list_category_corrections(identity_id), [])

        first_state = self.analysis.set_category(identity_id, "Shopping")
        second_state = self.analysis.set_category(identity_id, "Groceries")
        self.assertEqual(first_state.effective_category, "Shopping")
        self.assertEqual(second_state.effective_category, "Groceries")
        self.assertEqual(second_state.category_source, "human")
        self.assertEqual(
            [correction.category for correction in second_state.history],
            ["Shopping", "Groceries"],
        )
        self.assertEqual(
            second_state.effective_correction_id,
            second_state.history[-1].correction_id,
        )
        corrected_categories = self.category_map(
            self.analysis.get_month_summary("2026-06")
        )
        self.assertEqual(corrected_categories["Dining"], 1_425)
        self.assertEqual(corrected_categories["Groceries"], 26_402)

        self.store.undo_import_run(first_run)
        self.assertEqual(
            self.analysis.get_month_summary("2026-06").transaction_count,
            22,
        )
        self.store.undo_import_run(second_run)
        self.assertEqual(self.analysis.list_months(), ())
        hidden_state = self.analysis.get_category_state(identity_id)
        self.assertEqual(hidden_state.effective_category, "Groceries")
        self.assertEqual(hidden_state.history, second_state.history)

        restored_run = self.import_csv("later-restored-june.csv")
        restored = self.transaction(
            self.analysis.get_month_summary("2026-06"),
            merchant="SQ *COFFEE CO TORONTO ON",
        )
        self.assertEqual(restored.identity_id, identity_id)
        self.assertEqual(restored.effective_category, "Groceries")
        self.assertEqual(restored.category_source, "human")
        self.assertEqual(
            restored.correction_ids,
            tuple(correction.correction_id for correction in second_state.history),
        )
        self.assertEqual(
            self.store.get_normalized_transaction(identity_id),
            normalized_before,
        )
        restored_detail = self.store.get_import_run_detail(restored_run)
        self.assertTrue(
            any(record["identity_id"] == identity_id for record in restored_detail)
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
