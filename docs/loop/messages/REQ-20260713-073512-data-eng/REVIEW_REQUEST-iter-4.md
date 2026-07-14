# REVIEW_REQUEST

message_type: REVIEW_REQUEST
request_id: REQ-20260713-073512-data-eng
parent_request_id:
iteration: 4
from_lane: data-eng
to_lane: review
status: REVIEWING
created_at: 2026-07-14T06:29:45Z
implementation_commit: 06ac048
review_commit: eb8d745
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/import-pipeline.md
- docs/loop/messages/REQ-20260713-073512-data-eng/FIX_REQUEST-iter-4.md
- docs/loop/messages/REQ-20260713-073512-data-eng/IMPLEMENTATION_DONE-iter-4.md
- docs/review/REQ-20260713-073512-data-eng-iter-4-boundary-matrix.md
artifact_scope:
- backend/statement_import.py
- tests/backend/test_statement_import_csv.py
- tests/acceptance/test_statement_import_review.py
acceptance_criteria:
- The unchanged frozen 282-path matrix passes in full across valid/invalid Debit and Credit tokens plus A01-A10 absence/ambiguity semantics.
- Valid tokens convert to exact documented cents in `0..9223372036854775807`; extreme-exponent zero is context-independent and inclusive maximum remains valid.
- Invalid tokens remain retained `invalid_amount` rows with no normalized transaction or occurrence and no failure-family-specific code branches.
- Original fixtures, PDF extraction, identity/idempotency, duplicate visibility, run recovery, undo, correction history, provenance, privacy, and local boundary remain green.
- No frozen artifact, dependency, OCR/network/telemetry surface, or system installation changed.
verification:
- python -m unittest tests.backend.test_statement_fixtures -v
- python -m unittest tests.backend.test_statement_import_csv -v
- python -m unittest tests.backend.test_statement_import_pdf -v
- python -m unittest tests.backend.test_statement_import_idempotency -v
- python -m unittest tests.backend.test_statement_import_runs -v
- python -m unittest tests.backend.test_statement_import_local_boundary -v
- python -m unittest discover -s tests/backend -p "test_*.py" -v
- python -m unittest tests.acceptance.test_statement_import_review -v
- python completion_gate.py --loop-dir docs/loop
evidence:
- Nine flat JSON records prefixed `REQ-20260713-073512-data-eng-iter-4-` in `docs/loop/evidence/`; every record has exit_code 0.
- Backend discovery passed 31/31; frozen acceptance passed all 282 matrix paths plus the two existing acceptance behaviors.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-14T06:30:55Z
expected_reply:
- REVIEW_DONE PASS or blocker-severity FIX_REQUEST.
- Per-criterion results, scope-creep result, looks-done-but-wrong assessment, ease-of-misuse answer, exact commands/exit codes, and review evidence path.
