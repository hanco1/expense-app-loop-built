from __future__ import annotations

import re
from dataclasses import dataclass

from backend.analysis import AnalysisService
from tests.backend.statement_support import StatementStoreTestCase


Operation = tuple[str, ...]


@dataclass(frozen=True)
class MatrixCase:
    case_id: str
    topology: str
    support_state: str
    decision_state: str
    operation_family: str
    initial_labels: tuple[str, ...]
    pre_operations: tuple[Operation, ...]
    operation: Operation
    expected_active: tuple[str, ...]
    expected_post_state: str
    expect_reject: bool = False
    groups: tuple[tuple[str, str], ...] = ()


def _case(
    case_id: str,
    topology: str,
    support_state: str,
    decision_state: str,
    operation_family: str,
    initial_labels: str,
    pre_operations: tuple[Operation, ...],
    operation: Operation,
    expected_active: str,
    expected_post_state: str,
    *,
    expect_reject: bool = False,
    groups: tuple[tuple[str, str], ...] = (),
) -> MatrixCase:
    return MatrixCase(
        case_id=case_id,
        topology=topology,
        support_state=support_state,
        decision_state=decision_state,
        operation_family=operation_family,
        initial_labels=tuple(initial_labels),
        pre_operations=pre_operations,
        operation=operation,
        expected_active=tuple(expected_active),
        expected_post_state=expected_post_state,
        expect_reject=expect_reject,
        groups=groups,
    )


SAME_AB_A: Operation = ("decide", "A", "B", "same_transaction", "A")
SAME_AB_B: Operation = ("decide", "A", "B", "same_transaction", "B")
SAME_BC_B: Operation = ("decide", "B", "C", "same_transaction", "B")
SAME_BC_C: Operation = ("decide", "B", "C", "same_transaction", "C")
SAME_AC_A: Operation = ("decide", "A", "C", "same_transaction", "A")
SAME_AC_C: Operation = ("decide", "A", "C", "same_transaction", "C")
SAME_CD_C: Operation = ("decide", "C", "D", "same_transaction", "C")
SAME_CD_D: Operation = ("decide", "C", "D", "same_transaction", "D")
DISTINCT_AB: Operation = ("decide", "A", "B", "distinct", "-")
DISTINCT_BC: Operation = ("decide", "B", "C", "distinct", "-")
DISTINCT_AC: Operation = ("decide", "A", "C", "distinct", "-")


MATRIX_CASES: tuple[MatrixCase, ...] = (
    _case("P01", "isolated_pair", "all_active", "pending", "import_new_identity_or_link", "A", (), ("import", "B"), "AB", "pending pair includes A and B"),
    _case("P02", "isolated_pair", "keeper_inactive_one_active", "pending", "undo_final_support", "AB", (), ("undo", "A", "0"), "B", "pending B remains included"),
    _case("P03", "isolated_pair", "all_inactive", "pending", "undo_final_support", "AB", (("undo", "A", "0"),), ("undo", "B", "0"), "", "no active identity and no month"),
    _case("P04", "isolated_pair", "support_restored", "pending", "exact_reimport", "AB", (("undo", "A", "0"), ("undo", "B", "0")), ("reimport", "A"), "A", "restored pending A is included"),
    _case("P05", "isolated_pair", "multiple_supports_partial", "pending", "append_support", "AB", (), ("reimport", "A"), "AB", "pending A and B included; A has two supports"),
    _case("P06", "isolated_pair", "all_active", "same_transaction", "append_same", "AB", (), SAME_AB_A, "AB", "A is the sole representative"),
    _case("P07", "isolated_pair", "only_keeper_active", "same_transaction", "undo_final_support", "AB", (SAME_AB_A,), ("undo", "B", "0"), "A", "active keeper A remains included"),
    _case("P08", "isolated_pair", "keeper_inactive_one_active", "same_transaction", "undo_final_support", "AB", (SAME_AB_A,), ("undo", "A", "0"), "B", "B is the deterministic active fallback"),
    _case("P09", "isolated_pair", "support_restored", "same_transaction", "restore_keeper_support", "AB", (SAME_AB_A, ("undo", "A", "0")), ("reimport", "A"), "AB", "human keeper A resumes"),
    _case("P10", "isolated_pair", "multiple_supports_partial", "same_transaction", "undo_partial_support", "AB", (("reimport", "A"), SAME_AB_A), ("undo", "A", "0"), "AB", "A stays keeper with one support"),
    _case("P11", "isolated_pair", "multiple_supports_final", "same_transaction", "undo_final_support", "AB", (("reimport", "A"), SAME_AB_A, ("undo", "A", "0")), ("undo", "A", "1"), "B", "B becomes fallback after A final-support loss"),
    _case("P12", "isolated_pair", "all_inactive", "same_transaction", "undo_final_support", "AB", (SAME_AB_A, ("undo", "A", "0")), ("undo", "B", "0"), "", "zero active representatives"),
    _case("P13", "isolated_pair", "support_restored", "same_transaction", "exact_reimport", "AB", (SAME_AB_A, ("undo", "A", "0"), ("undo", "B", "0")), ("reimport", "B"), "B", "restored non-keeper B is fallback"),
    _case("P14", "component_split", "all_active", "latest_wins", "append_distinct", "AB", (SAME_AB_A,), DISTINCT_AB, "AB", "distinct splits pair and includes both"),
    _case("P15", "isolated_pair", "all_active", "latest_wins", "append_same", "AB", (DISTINCT_AB,), SAME_AB_A, "AB", "latest same rejoins pair with A representative"),
    _case("P16", "isolated_pair", "all_active", "keeper_change", "keeper_redecision", "AB", (SAME_AB_A,), SAME_AB_B, "AB", "latest keeper B is sole representative"),
    _case("P17", "isolated_pair", "all_active", "same_transaction", "append_support", "AB", (SAME_AB_A,), ("reimport", "B"), "AB", "extra non-keeper support does not change A"),
    _case("P18", "isolated_pair", "all_active", "same_transaction", "renamed_exact_reimport", "AB", (SAME_AB_A,), ("reimport", "A"), "AB", "renamed exact re-import keeps A and adds support"),

    _case("C01", "three_identity_chain", "all_active", "same_transaction", "append_same", "ABC", (SAME_AB_A,), SAME_BC_B, "ABC", "chain has sole structural keeper A"),
    _case("C02", "three_identity_chain", "all_active", "same_transaction", "append_same", "ABC", (SAME_AB_B,), SAME_BC_B, "ABC", "chain has sole structural keeper B"),
    _case("C03", "three_identity_chain", "all_active", "conflicting_multi_keeper", "append_same", "ABC", (SAME_AB_A,), SAME_BC_C, "ABC", "multi-keeper proposal rejected with no history", expect_reject=True),
    _case("C04", "three_identity_chain", "keeper_inactive_one_active", "same_transaction", "undo_final_support", "ABC", (SAME_AB_A, SAME_BC_B, ("undo", "C", "0")), ("undo", "A", "0"), "B", "B is sole active fallback"),
    _case("C05", "three_identity_chain", "keeper_inactive_multiple_active", "same_transaction", "undo_final_support", "ABC", (SAME_AB_A, SAME_BC_B), ("undo", "A", "0"), "BC", "min(identity_id of B,C) is sole fallback"),
    _case("C06", "three_identity_chain", "multiple_supports_partial", "same_transaction", "undo_partial_support", "ABC", (("reimport", "A"), SAME_AB_A, SAME_BC_B), ("undo", "A", "0"), "ABC", "A remains keeper after partial support loss"),
    _case("C07", "three_identity_chain", "multiple_supports_final", "same_transaction", "undo_final_support", "ABC", (("reimport", "A"), SAME_AB_A, SAME_BC_B, ("undo", "A", "0")), ("undo", "A", "1"), "BC", "min(identity_id of B,C) is sole fallback"),
    _case("C08", "three_identity_chain", "all_inactive", "same_transaction", "undo_final_support", "ABC", (SAME_AB_A, SAME_BC_B, ("undo", "A", "0"), ("undo", "B", "0")), ("undo", "C", "0"), "", "no active identity and no representative"),
    _case("C09", "three_identity_chain", "support_restored", "same_transaction", "restore_keeper_support", "ABC", (SAME_AB_A, SAME_BC_B, ("undo", "A", "0")), ("reimport", "A"), "ABC", "restored keeper A resumes"),
    _case("C10", "three_identity_chain", "all_active", "pending", "import_new_identity_or_link", "ABC", (SAME_AB_A, SAME_BC_B), ("import", "D"), "ABCD", "new pending D remains separate; representatives A and D"),
    _case("C11", "component_merge", "all_active", "same_transaction", "append_same", "ABCD", (SAME_AB_A, SAME_BC_B), ("decide", "A", "D", "same_transaction", "A"), "ABCD", "D merges under sole keeper A"),
    _case("C12", "component_split", "all_active", "latest_wins", "append_distinct", "ABC", (SAME_AB_A, SAME_BC_B), DISTINCT_BC, "ABC", "bridge split yields representatives A and C"),
    _case("C13", "component_merge", "all_active", "latest_wins", "append_same", "ABC", (SAME_AB_A, SAME_BC_B, DISTINCT_BC), SAME_BC_B, "ABC", "latest same rejoins split chain under A"),
    _case("C14", "three_identity_chain", "all_active", "keeper_change", "keeper_redecision", "ABC", (SAME_AB_A, SAME_BC_B), SAME_AB_B, "ABC", "keeper redecision makes B sole representative"),
    _case("C15", "three_identity_chain", "keeper_inactive_multiple_active", "same_transaction", "append_support", "ABC", (SAME_AB_A, SAME_BC_B, ("undo", "A", "0")), ("reimport", "B"), "BC", "support append preserves deterministic fallback"),

    _case("T01", "three_identity_triangle", "all_active", "same_transaction", "append_same", "ABC", (SAME_AB_A, SAME_AC_A), SAME_BC_B, "ABC", "triangle has sole structural keeper A"),
    _case("T02", "three_identity_triangle", "all_active", "conflicting_zero_keeper", "append_same", "ABC", (SAME_AB_A, SAME_BC_B), SAME_AC_C, "ABC", "cycle-closing zero-keeper proposal rejected", expect_reject=True),
    _case("T03", "three_identity_triangle", "keeper_inactive_multiple_active", "same_transaction", "undo_final_support", "ABC", (SAME_AB_A, SAME_AC_A, SAME_BC_B), ("undo", "A", "0"), "BC", "min(identity_id of B,C) is sole fallback"),
    _case("T04", "three_identity_triangle", "all_active", "conflicting_multi_keeper", "append_distinct", "ABC", (SAME_AB_A, SAME_AC_A, SAME_BC_B), DISTINCT_AB, "ABC", "non-bridge distinct contradiction rejected", expect_reject=True),
    _case("T05", "three_identity_triangle", "all_active", "keeper_change", "keeper_redecision", "ABC", (SAME_AB_A, SAME_AC_A, SAME_BC_B), SAME_AB_B, "ABC", "keeper redecision makes B sole representative"),
    _case("T06", "three_identity_triangle", "all_inactive", "same_transaction", "undo_final_support", "ABC", (SAME_AB_A, SAME_AC_A, SAME_BC_B, ("undo", "A", "0"), ("undo", "B", "0")), ("undo", "C", "0"), "", "no active identity and no representative"),
    _case("T07", "three_identity_triangle", "support_restored", "same_transaction", "restore_keeper_support", "ABC", (SAME_AB_A, SAME_AC_A, SAME_BC_B, ("undo", "A", "0")), ("reimport", "A"), "ABC", "restored keeper A resumes"),
    _case("T08", "three_identity_triangle", "multiple_supports_final", "same_transaction", "undo_final_support", "ABC", (("reimport", "A"), SAME_AB_A, SAME_AC_A, SAME_BC_B, ("undo", "A", "0")), ("undo", "A", "1"), "BC", "min(identity_id of B,C) is sole fallback"),

    _case("M01", "multiple_disconnected_components", "all_active", "same_transaction", "append_same", "ABCD", (SAME_AB_A,), SAME_CD_C, "ABCD", "pending cross-links do not merge; representatives A,C"),
    _case("M02", "component_merge", "all_active", "same_transaction", "append_same", "ABCD", (SAME_AB_A, SAME_CD_C), SAME_AC_A, "ABCD", "keeper-to-keeper merge yields sole A"),
    _case("M03", "component_merge", "all_active", "conflicting_multi_keeper", "append_same", "ABCD", (SAME_AB_A, SAME_CD_C), ("decide", "B", "D", "same_transaction", "B"), "ABCD", "non-keeper merge with two survivors rejected", expect_reject=True),
    _case("M04", "component_merge", "keeper_inactive_multiple_active", "same_transaction", "append_same", "ABCD", (SAME_AB_A, SAME_CD_C, ("undo", "A", "0"), ("undo", "B", "0")), ("decide", "A", "C", "same_transaction", "C"), "CD", "inactive component merges under active keeper C"),
    _case("M05", "component_split", "all_active", "latest_wins", "append_distinct", "ABCD", (SAME_AB_A, SAME_CD_C, SAME_AC_A), DISTINCT_AC, "ABCD", "bridge distinct restores two components A,C"),
    _case("M06", "component_merge", "all_active", "keeper_change", "keeper_redecision", "ABCD", (SAME_AB_A, SAME_CD_C, SAME_AC_A), SAME_AC_C, "ABCD", "merged component keeper changes from A to C"),
    _case("M07", "component_merge", "keeper_inactive_multiple_active", "same_transaction", "append_same", "ABCD", (SAME_AB_A, SAME_CD_C, ("undo", "A", "0")), ("decide", "A", "C", "same_transaction", "C"), "BCD", "merge selects active keeper C without reviving A"),

    _case("X01", "multiple_disconnected_components", "all_active", "same_transaction", "disconnected_operation", "ABCD", (SAME_AB_A,), SAME_CD_C, "ABCD", "representatives A,C in isolated groups", groups=(("A", "ONE"), ("B", "ONE"), ("C", "TWO"), ("D", "TWO"))),
    _case("X02", "multiple_disconnected_components", "keeper_inactive_multiple_active", "same_transaction", "disconnected_operation", "ABCD", (SAME_AB_A, SAME_CD_C), ("undo", "A", "0"), "BCD", "fallback B plus unaffected keeper C", groups=(("A", "ONE"), ("B", "ONE"), ("C", "TWO"), ("D", "TWO"))),
    _case("X03", "multiple_disconnected_components", "all_active", "keeper_change", "disconnected_operation", "ABCD", (SAME_AB_A, SAME_CD_C), SAME_CD_D, "ABCD", "A unaffected while second keeper changes to D", groups=(("A", "ONE"), ("B", "ONE"), ("C", "TWO"), ("D", "TWO"))),
    _case("X04", "multiple_disconnected_components", "multiple_supports_partial", "same_transaction", "disconnected_operation", "ABCD", (SAME_AB_A, SAME_CD_C), ("reimport", "B"), "ABCD", "extra B support leaves representatives A,C", groups=(("A", "ONE"), ("B", "ONE"), ("C", "TWO"), ("D", "TWO"))),
    _case("X05", "multiple_disconnected_components", "all_inactive", "same_transaction", "disconnected_operation", "ABCD", (SAME_AB_A, SAME_CD_C, ("undo", "A", "0")), ("undo", "B", "0"), "CD", "inactive first component has zero; second keeps C", groups=(("A", "ONE"), ("B", "ONE"), ("C", "TWO"), ("D", "TWO"))),
    _case("X06", "multiple_disconnected_components", "support_restored", "same_transaction", "disconnected_operation", "ABCD", (SAME_AB_A, SAME_CD_C, ("undo", "A", "0"), ("undo", "B", "0")), ("reimport", "A"), "ACD", "restored A plus unaffected C", groups=(("A", "ONE"), ("B", "ONE"), ("C", "TWO"), ("D", "TWO"))),
    _case("X07", "multiple_disconnected_components", "all_active", "pending", "disconnected_operation", "ACD", (SAME_CD_C,), ("import", "B"), "ABCD", "new pending A/B identities plus unaffected C", groups=(("A", "ONE"), ("B", "ONE"), ("C", "TWO"), ("D", "TWO"))),
)


IMPOSSIBLE_CASES: tuple[tuple[str, str], ...] = (
    ("I01", "pending or distinct edges do not form a same_transaction component"),
    ("I02", "an isolated pair cannot already have chain or triangle topology"),
    ("I03", "a triangle edge is not a bridge, so one distinct decision cannot split it"),
    ("I04", "components cannot merge through a pending edge; a same decision is required"),
    ("I05", "different normalized facts cannot receive an automatic suspected link"),
    ("I06", "partial support loss requires at least two active supports beforehand"),
    ("I07", "final support loss cannot leave that same identity active"),
    ("I08", "pending and latest-distinct states have no designated component keeper"),
    ("I09", "a distinct decision cannot carry a kept_identity_id"),
    ("I10", "a rejected human decision cannot append a history row"),
    ("I11", "an exact re-import cannot create a new stable identity"),
    ("I12", "renaming an exact re-import cannot change its content fingerprint"),
    ("I13", "one import cannot be both a new-source identity and an exact re-import"),
    ("I14", "undo cannot create support, duplicate links, or human decisions"),
    ("I15", "support restoration cannot append or rewrite decision history"),
    ("I16", "an operation on a normalized-disconnected component cannot merge another"),
    ("I17", "an all-inactive component cannot have an included representative"),
    ("I18", "an active committed same component with zero or multiple representatives is invalid"),
    ("I19", "cycle closing is impossible on a pair; it requires an alternate same path"),
    ("I20", "different-source identities cannot share one occurrence support row"),
)


class ComponentStateMatrixTests(StatementStoreTestCase):
    maxDiff = None

    def setUp(self) -> None:
        super().setUp()
        self.analysis = AnalysisService(self.store)
        self.ids: dict[str, str] = {}
        self.contents: dict[str, bytes] = {}
        self.runs: dict[str, list[str]] = {}
        self.run_active: dict[str, bool] = {}
        self.groups: dict[str, str] = {}
        self.model_history: dict[
            tuple[str, str], list[tuple[str, str | None]]
        ] = {}

    def test_matrix_manifest_is_frozen_and_complete(self) -> None:
        self.assertEqual(len(MATRIX_CASES), 55)
        self.assertEqual(len(IMPOSSIBLE_CASES), 20)
        ids = [case.case_id for case in MATRIX_CASES]
        impossible_ids = [case_id for case_id, _ in IMPOSSIBLE_CASES]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(impossible_ids), len(set(impossible_ids)))
        self.assertEqual(
            {case.topology for case in MATRIX_CASES},
            {
                "isolated_pair",
                "three_identity_chain",
                "three_identity_triangle",
                "component_merge",
                "component_split",
                "multiple_disconnected_components",
            },
        )
        self.assertTrue(
            {
                "all_active",
                "only_keeper_active",
                "keeper_inactive_one_active",
                "keeper_inactive_multiple_active",
                "multiple_supports_partial",
                "multiple_supports_final",
                "all_inactive",
                "support_restored",
            }
            <= {case.support_state for case in MATRIX_CASES}
        )
        self.assertTrue(
            {
                "pending",
                "same_transaction",
                "latest_wins",
                "keeper_change",
                "conflicting_multi_keeper",
                "conflicting_zero_keeper",
            }
            <= {case.decision_state for case in MATRIX_CASES}
        )
        self.assertTrue(
            {
                "import_new_identity_or_link",
                "append_support",
                "append_same",
                "append_distinct",
                "keeper_redecision",
                "undo_partial_support",
                "undo_final_support",
                "exact_reimport",
                "renamed_exact_reimport",
                "restore_keeper_support",
                "disconnected_operation",
            }
            <= {case.operation_family for case in MATRIX_CASES}
        )

    def _run_matrix_case(self, case: MatrixCase) -> None:
        self.groups = dict(case.groups)
        for label in case.initial_labels:
            self._import_label(label)
        for operation in case.pre_operations:
            self._apply_operation(operation)

        histories_before = self._history_ids()
        counts_before = self.store.entity_counts()
        import_link_delta = 0
        if case.operation[0] == "import":
            label = case.operation[1]
            group = self.groups.get(label, "ONE")
            import_link_delta = sum(
                self.groups.get(existing, "ONE") == group
                for existing in self.ids
            )

        self._apply_operation(case.operation, expect_reject=case.expect_reject)
        histories_after = self._history_ids()
        counts_after = self.store.entity_counts()
        self._assert_history_transition(
            case,
            histories_before,
            histories_after,
        )
        self._assert_entity_transition(
            case,
            counts_before,
            counts_after,
            import_link_delta,
        )

        expected_active_labels = set(case.expected_active)
        active_rows = self.store.list_effective_transactions()
        active_ids = {str(row["identity_id"]) for row in active_rows}
        self.assertEqual(
            active_ids,
            {self.ids[label] for label in expected_active_labels},
            case.case_id,
        )
        expected_included_labels, same_component_labels = self._model_projection(
            expected_active_labels
        )
        expected_included_ids = {
            self.ids[label] for label in expected_included_labels
        }

        if not expected_included_ids:
            self.assertEqual(self.analysis.list_months(), (), case.case_id)
        else:
            self.assertEqual(
                self.analysis.list_months(),
                ("2026-06",),
                case.case_id,
            )
            summary = self.analysis.get_month_summary("2026-06")
            self.assertEqual(summary.transaction_count, len(expected_included_ids))
            self.assertEqual(
                summary.spending_transaction_count,
                len(expected_included_ids),
            )
            self.assertEqual(summary.credit_transaction_count, 0)
            self.assertEqual(
                summary.spending_total_minor,
                450 * len(expected_included_ids),
            )
            self.assertEqual(summary.credit_total_minor, 0)
            self.assertEqual(
                {transaction.identity_id for transaction in summary.transactions},
                active_ids,
            )
            included_ids = {
                transaction.identity_id
                for transaction in summary.transactions
                if transaction.included
            }
            self.assertEqual(included_ids, expected_included_ids, case.case_id)
            self.assertEqual(len(summary.category_breakdown), 1)
            bucket = summary.category_breakdown[0]
            self.assertEqual(bucket.category, "Dining")
            self.assertEqual(bucket.spending_minor, 450 * len(expected_included_ids))
            self.assertEqual(bucket.transaction_count, len(expected_included_ids))
            self.assertEqual(
                bucket.contributing_identity_ids,
                tuple(sorted(expected_included_ids)),
            )
            labels_by_id = {identity_id: label for label, identity_id in self.ids.items()}
            for transaction in summary.transactions:
                label = labels_by_id[transaction.identity_id]
                self.assertEqual(transaction.amount_minor, -450)
                self.assertEqual(transaction.currency, "CAD")
                self.assertEqual(transaction.effective_category, "Dining")
                self.assertEqual(transaction.category_rule_version, "mvp-1")
                self.assertEqual(
                    transaction.inclusion_reason,
                    (
                        "active_support"
                        if transaction.identity_id in expected_included_ids
                        else "human_duplicate_same_transaction"
                    ),
                )
                if label in same_component_labels:
                    self.assertEqual(transaction.duplicate_decision, "same_transaction")
                    self.assertTrue(transaction.duplicate_link_ids)
                expected_support_run_ids = {
                    run_id
                    for run_id in self.runs[label]
                    if self.run_active[run_id]
                }
                self.assertEqual(
                    {support.run_id for support in transaction.active_supports},
                    expected_support_run_ids,
                )
                self.assertTrue(
                    all(
                        support.source_locator
                        and support.source_record_id
                        and support.source_fingerprint
                        for support in transaction.active_supports
                    )
                )

        for candidate in self.analysis.list_duplicate_candidates():
            self.assertEqual(
                candidate.left_included,
                candidate.left_identity_id in expected_included_ids,
                case.case_id,
            )
            self.assertEqual(
                candidate.right_included,
                candidate.right_identity_id in expected_included_ids,
                case.case_id,
            )
        self.assertEqual(counts_after["transaction_identities"], len(self.ids))
        self.assertEqual(counts_after["normalized_transactions"], len(self.ids))

    def _import_label(self, label: str) -> None:
        group = self.groups.get(label, "ONE")
        merchant = f"MATRIX {group} COFFEE"
        balance = ord(label) - ord("A")
        content = (
            "Date,Description,Debit,Credit,Balance\r\n"
            f"06/01/2026,{merchant},4.50,,{balance}.00\r\n"
        ).encode("ascii")
        run_id = self.importer.import_bytes(
            content,
            filename=f"matrix-{label}.csv",
            source_type="csv",
        )
        occurrence = self.store.list_occurrences(run_id)[0]
        identity_id = str(occurrence["identity_id"])
        self.contents[label] = content
        self.ids[label] = identity_id
        self.runs[label] = [run_id]
        self.run_active[run_id] = True

    def _apply_operation(
        self,
        operation: Operation,
        *,
        expect_reject: bool = False,
    ) -> None:
        kind = operation[0]
        if kind == "import":
            self._import_label(operation[1])
            return
        if kind == "reimport":
            label = operation[1]
            run_id = self.importer.import_bytes(
                self.contents[label],
                filename=f"renamed-{label}-{len(self.runs[label])}.csv",
                source_type="csv",
            )
            occurrence = self.store.list_occurrences(run_id)[0]
            self.assertEqual(str(occurrence["identity_id"]), self.ids[label])
            self.runs[label].append(run_id)
            self.run_active[run_id] = True
            return
        if kind == "undo":
            label = operation[1]
            run_id = self.runs[label][int(operation[2])]
            self.store.undo_import_run(run_id)
            self.run_active[run_id] = False
            return
        if kind != "decide":
            raise AssertionError(f"unknown matrix operation: {operation}")

        left, right, decision, keeper = operation[1:]
        candidate = self._candidate(left, right)
        kept_identity_id = None if keeper == "-" else self.ids[keeper]
        if expect_reject:
            with self.assertRaises(ValueError):
                self.analysis.set_duplicate_decision(
                    candidate.duplicate_link_id,
                    decision,
                    kept_identity_id,
                )
            return
        self.analysis.set_duplicate_decision(
            candidate.duplicate_link_id,
            decision,
            kept_identity_id,
        )
        pair = self._pair(left, right)
        self.model_history.setdefault(pair, []).append(
            (decision, None if keeper == "-" else keeper)
        )

    def _candidate(self, left: str, right: str):
        expected = {self.ids[left], self.ids[right]}
        matches = [
            candidate
            for candidate in self.analysis.list_duplicate_candidates()
            if {candidate.left_identity_id, candidate.right_identity_id} == expected
        ]
        self.assertEqual(len(matches), 1, (left, right))
        return matches[0]

    @staticmethod
    def _pair(left: str, right: str) -> tuple[str, str]:
        return tuple(sorted((left, right)))  # type: ignore[return-value]

    def _history_ids(self) -> dict[tuple[str, str], tuple[str, ...]]:
        labels_by_id = {identity_id: label for label, identity_id in self.ids.items()}
        histories: dict[tuple[str, str], tuple[str, ...]] = {}
        for candidate in self.analysis.list_duplicate_candidates():
            pair = self._pair(
                labels_by_id[candidate.left_identity_id],
                labels_by_id[candidate.right_identity_id],
            )
            histories[pair] = tuple(decision.decision_id for decision in candidate.history)
        return histories

    def _assert_history_transition(
        self,
        case: MatrixCase,
        before: dict[tuple[str, str], tuple[str, ...]],
        after: dict[tuple[str, str], tuple[str, ...]],
    ) -> None:
        kind = case.operation[0]
        if kind == "decide" and not case.expect_reject:
            target = self._pair(case.operation[1], case.operation[2])
            self.assertEqual(after[target][:-1], before[target])
            self.assertEqual(len(after[target]), len(before[target]) + 1)
            for pair, history in before.items():
                if pair != target:
                    self.assertEqual(after[pair], history)
            return
        for pair, history in before.items():
            self.assertEqual(after[pair], history, case.case_id)
        if kind == "import":
            for pair in set(after) - set(before):
                self.assertEqual(after[pair], ())

    def _assert_entity_transition(
        self,
        case: MatrixCase,
        before: dict[str, int],
        after: dict[str, int],
        import_link_delta: int,
    ) -> None:
        kind = case.operation[0]
        expected = dict(before)
        if kind == "decide" and not case.expect_reject:
            expected["duplicate_decisions"] += 1
        elif kind == "reimport":
            expected["import_runs"] += 1
            expected["source_records"] += 1
            expected["imported_occurrences"] += 1
        elif kind == "import":
            expected["import_runs"] += 1
            expected["source_records"] += 1
            expected["transaction_identities"] += 1
            expected["normalized_transactions"] += 1
            expected["imported_occurrences"] += 1
            expected["duplicate_links"] += import_link_delta
        self.assertEqual(after, expected, case.case_id)

    def _model_projection(
        self,
        active_labels: set[str],
    ) -> tuple[set[str], set[str]]:
        parent = {label: label for label in self.ids}

        def find(label: str) -> str:
            while parent[label] != label:
                parent[label] = parent[parent[label]]
                label = parent[label]
            return label

        def union(left: str, right: str) -> None:
            left_root = find(left)
            right_root = find(right)
            if left_root != right_root:
                parent[right_root] = left_root

        effective_same: list[tuple[str, str, str]] = []
        for (left, right), history in self.model_history.items():
            decision, keeper = history[-1]
            if decision == "same_transaction":
                assert keeper is not None
                union(left, right)
                effective_same.append((left, right, keeper))

        components: dict[str, set[str]] = {}
        for label in self.ids:
            components.setdefault(find(label), set()).add(label)
        same_component_labels = {
            label
            for left, right, _ in effective_same
            for label in (left, right)
        }
        expected_included: set[str] = set()
        for component in components.values():
            active_component = component & active_labels
            if not active_component:
                continue
            component_edges = [
                edge
                for edge in effective_same
                if edge[0] in component and edge[1] in component
            ]
            if not component_edges:
                expected_included.update(active_component)
                continue
            excluded = {
                right if keeper == left else left
                for left, right, keeper in component_edges
            }
            structural_keepers = component - excluded
            self.assertEqual(
                len(structural_keepers),
                1,
                f"model state must have one structural keeper: {component_edges}",
            )
            preferred = next(iter(structural_keepers))
            if preferred in active_component:
                expected_included.add(preferred)
            else:
                expected_included.add(
                    min(active_component, key=lambda label: self.ids[label])
                )
        return expected_included, same_component_labels


def _make_matrix_test(case: MatrixCase):
    def test(self: ComponentStateMatrixTests) -> None:
        self._run_matrix_case(case)

    slug = re.sub(r"[^a-z0-9]+", "_", case.expected_post_state.lower()).strip("_")
    test.__name__ = f"test_matrix_{case.case_id.lower()}_{slug}"
    test.__qualname__ = f"ComponentStateMatrixTests.{test.__name__}"
    return test


for _matrix_case in MATRIX_CASES:
    setattr(
        ComponentStateMatrixTests,
        _make_matrix_test(_matrix_case).__name__,
        _make_matrix_test(_matrix_case),
    )


if __name__ == "__main__":
    import unittest

    unittest.main()
