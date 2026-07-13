# FIX_REQUEST

message_type: FIX_REQUEST
request_id: REQ-20260713-073512-data-eng
parent_request_id:
iteration: 2
from_lane: review
to_lane: data-eng
status: FIX_REQUESTED
created_at: 2026-07-13T07:56:00Z
implementation_commit: 9fccab6
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/import-pipeline.md
- docs/loop/messages/REQ-20260713-073512-data-eng/IMPLEMENTATION_REQUEST-iter-1.md
- docs/loop/messages/REQ-20260713-073512-data-eng/IMPLEMENTATION_DONE-iter-1.md
- docs/review/REQ-20260713-073512-data-eng-iter-1.md
artifact_scope:
- backend/statement_import.py
- backend/persistence.py
- tests/backend/test_statement_import_csv.py
- tests/acceptance/test_statement_import_review.py
acceptance_criteria:
- A source record whose amount cannot be represented in exact SQLite minor units is retained with an explicit failure, or the rejected import is rolled back without leaving any active/effective partial state.
- Unexpected failure at any persistence step cannot expose a partially imported active run to effective queries without returning an inspectable `run_id` to the caller.
failed_criteria:
- INV-1/INV-4/INV-6 failure: a header-valid CSV with one ordinary row followed by an oversized amount raises `OverflowError` after committing the earlier row and leaves the second row as `parsed` with `parse_failed:None`.
severity: blocker
criteria_results:
- Pinned fixture hashes and byte-for-byte repository copies: pass.
- CSV 23/22/1 and all exact normalized CSV fields/signs: pass.
- PDF 12/12/0 and all exact normalized PDF fields/signs: pass.
- Exact re-import idempotency, stable identities, 34 effective identities, and visible included Tim Hortons suspected pair: pass.
- Ordinary run detail, active-support undo, append-only links, and correction survival: pass.
- Failed-import recoverability and explicit failure visibility: fail.
- Bytes-only/no-network/no-OCR/no-raw-log boundary and non-goals: pass.
- Full declared backend suite: pass.
scope_creep: none - changed files are within declared scope or protocol-mandated request artifacts.
looks_done_but_wrong: seven declared commands and SHIP_CHECK_OK are green, but no declared test fails when a later persistence error leaves earlier rows effective.
ease_of_misuse: submit a header-valid CSV whose second amount exceeds SQLite INTEGER range; `import_bytes` raises after the first row becomes effective under an active run whose ID is not returned.
evidence:
- `python -m unittest tests.acceptance.test_statement_import_review -v`: exit 1; failure at tests/acceptance/test_statement_import_review.py:92.
- `backend/statement_import.py:163-201` creates the run and persists each component through separate committed calls.
- `backend/persistence.py:448` raises while binding the oversized integer after prior writes have committed.
- `backend/persistence.py:716-721` misreports the parsed row without an occurrence as `parse_failed:None`.
- All seven declared commands exited 0; full backend discovery ran 24 tests.
- Completion gate exited 0 with `SHIP_CHECK_OK REQ-20260713-073512-data-eng`.
- Review evidence: docs/loop/lanes/review/evidence/REQ-20260713-073512-data-eng-iter-1-review.json
requested_fix:
- Make record-level out-of-range money an explicit retained failure and ensure the public import operation cannot leave partial active/effective state if any later persistence step raises. Add red-capable backend regression coverage for the review sequence.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-13T07:56:50Z
expected_reply:
- implementation commit and changed files
- exact verification commands, exit codes, and iteration-2 evidence paths
- IMPLEMENTATION_DONE followed by REVIEW_REQUEST using the same request_id
