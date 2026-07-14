from __future__ import annotations

from tests.backend.analysis_support import AnalysisStoreTestCase


class AnalysisInclusionTests(AnalysisStoreTestCase):
    def _import_component_identity(
        self,
        label: str,
        *,
        group: str = "ONE",
        content: bytes | None = None,
    ) -> tuple[bytes, str, str]:
        if content is None:
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
        return content, run_id, identity_id

    def _component_candidate(self, left_identity_id: str, right_identity_id: str):
        expected = {left_identity_id, right_identity_id}
        matches = [
            candidate
            for candidate in self.analysis.list_duplicate_candidates()
            if {candidate.left_identity_id, candidate.right_identity_id} == expected
        ]
        self.assertEqual(len(matches), 1)
        return matches[0]

    def _included_identity_ids(self) -> set[str]:
        if not self.analysis.list_months():
            return set()
        return {
            transaction.identity_id
            for transaction in self.analysis.get_month_summary("2026-06").transactions
            if transaction.included
        }

    def test_reimport_and_run_support_change_analysis_only_at_final_undo(self) -> None:
        first_pdf = self.import_pdf()
        first_csv = self.import_csv()
        baseline_may = self.analysis.get_month_summary("2026-05")
        baseline_june = self.analysis.get_month_summary("2026-06")
        second_pdf = self.import_pdf("same-may-new-name.pdf")
        second_csv = self.import_csv("same-june-new-name.csv")

        for baseline in (baseline_may, baseline_june):
            reimported = self.analysis.get_month_summary(baseline.month)
            self.assertEqual(
                (
                    reimported.spending_total_minor,
                    reimported.credit_total_minor,
                    reimported.transaction_count,
                    reimported.spending_transaction_count,
                    reimported.credit_transaction_count,
                    self.category_map(reimported),
                ),
                (
                    baseline.spending_total_minor,
                    baseline.credit_total_minor,
                    baseline.transaction_count,
                    baseline.spending_transaction_count,
                    baseline.credit_transaction_count,
                    self.category_map(baseline),
                ),
            )
        self.assertTrue(
            all(
                len(transaction.active_supports) == 2
                for transaction in self.analysis.get_month_summary("2026-06").transactions
            )
        )

        self.store.undo_import_run(first_csv)
        self.store.undo_import_run(first_pdf)
        self.assertEqual(
            self.analysis.get_month_summary("2026-05").spending_total_minor,
            50_340,
        )
        self.assertEqual(
            self.analysis.get_month_summary("2026-06").spending_total_minor,
            277_617,
        )
        self.store.undo_import_run(second_csv)
        self.assertEqual(self.analysis.list_months(), ("2026-05",))
        with self.assertRaises(KeyError):
            self.analysis.get_month_summary("2026-06")
        self.store.undo_import_run(second_pdf)
        self.assertEqual(self.analysis.list_months(), ())

    def test_credits_and_failed_rows_never_enter_spending_or_transaction_counts(self) -> None:
        run_id = self.import_csv()
        run_summary = self.store.get_import_run_summary(run_id)
        summary = self.analysis.get_month_summary("2026-06")
        self.assertEqual(run_summary["source_record_count"], 23)
        self.assertEqual(run_summary["failed_count"], 1)
        self.assertEqual(summary.transaction_count, 22)
        self.assertEqual(len(summary.transactions), 22)
        positive = [
            transaction
            for transaction in summary.transactions
            if transaction.amount_minor > 0
        ]
        self.assertEqual(
            [(transaction.amount_minor, transaction.is_spending) for transaction in positive],
            [(12_999, False), (60_000, False)],
        )
        self.assertEqual(
            summary.spending_total_minor,
            sum(
                -transaction.amount_minor
                for transaction in summary.transactions
                if transaction.included and transaction.amount_minor < 0
            ),
        )
        self.assertTrue(
            all(
                record["normalized_transaction"] is None
                for record in self.store.get_import_run_detail(run_id)
                if record["parse_status"] == "failed"
            )
        )

    def test_mixed_currency_month_is_rejected_without_conversion(self) -> None:
        self.import_csv()
        run_id = self.store.create_import_run("sha256:synthetic-usd")
        source_id = self.store.add_source_record(
            run_id,
            source_locator="csv-row:2",
            retained_input="synthetic:usd",
            parse_status="parsed",
        )
        identity_id = self.store.get_or_create_identity("synthetic:usd:identity")
        self.store.add_normalized_transaction(
            identity_id,
            transaction_date="2026-06-30",
            merchant="SYNTHETIC USD",
            amount_minor=-100,
            currency="USD",
        )
        self.store.add_occurrence(
            run_id,
            source_record_id=source_id,
            identity_id=identity_id,
            amount_minor=-100,
            currency="USD",
        )
        with self.assertRaises(ValueError):
            self.analysis.get_month_summary("2026-06")

    def test_component_fallback_support_append_and_keeper_restore_preserve_history(self) -> None:
        imported = {
            label: self._import_component_identity(label)
            for label in "ABC"
        }
        ids = {label: imported[label][2] for label in imported}
        ab = self._component_candidate(ids["A"], ids["B"])
        bc = self._component_candidate(ids["B"], ids["C"])
        self.analysis.set_duplicate_decision(
            ab.duplicate_link_id,
            "same_transaction",
            ids["A"],
        )
        self.analysis.set_duplicate_decision(
            bc.duplicate_link_id,
            "same_transaction",
            ids["B"],
        )
        history_ids = {
            candidate.duplicate_link_id: tuple(
                decision.decision_id for decision in candidate.history
            )
            for candidate in self.analysis.list_duplicate_candidates()
        }

        self.store.undo_import_run(imported["A"][1])
        self.assertEqual(self._included_identity_ids(), {min(ids["B"], ids["C"])})

        _, second_b_run, second_b_identity = self._import_component_identity(
            "B",
            content=imported["B"][0],
        )
        self.assertEqual(second_b_identity, ids["B"])
        self.assertEqual(self._included_identity_ids(), {min(ids["B"], ids["C"])})
        self.assertEqual(
            {
                candidate.duplicate_link_id: tuple(
                    decision.decision_id for decision in candidate.history
                )
                for candidate in self.analysis.list_duplicate_candidates()
            },
            history_ids,
        )

        self.store.undo_import_run(imported["B"][1])
        self.store.undo_import_run(second_b_run)
        self.store.undo_import_run(imported["C"][1])
        self.assertEqual(self._included_identity_ids(), set())

        _, _, restored_b_identity = self._import_component_identity(
            "B",
            content=imported["B"][0],
        )
        self.assertEqual(restored_b_identity, ids["B"])
        self.assertEqual(self._included_identity_ids(), {ids["B"]})

        _, _, restored_a_identity = self._import_component_identity(
            "A",
            content=imported["A"][0],
        )
        self.assertEqual(restored_a_identity, ids["A"])
        self.assertEqual(self._included_identity_ids(), {ids["A"]})
        self.assertEqual(
            {
                candidate.duplicate_link_id: tuple(
                    decision.decision_id for decision in candidate.history
                )
                for candidate in self.analysis.list_duplicate_candidates()
            },
            history_ids,
        )

    def test_disconnected_component_fallback_does_not_change_other_keeper(self) -> None:
        imported = {
            "A": self._import_component_identity("A", group="ONE"),
            "B": self._import_component_identity("B", group="ONE"),
            "C": self._import_component_identity("C", group="TWO"),
            "D": self._import_component_identity("D", group="TWO"),
        }
        ids = {label: imported[label][2] for label in imported}
        ab = self._component_candidate(ids["A"], ids["B"])
        cd = self._component_candidate(ids["C"], ids["D"])
        self.analysis.set_duplicate_decision(
            ab.duplicate_link_id,
            "same_transaction",
            ids["A"],
        )
        self.analysis.set_duplicate_decision(
            cd.duplicate_link_id,
            "same_transaction",
            ids["C"],
        )

        self.store.undo_import_run(imported["A"][1])
        self.assertEqual(self._included_identity_ids(), {ids["B"], ids["C"]})


if __name__ == "__main__":
    import unittest

    unittest.main()
