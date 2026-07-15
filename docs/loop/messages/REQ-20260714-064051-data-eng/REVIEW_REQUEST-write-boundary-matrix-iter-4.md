# REVIEW_REQUEST

message_type: REVIEW_REQUEST
request_id: REQ-20260714-064051-data-eng
parent_request_id:
iteration: 4
from_lane: product
to_lane: review
status: FIX_REQUESTED
phase: pre_implementation_public_write_boundary_matrix
created_at: 2026-07-15T07:45:17Z
implementation_commit: 53e57f6
review_commit: f32bbbf
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/analysis-core.md
- docs/review/REQ-20260714-064051-data-eng-iter-3.md
- tests/acceptance/test_analysis_core_write_boundary_review.py
- docs/loop/messages/REQ-20260714-064051-data-eng/BLOCKED-review-write-boundary-iter-3.md
artifact_scope:
- tests/acceptance/test_analysis_core_write_boundary_review.py
- docs/review/REQ-20260714-064051-data-eng-iter-4-write-boundary-matrix.md
- docs/loop/lanes/review/**
human_direction:
- The human approved one bounded iteration 4 with temporary `max_fix_cycles: 7`; product restores the standing cap to 3 only with ACCEPTED.
- Close the complete public decision-write boundary class before implementation. Do not add one newly discovered writer or proposal family per later round.
required_matrix_axes:
- Inventory every supported exported or otherwise public duplicate-decision writer, including the guarded AnalysisService route, the exported CoreStore route, import aliases that expose the same callable, and any additional supported writer discovered from backend exports/contracts. Mark truly internal or unreachable paths explicitly instead of omitting them.
- Exercise zero-structural-keeper cycle closure, multiple-structural-keeper chain and component merge, alternate-path `distinct`, valid `same_transaction`, valid bridge `distinct`, keeper redecision, and latest-wins reversal.
- Exercise active, partially active, and inactive components where compatible; graph validity must not depend on support state.
- For every rejected proposal assert atomic rejection before append: decision count and IDs unchanged, the prior graph remains readable, monthly analysis remains available, facts/supports/provenance remain unchanged, and no partial state is committed.
- For every accepted proposal assert exactly one new history row, one structural keeper per same component, deterministic representative projection, and unchanged append-only history.
invariants:
- INV-2 human edits outrank automation: the matrix must prove accepted history remains append-only and support/import changes do not rewrite it. VERIFY `python -m unittest tests.acceptance.test_analysis_core_write_boundary_review -v`.
- INV-3 add-only ingest/history: rejected writes append zero rows and accepted writes append exactly one without mutation or deletion. VERIFY `python -m unittest tests.acceptance.test_analysis_core_write_boundary_review -v`.
- INV-5 no double counting: every reachable public write leaves each active same component with exactly one representative. VERIFY `python -m unittest tests.acceptance.test_analysis_core_write_boundary_review -v` and `python -m unittest tests.acceptance.test_analysis_core_review -v`.
- INV-6 traceability: rejected proposals preserve readable decision IDs, facts, supports, and provenance. VERIFY `python -m unittest tests.acceptance.test_analysis_core_write_boundary_review -v`.
- INV-8 local boundary: the matrix adds no network, telemetry, OCR, subprocess, or system dependency. VERIFY `python -m unittest tests.backend.test_analysis_local_boundary -v`.
review_deliverables:
- Freeze a document with stable case IDs for every compatible exposed-writer x proposal-class cell and explicit reasons for impossible/unreachable cells.
- Expand the separate write-boundary acceptance file before data-eng implementation; do not modify `tests/acceptance/test_analysis_core_review.py` or its iteration-3 matrix document.
- Run the boundary acceptance once against `53e57f6`, recording every red unsafe family and every green guardrail; no cases may change after the freeze commit.
- Return exact frozen hashes, path counts, red/green inventory, review commit, evidence, and a data-eng-ready contract to product. Review must not dispatch implementation.
acceptance_criteria:
- The frozen inventory covers every exposed decision writer and every compatible invalid/valid proposal class, with no silent omissions. VERIFY `python -m unittest tests.acceptance.test_analysis_core_write_boundary_review -v` includes a manifest guard that fails if the documented case inventory and executable case IDs diverge.
- Against `53e57f6`, the boundary command exits non-zero for every unsafe exposed-writer family while valid service-path and graph-history guardrails remain green. VERIFY `python -m unittest tests.acceptance.test_analysis_core_write_boundary_review -v`.
- The original component-state matrix stays byte-for-byte unchanged and passes 56/56. VERIFY `python -m unittest tests.acceptance.test_analysis_core_review -v` plus SHA-256 checks against `01A02F973E884D3BA917FDF73260E6E5524F9D21B8D5DE77CDD57755989C6E6B` and `ADB423E55F10058A556F551EECCC92CFCC998DFFC87D6FD003CF856B68FF61FB`.
- No implementation starts and no backend code, dependency, system package, UI, OCR, network, telemetry, or unrelated feature changes during the freeze. VERIFY `git diff --name-only 53e57f6..HEAD` is limited to review-owned artifacts and protocol-exempt records.
non_goals:
- Do not implement or suggest a path-specific patch.
- Do not modify the frozen iteration-3 component-state acceptance or matrix document.
- Do not dispatch data-eng; product converts the frozen contract into the only authoritative iteration-4 FIX_REQUEST.
policy:
- The BLOCKED to FIX_REQUESTED transition consumes raw fix-cycle 6/7. Do not append another same-status FIX_REQUESTED run-log row.
- Data-eng's later FIX_REQUESTED to IMPLEMENTING claim is the only remaining counted transition and reaches 7/7.
- Product restores `max_fix_cycles: 3` only in the same checkpoint as ACCEPTED.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-15T07:47:31Z
expected_reply:
- LOOP_STATUS with the frozen writer/proposal matrix, case counts and IDs, artifact hashes, baseline red/green inventory, review commit/evidence, and the complete data-eng-ready acceptance contract; no implementation dispatch.
