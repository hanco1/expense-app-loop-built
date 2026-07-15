# FIX_REQUEST

message_type: FIX_REQUEST
request_id: REQ-20260714-064051-data-eng
parent_request_id:
iteration: 4
from_lane: product
to_lane: data-eng
status: FIX_REQUESTED
created_at: 2026-07-15T07:58:28Z
implementation_commit: 53e57f6
freeze_commit: 7a99866
review_evidence_commit: 8c0c886
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/analysis-core.md
- docs/review/REQ-20260714-064051-data-eng-iter-3-component-state-matrix.md
- tests/acceptance/test_analysis_core_review.py
- docs/review/REQ-20260714-064051-data-eng-iter-4-write-boundary-matrix.md
- tests/acceptance/test_analysis_core_write_boundary_review.py
- docs/loop/lanes/review/evidence/REQ-20260714-064051-data-eng-iter-4-write-boundary-matrix.json
artifact_scope:
- backend/analysis.py
- backend/persistence.py
- tests/backend/test_analysis_duplicates.py
- tests/backend/test_analysis_inclusion.py
- docs/data/analysis-core.md
- docs/loop/lanes/data-eng/**
frozen_artifacts:
- path: tests/acceptance/test_analysis_core_review.py
  sha256: 01A02F973E884D3BA917FDF73260E6E5524F9D21B8D5DE77CDD57755989C6E6B
- path: docs/review/REQ-20260714-064051-data-eng-iter-3-component-state-matrix.md
  sha256: ADB423E55F10058A556F551EECCC92CFCC998DFFC87D6FD003CF856B68FF61FB
- path: tests/acceptance/test_analysis_core_write_boundary_review.py
  sha256: 974432935CBB3C8EB957297DA50E3FD52E1F877D1C5D9C3BBAFD4D16818D809B
- path: docs/review/REQ-20260714-064051-data-eng-iter-4-write-boundary-matrix.md
  sha256: 91B1DFD3792A04DBD42E2847544896EB239594C7D9F7C2BAEAC1E4A26FCD421C
frozen_inventory:
- writers: 6
- proposal_classes: 8
- support_states: 3
- executable_paths: 144
- unreachable_classes: 6
- total_entries: 150
- consolidated_unittest_count: 145
writers:
- SP: backend.AnalysisService
- SM: backend.analysis.AnalysisService
- CP: backend.CoreStore
- CM: backend.persistence.CoreStore
- CA: backend.analysis.CoreStore
- CT: backend.statement_import.CoreStore
proposal_classes:
- ZK: zero structural keeper
- MC: multiple structural keepers in a chain
- MM: multiple structural keepers after component merge
- AD: alternate-path distinct contradiction
- VS: valid same_transaction
- BD: valid bridge distinct
- KR: valid keeper redecision
- LR: valid latest-wins reversal
support_states:
- A: all target identities active
- P: first target identity inactive and remaining identities active
- I: target component fully inactive with a disconnected active monthly anchor
baseline:
- command: python -m unittest tests.acceptance.test_analysis_core_write_boundary_review -v
- exit_code: 1
- result: 145 tests; 48 red paths, 96 green compatible guardrails, manifest guard green, no errors.
- red_inventory: every CP|CM|CA|CT x ZK|MC|MM|AD x A|P|I case.
- green_inventory: every SP|SM case plus every CP|CM|CA|CT x VS|BD|KR|LR x A|P|I case.
requested_fix:
- Put one centralized latest-same graph proposal validator at the underlying duplicate-decision write boundary. Every supported `CoreStore.add_duplicate_decision` import alias must enforce the identical rule atomically; do not add alias-specific or proposal-specific patches.
- Before appending a decision, project the latest effective graph and reject ZK, MC, MM, and AD proposals independent of active support state. Rejection must happen before any decision ID or history row is committed.
- Preserve the already-correct `AnalysisService` behavior and retain valid VS, BD, KR, and LR writes through all six public import paths. Each accepted proposal appends exactly one target history row, preserves all prior IDs, and leaves exactly one structural keeper per same component.
- Every rejected proposal must leave entity counts, all decision IDs, the readable prior graph, monthly analysis, normalized facts, active supports, and structured provenance equivalent to the pre-call state.
- Active projection remains the structural keeper when active, otherwise the lexicographically smallest active stable identity fallback; inactive components include zero. Support loss, undo, support append, and exact/renamed re-import must not rewrite human decision history.
- Add backend regressions for the centralized write boundary and the invalid/valid proposal families. Do not modify any of the four frozen artifacts or their case IDs.
acceptance_criteria:
- The unchanged iteration-4 boundary command passes all 145 tests: all 144 executable paths and the manifest guard are green; all six unreachable classes remain unchanged.
- All four frozen artifact SHA-256 values match exactly before and after implementation.
- All 48 previously red CoreStore-alias invalid-proposal paths reject atomically with zero appended rows; all 96 previously green compatible paths remain green.
- The unchanged iteration-3 component-state command remains 56/56, and every original C1-C7 focused command, full backend discovery, privacy/local boundary, and completion gate remain green.
- No dependency, system package, OCR, network, telemetry, subprocess, UI, or unrelated feature is added.
verification:
- python -m unittest tests.acceptance.test_analysis_core_write_boundary_review -v
- python -m unittest tests.acceptance.test_analysis_core_review -v
- python -m unittest tests.backend.test_analysis_categories -v
- python -m unittest tests.backend.test_analysis_corrections -v
- python -m unittest tests.backend.test_analysis_duplicates -v
- python -m unittest tests.backend.test_analysis_monthly -v
- python -m unittest tests.backend.test_analysis_inclusion -v
- python -m unittest tests.backend.test_analysis_contracts -v
- python -m unittest tests.backend.test_analysis_local_boundary -v
- python -m unittest discover -s tests/backend -p "test_*.py" -v
- python completion_gate.py --loop-dir docs/loop --request-id REQ-20260714-064051-data-eng
policy:
- The human approved temporary `max_fix_cycles: 7` for iteration 4. Do not append a same-status `FIX_REQUESTED` run-log row.
- Data-eng's claim must be the single `FIX_REQUESTED -> IMPLEMENTING` transition, reaching raw 7/7.
- Product restores `max_fix_cycles: 3` only in the same checkpoint as ACCEPTED.
- No system dependency, OCR engine, network path, UI work, or scope expansion is authorized.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: pending
- sent_at:
expected_reply:
- IMPLEMENTATION_DONE iteration 4 with the centralized underlying write-boundary design, implementation commit, changed files, unchanged four hashes, all eleven command exits, flat evidence paths, and no scope or dependency expansion.
