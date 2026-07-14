# FIX_REQUEST

message_type: FIX_REQUEST
request_id: REQ-20260714-064051-data-eng
parent_request_id:
iteration: 3
from_lane: product
to_lane: data-eng
status: FIX_REQUESTED
created_at: 2026-07-14T18:10:54Z
implementation_commit: 6b9378f
freeze_commit: 6fdc57d
review_evidence_commit: 7ab8341
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/analysis-core.md
- docs/review/REQ-20260714-064051-data-eng-iter-3-component-state-matrix.md
- tests/acceptance/test_analysis_core_review.py
- docs/loop/lanes/review/evidence/REQ-20260714-064051-data-eng-iter-3-component-state-matrix.json
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
frozen_matrix:
- total_entries: 75
- compatible_executable_paths: 55
- impossible_or_invalid_classes: 20
- consolidated_unittest_count: 56
baseline:
- command: python -m unittest tests.acceptance.test_analysis_core_review -v
- exit_code: 1
- result: 56 tests, 13 failures, 0 errors; 13 red compatible paths, 42 green compatible guardrails, manifest guard green.
- red_path_ids: P08, P11, P13, C03, C04, C05, C07, C15, T03, T04, T08, M03, X02
failed_operation_families:
- Keeper final-support loss or fallback: P08, P11, C04, C05, C07, T03, T08, X02.
- Non-keeper-only restore: P13.
- Support append while fallback is active: C15.
- Multi-keeper same or component-merge proposals: C03, M03.
- Non-bridge distinct contradiction: T04.
requested_fix:
- Implement one centralized component projection and proposal-validation rule used across decision append, suspected-link creation/acceptance, import/support append, human same/distinct/keeper redecision, per-run undo/final-support loss, exact and renamed re-import, support restore, component merge/split, and disconnected-component operations. Scattered operation-specific patches do not satisfy this request.
- Effective latest `same_transaction` edges, and only those edges, form components. Pending and latest `distinct` links do not connect components.
- Every committed same component has exactly one structural keeper. Before appending a human decision, reject any proposal that would leave zero or multiple structural keepers, and reject a `distinct` proposal whose endpoints remain same-connected through an alternate path. A rejected proposal appends no history row.
- For each component with active identities, include exactly one representative: the structural keeper when it is active, otherwise the active identity with lexicographically smallest stable `identity_id`. Include zero when no identity is active. When structural-keeper support returns, it resumes automatically.
- Support/fallback changes must not append, mutate, or delete human decisions. Accepted human redecisions append exactly one history row. Retained facts, run/source provenance, audit inclusion reasons, exact month/category totals, and disconnected-component isolation must remain intact.
- Add backend regressions that exercise the centralized rule across all five red operation families. Do not modify either frozen artifact or any case ID.
acceptance_criteria:
- The unchanged frozen acceptance command passes all 56 tests: all 55 executable paths and the manifest guard are green, and the 20 impossible/invalid classes remain unchanged.
- Both frozen artifact SHA-256 values match exactly before and after implementation.
- Every active same component has exactly one included active representative; every inactive component has zero. Human keeper preference, deterministic fallback, and keeper restoration hold for every compatible state-changing path.
- All 42 previously green compatible guardrails remain green; no decision-history, retained-fact, exact-money, aggregation, provenance, privacy, or component-isolation regression is introduced.
- Original C1-C7 focused commands and full backend discovery remain green; completion gate returns `SHIP_CHECK_OK`.
verification:
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
- The human approved temporary `max_fix_cycles: 5` for this iteration. Do not add a same-status `FIX_REQUESTED` run-log row.
- Data-eng's claim must be the single `FIX_REQUESTED -> IMPLEMENTING` transition, reaching raw 5/5.
- Product restores `max_fix_cycles: 3` only in the same checkpoint as ACCEPTED.
- No system dependency, OCR engine, network path, UI work, or unrelated feature is authorized.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-14T18:12:05Z
expected_reply:
- IMPLEMENTATION_DONE iteration 3 with the centralized component-state design, implementation commit, changed files, unchanged frozen hashes, all ten command exits, flat evidence paths, and no scope or dependency expansion.
