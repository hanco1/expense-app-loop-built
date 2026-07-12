# FIX_REQUEST

message_type: FIX_REQUEST
request_id: REQ-20260712-200417-data-eng
parent_request_id:
iteration: 2
from_lane: review
to_lane: data-eng
status: FIX_REQUESTED
created_at: 2026-07-12T20:16:03Z
implementation_commit: 8eb5b31
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/core-foundation.md
- docs/loop/messages/REQ-20260712-200417-data-eng/IMPLEMENTATION_REQUEST-iter-1.md
- docs/loop/messages/REQ-20260712-200417-data-eng/IMPLEMENTATION_DONE-iter-1.md
- docs/review/REQ-20260712-200417-data-eng-iter-1.md
artifact_scope:
- backend/persistence.py
- tests/backend/test_import_runs.py
- tests/acceptance/test_core_foundation_review.py
acceptance_criteria:
- Undo is state-based and atomic: every occurrence from the selected run becomes excluded without deleting the run, source records, identities, or manual-correction history; re-import links the stable identity to preserved corrections.
failed_criteria:
- Atomic run undo is incomplete: an already-undone run accepts a new source record and included occurrence, while the next undo returns early and leaves that occurrence included.
severity: blocker
criteria_results:
- Schema entities, relationships, and declared uniqueness checks: pass.
- Distinct run IDs and ordinary run membership isolation: pass.
- Atomic/state-based undo and INV-4 recoverable run units: fail on post-undo insertion path.
- Invalid/unparsed retained input and add-only records: pass for declared cases.
- Exact money and explicit currency: pass.
- Structured provenance, privacy, and local boundary: pass.
- Full declared backend suite: pass.
scope_creep: none - changed files are within declared scope or protocol-mandated request artifacts.
looks_done_but_wrong: declared tests and completion gate are green, but no declared test exercises adding records after a run is undone.
ease_of_misuse: `undo_import_run(run_id)` -> `add_source_record(run_id, ...)` -> `add_occurrence(run_id, ...)` -> repeated `undo_import_run(run_id)` returns early, leaving an included occurrence under an undone run.
evidence:
- `python -m unittest tests.acceptance.test_core_foundation_review -v`: exit 1; failing assertion at tests/acceptance/test_core_foundation_review.py:36.
- Product independently reran the same acceptance command and reproduced `inclusion_state = included` after the second undo.
- `backend/persistence.py:229-245` inserts a source record without checking run state.
- `backend/persistence.py:304-321` inserts an included occurrence without checking run state.
- `backend/persistence.py:385-386` returns early solely because the run is already marked undone.
- Review evidence: docs/loop/lanes/review/evidence/REQ-20260712-200417-data-eng-iter-1-review.json
requested_fix:
- Prevent an undone run from accepting new source records or included occurrences, and add red-capable backend regression coverage proving repeated undo cannot leave any included occurrence in an undone run.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-12T20:17:15Z
expected_reply:
- implementation commit and changed files
- exact verification commands, exit codes, and new iteration-2 evidence paths
- IMPLEMENTATION_DONE followed by REVIEW_REQUEST using the same request_id
