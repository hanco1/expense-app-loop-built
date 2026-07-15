from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import backend
from backend import AnalysisService as PackageAnalysisService
from backend import CoreStore as PackageCoreStore
from backend.analysis import AnalysisService as ModuleAnalysisService
from backend.analysis import CoreStore as AnalysisModuleCoreStore
from backend.persistence import CoreStore as ModuleCoreStore
from backend.statement_import import CoreStore as ImportModuleCoreStore
from tests.backend.analysis_support import AnalysisStoreTestCase


Decision = tuple[str, str, str, str]
SupportState = Literal["active", "partial", "inactive"]

MATRIX_DOCUMENT = (
    Path(__file__).parents[2]
    / "docs"
    / "review"
    / "REQ-20260714-064051-data-eng-iter-4-write-boundary-matrix.md"
)


@dataclass(frozen=True)
class WriterSpec:
    writer_id: str
    import_path: str
    writer_kind: Literal["service", "store"]


@dataclass(frozen=True)
class ProposalSpec:
    proposal_id: str
    labels: str
    pre_decisions: tuple[Decision, ...]
    proposal: Decision
    expect_reject: bool
    description: str


@dataclass(frozen=True)
class SupportSpec:
    support_id: str
    state: SupportState


@dataclass(frozen=True)
class BoundaryCase:
    case_id: str
    writer: WriterSpec
    proposal: ProposalSpec
    support: SupportSpec


WRITERS = (
    WriterSpec("SP", "backend.AnalysisService", "service"),
    WriterSpec("SM", "backend.analysis.AnalysisService", "service"),
    WriterSpec("CP", "backend.CoreStore", "store"),
    WriterSpec("CM", "backend.persistence.CoreStore", "store"),
    WriterSpec("CA", "backend.analysis.CoreStore", "store"),
    WriterSpec("CT", "backend.statement_import.CoreStore", "store"),
)

PROPOSALS = (
    ProposalSpec(
        "ZK",
        "ABC",
        (("A", "B", "same_transaction", "A"),
         ("B", "C", "same_transaction", "B")),
        ("A", "C", "same_transaction", "C"),
        True,
        "zero-structural-keeper triangle closure",
    ),
    ProposalSpec(
        "MC",
        "ABC",
        (("A", "B", "same_transaction", "A"),),
        ("B", "C", "same_transaction", "C"),
        True,
        "multiple-structural-keeper chain",
    ),
    ProposalSpec(
        "MM",
        "ABCD",
        (("A", "B", "same_transaction", "A"),
         ("C", "D", "same_transaction", "C")),
        ("B", "D", "same_transaction", "B"),
        True,
        "multiple-structural-keeper component merge",
    ),
    ProposalSpec(
        "AD",
        "ABC",
        (("A", "B", "same_transaction", "A"),
         ("A", "C", "same_transaction", "A"),
         ("B", "C", "same_transaction", "B")),
        ("A", "B", "distinct", "-"),
        True,
        "alternate-path distinct contradiction",
    ),
    ProposalSpec(
        "VS",
        "AB",
        (),
        ("A", "B", "same_transaction", "A"),
        False,
        "valid pending-to-same decision",
    ),
    ProposalSpec(
        "BD",
        "ABC",
        (("A", "B", "same_transaction", "A"),
         ("B", "C", "same_transaction", "B")),
        ("B", "C", "distinct", "-"),
        False,
        "valid bridge distinct split",
    ),
    ProposalSpec(
        "KR",
        "ABC",
        (("A", "B", "same_transaction", "A"),
         ("B", "C", "same_transaction", "B")),
        ("A", "B", "same_transaction", "B"),
        False,
        "valid structural-keeper redecision",
    ),
    ProposalSpec(
        "LR",
        "AB",
        (("A", "B", "same_transaction", "A"),
         ("A", "B", "distinct", "-")),
        ("A", "B", "same_transaction", "A"),
        False,
        "valid latest-wins reversal",
    ),
)

SUPPORT_STATES = (
    SupportSpec("A", "active"),
    SupportSpec("P", "partial"),
    SupportSpec("I", "inactive"),
)

BOUNDARY_CASES = tuple(
    BoundaryCase(
        case_id=(
            f"{writer.writer_id}-{proposal.proposal_id}-{support.support_id}"
        ),
        writer=writer,
        proposal=proposal,
        support=support,
    )
    for writer in WRITERS
    for proposal in PROPOSALS
    for support in SUPPORT_STATES
)

UNREACHABLE_IDS = ("U01", "U02", "U03", "U04", "U05", "U06")


class DuplicateDecisionWriteBoundaryReviewTests(AnalysisStoreTestCase):
    def test_write_boundary_manifest_is_frozen_and_complete(self) -> None:
        self.assertEqual(len(WRITERS), 6)
        self.assertEqual(len(PROPOSALS), 8)
        self.assertEqual(len(SUPPORT_STATES), 3)
        self.assertEqual(len(BOUNDARY_CASES), 144)
        self.assertEqual(len({case.case_id for case in BOUNDARY_CASES}), 144)
        self.assertEqual(tuple(backend.__all__), (
            "AnalysisService",
            "CoreStore",
            "StatementImportService",
        ))
        self.assertIs(PackageAnalysisService, ModuleAnalysisService)
        self.assertIs(PackageCoreStore, ModuleCoreStore)
        self.assertIs(PackageCoreStore, AnalysisModuleCoreStore)
        self.assertIs(PackageCoreStore, ImportModuleCoreStore)

        document = MATRIX_DOCUMENT.read_text(encoding="utf-8")
        executable_section = document.split(
            "<!-- EXECUTABLE_CASE_IDS_START -->", 1
        )[1].split("<!-- EXECUTABLE_CASE_IDS_END -->", 1)[0]
        documented_case_ids = tuple(
            re.findall(
                r"`((?:SP|SM|CP|CM|CA|CT)-[A-Z]{2}-[API])`",
                executable_section,
            )
        )
        self.assertEqual(
            documented_case_ids,
            tuple(case.case_id for case in BOUNDARY_CASES),
        )

        unreachable_section = document.split(
            "<!-- UNREACHABLE_CASE_IDS_START -->", 1
        )[1].split("<!-- UNREACHABLE_CASE_IDS_END -->", 1)[0]
        self.assertEqual(
            tuple(re.findall(r"`(U\d{2})`", unreachable_section)),
            UNREACHABLE_IDS,
        )
        self.assertIn("Total inventory entries: **150**", document)
        self.assertIn("Executable paths: **144**", document)
        self.assertIn("Explicitly unreachable classes: **6**", document)

    def _run_boundary_case(self, case: BoundaryCase) -> None:
        self.identities: dict[str, str] = {}
        self.contents: dict[str, bytes] = {}
        self.runs: dict[str, list[str]] = {}
        self.occurrences: dict[str, list[str]] = {}

        for label in case.proposal.labels:
            self._import_identity(label, group="TARGET")
        self._import_identity("Z", group="ANCHOR")

        for decision in case.proposal.pre_decisions:
            self._set_up_decision(decision)

        history_before_support = self._decision_ids()
        counts_before_support = self.store.entity_counts()
        self._apply_support_state(case.proposal.labels, case.support.state)
        self.assertEqual(self._decision_ids(), history_before_support)
        self.assertEqual(self.store.entity_counts(), counts_before_support)
        self._assert_projection_and_traceability()

        counts_before = self.store.entity_counts()
        history_before = self._decision_ids()
        summary_before = self.analysis.get_month_summary("2026-06")
        candidates_before = self._candidate_signature()
        facts_before = self._fact_signature()
        supports_before = self._support_signature()
        provenance_before = self._provenance_signature()

        if case.proposal.expect_reject:
            with self.assertRaises(ValueError, msg=case.case_id):
                self._invoke_writer(case.writer, case.proposal.proposal)
            self.assertEqual(self.store.entity_counts(), counts_before)
            self.assertEqual(self._decision_ids(), history_before)
            self.assertEqual(
                self.analysis.get_month_summary("2026-06"),
                summary_before,
            )
            self.assertEqual(self._candidate_signature(), candidates_before)
        else:
            target_pair = self._pair(*case.proposal.proposal[:2])
            self._invoke_writer(case.writer, case.proposal.proposal)
            counts_after = self.store.entity_counts()
            expected_counts = dict(counts_before)
            expected_counts["duplicate_decisions"] += 1
            self.assertEqual(counts_after, expected_counts)
            history_after = self._decision_ids()
            self.assertEqual(
                history_after[target_pair][:-1],
                history_before[target_pair],
            )
            self.assertEqual(
                len(history_after[target_pair]),
                len(history_before[target_pair]) + 1,
            )
            for pair, decision_ids in history_before.items():
                if pair != target_pair:
                    self.assertEqual(history_after[pair], decision_ids)

        self.assertEqual(self._fact_signature(), facts_before)
        self.assertEqual(self._support_signature(), supports_before)
        self.assertEqual(self._provenance_signature(), provenance_before)
        self._assert_projection_and_traceability()
        self._exercise_exact_support_append(case.proposal.labels[0])

    def _import_identity(self, label: str, *, group: str) -> None:
        balance = ord(label) - ord("A")
        content = (
            "Date,Description,Debit,Credit,Balance\r\n"
            f"06/01/2026,WRITE BOUNDARY {group} COFFEE,4.50,,{balance}.00\r\n"
        ).encode("ascii")
        run_id = self.importer.import_bytes(
            content,
            filename=f"write-boundary-{label}.csv",
            source_type="csv",
        )
        occurrence = self.store.list_occurrences(run_id)[0]
        self.identities[label] = str(occurrence["identity_id"])
        self.contents[label] = content
        self.runs[label] = [run_id]
        self.occurrences[label] = [str(occurrence["occurrence_id"])]

    def _set_up_decision(self, decision: Decision) -> None:
        left, right, value, keeper = decision
        self.analysis.set_duplicate_decision(
            self._link_id(left, right),
            value,
            None if keeper == "-" else self.identities[keeper],
        )

    def _invoke_writer(self, writer: WriterSpec, decision: Decision) -> None:
        left, right, value, keeper = decision
        link_id = self._link_id(left, right)
        kept_identity_id = None if keeper == "-" else self.identities[keeper]
        if writer.writer_id == "SP":
            PackageAnalysisService.set_duplicate_decision(
                self.analysis,
                link_id,
                value,
                kept_identity_id,
            )
        elif writer.writer_id == "SM":
            ModuleAnalysisService.set_duplicate_decision(
                self.analysis,
                link_id,
                value,
                kept_identity_id,
            )
        elif writer.writer_id == "CP":
            PackageCoreStore.add_duplicate_decision(
                self.store,
                link_id,
                decision=value,
                kept_identity_id=kept_identity_id,
            )
        elif writer.writer_id == "CM":
            ModuleCoreStore.add_duplicate_decision(
                self.store,
                link_id,
                decision=value,
                kept_identity_id=kept_identity_id,
            )
        elif writer.writer_id == "CA":
            AnalysisModuleCoreStore.add_duplicate_decision(
                self.store,
                link_id,
                decision=value,
                kept_identity_id=kept_identity_id,
            )
        elif writer.writer_id == "CT":
            ImportModuleCoreStore.add_duplicate_decision(
                self.store,
                link_id,
                decision=value,
                kept_identity_id=kept_identity_id,
            )
        else:
            raise AssertionError(f"unknown writer: {writer.writer_id}")

    def _apply_support_state(self, labels: str, state: SupportState) -> None:
        if state == "active":
            return
        active_labels = set(labels[1:]) if state == "partial" else set()
        for label in labels:
            if label not in active_labels:
                self.store.undo_import_run(self.runs[label][0])

    def _exercise_exact_support_append(self, label: str) -> None:
        history_before = self._decision_ids()
        counts_before = self.store.entity_counts()
        provenance_before = self._provenance_signature()
        run_id = self.importer.import_bytes(
            self.contents[label],
            filename=f"write-boundary-restored-{label}.csv",
            source_type="csv",
        )
        occurrence = self.store.list_occurrences(run_id)[0]
        self.assertEqual(str(occurrence["identity_id"]), self.identities[label])
        self.runs[label].append(run_id)
        self.occurrences[label].append(str(occurrence["occurrence_id"]))
        self.assertEqual(self._decision_ids(), history_before)

        counts_after = self.store.entity_counts()
        expected_counts = dict(counts_before)
        expected_counts["import_runs"] += 1
        expected_counts["source_records"] += 1
        expected_counts["imported_occurrences"] += 1
        self.assertEqual(counts_after, expected_counts)
        provenance_after = self._provenance_signature()
        for occurrence_id, provenance in provenance_before.items():
            self.assertEqual(provenance_after[occurrence_id], provenance)
        self._assert_projection_and_traceability()

    def _assert_projection_and_traceability(self) -> None:
        candidates = self.analysis.list_duplicate_candidates()
        active_rows = self.store.list_effective_transactions()
        active_identity_ids = {
            str(row["identity_id"])
            for row in active_rows
        }

        adjacency: dict[str, set[str]] = {}
        excluded_by_edges: set[str] = set()
        for candidate in candidates:
            if candidate.effective_decision != "same_transaction":
                continue
            left = candidate.left_identity_id
            right = candidate.right_identity_id
            adjacency.setdefault(left, set()).add(right)
            adjacency.setdefault(right, set()).add(left)
            self.assertIn(candidate.kept_identity_id, {left, right})
            excluded_by_edges.add(
                right if candidate.kept_identity_id == left else left
            )

        expected_included = active_identity_ids - set(adjacency)
        visited: set[str] = set()
        for root in sorted(adjacency):
            if root in visited:
                continue
            component: set[str] = set()
            pending = [root]
            while pending:
                identity_id = pending.pop()
                if identity_id in component:
                    continue
                component.add(identity_id)
                pending.extend(adjacency[identity_id])
            visited.update(component)
            structural_keepers = component - excluded_by_edges
            self.assertEqual(len(structural_keepers), 1)
            structural_keeper = next(iter(structural_keepers))
            active_component = component & active_identity_ids
            if active_component:
                expected_included.add(
                    structural_keeper
                    if structural_keeper in active_component
                    else min(active_component)
                )

        summary = self.analysis.get_month_summary("2026-06")
        self.assertEqual(
            {transaction.identity_id for transaction in summary.transactions},
            active_identity_ids,
        )
        actual_included = {
            transaction.identity_id
            for transaction in summary.transactions
            if transaction.included
        }
        self.assertEqual(actual_included, expected_included)
        self.assertEqual(summary.transaction_count, len(expected_included))
        self.assertEqual(summary.spending_total_minor, 450 * len(expected_included))
        self.assertEqual(summary.credit_total_minor, 0)
        self.assertEqual(len(summary.category_breakdown), 1)
        self.assertEqual(
            set(summary.category_breakdown[0].contributing_identity_ids),
            expected_included,
        )
        for transaction in summary.transactions:
            self.assertEqual(
                transaction.inclusion_reason,
                (
                    "active_support"
                    if transaction.identity_id in expected_included
                    else "human_duplicate_same_transaction"
                ),
            )
            self.assertTrue(transaction.active_supports)
            for support in transaction.active_supports:
                self.assertTrue(support.run_id)
                self.assertTrue(support.source_fingerprint)
                self.assertTrue(support.source_record_id)
                self.assertTrue(support.source_locator)

        for candidate in candidates:
            self.assertEqual(
                candidate.left_included,
                candidate.left_identity_id in expected_included,
            )
            self.assertEqual(
                candidate.right_included,
                candidate.right_identity_id in expected_included,
            )

    def _link_id(self, left: str, right: str) -> str:
        expected = {self.identities[left], self.identities[right]}
        matches = [
            pair
            for pair in self.store.list_suspected_duplicate_pairs()
            if {str(pair["left_identity_id"]), str(pair["right_identity_id"])}
            == expected
        ]
        self.assertEqual(len(matches), 1, (left, right))
        return str(matches[0]["duplicate_link_id"])

    def _decision_ids(self) -> dict[tuple[str, str], tuple[str, ...]]:
        labels_by_id = {
            identity_id: label
            for label, identity_id in self.identities.items()
        }
        result: dict[tuple[str, str], tuple[str, ...]] = {}
        for pair in self.store.list_suspected_duplicate_pairs():
            left = labels_by_id[str(pair["left_identity_id"])]
            right = labels_by_id[str(pair["right_identity_id"])]
            link_id = str(pair["duplicate_link_id"])
            result[self._pair(left, right)] = tuple(
                str(row["decision_id"])
                for row in self.store.list_duplicate_decisions(link_id)
            )
        return result

    def _candidate_signature(self) -> tuple[tuple[object, ...], ...]:
        return tuple(
            (
                candidate.duplicate_link_id,
                candidate.effective_decision,
                candidate.effective_decision_id,
                candidate.kept_identity_id,
                candidate.left_included,
                candidate.right_included,
                tuple(decision.decision_id for decision in candidate.history),
            )
            for candidate in self.analysis.list_duplicate_candidates()
        )

    def _fact_signature(self) -> dict[str, tuple[object, ...]]:
        return {
            label: (
                row["identity_id"],
                row["transaction_date"],
                row["merchant"],
                row["amount_minor"],
                row["currency"],
            )
            for label, identity_id in self.identities.items()
            for row in (self.store.get_normalized_transaction(identity_id),)
        }

    def _support_signature(self) -> dict[str, tuple[tuple[object, ...], ...]]:
        return {
            str(row["identity_id"]): tuple(
                (
                    support["occurrence_id"],
                    support["run_id"],
                    support["source_fingerprint"],
                    support["source_record_id"],
                    support["source_locator"],
                )
                for support in row["active_supports"]
            )
            for row in self.store.list_effective_transactions()
        }

    def _provenance_signature(self) -> dict[str, dict[str, object]]:
        return {
            occurrence_id: self.store.get_statement_occurrence_provenance(
                occurrence_id
            )
            for occurrence_ids in self.occurrences.values()
            for occurrence_id in occurrence_ids
        }

    @staticmethod
    def _pair(left: str, right: str) -> tuple[str, str]:
        return tuple(sorted((left, right)))  # type: ignore[return-value]


def _make_boundary_test(case: BoundaryCase):
    def test(self: DuplicateDecisionWriteBoundaryReviewTests) -> None:
        self._run_boundary_case(case)

    test.__name__ = f"test_boundary_{case.case_id.lower().replace('-', '_')}"
    return test


for _case in BOUNDARY_CASES:
    setattr(
        DuplicateDecisionWriteBoundaryReviewTests,
        f"test_boundary_{_case.case_id.lower().replace('-', '_')}",
        _make_boundary_test(_case),
    )


if __name__ == "__main__":
    import unittest

    unittest.main()
