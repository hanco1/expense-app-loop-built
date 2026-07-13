# FIX_REQUEST

message_type: FIX_REQUEST
request_id: REQ-20260713-073512-data-eng
parent_request_id:
iteration: 3
from_lane: product
to_lane: data-eng
status: FIX_REQUESTED
created_at: 2026-07-13T08:50:46Z
implementation_commit: 6bca89e
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/import-pipeline.md
- docs/loop/messages/REQ-20260713-073512-data-eng/BLOCKED-review-iter-2.md
- docs/review/REQ-20260713-073512-data-eng-iter-2.md
artifact_scope:
- backend/statement_import.py
- tests/backend/test_statement_import_csv.py
- tests/acceptance/test_statement_import_review.py
requested_fix:
- Catch every Decimal construction, arithmetic, comparison, and integer-conversion exception that makes an amount unrepresentable.
- Convert each such value to row-level `RecordParseFailure("invalid_amount")`; retain the original source row and create no normalized transaction.
- Add red-capable backend regressions for `NaN` and an exponent that overflows the active Decimal context, including `1e999999` or an equivalent deterministic value.
- Preserve all iteration-2 partial-import, failed-run, identity, duplicate, undo, correction, provenance, privacy, and dependency boundaries.
acceptance_criteria:
- A valid-shape CSV row containing `NaN` is retained with `parse_status=failed`, `parse_error=invalid_amount`, and no normalized transaction.
- A valid-shape CSV row containing an overflowing exponent is retained with `parse_status=failed`, `parse_error=invalid_amount`, and no normalized transaction.
- Neither Decimal edge case fails the whole import or disappears from run detail.
- The review-owned Decimal boundary test passes along with all eight iteration-2 commands and the completion gate.
- No dependency or system-level installation is introduced.
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
policy:
- The human approved `max_fix_cycles: 4` for this iteration.
- Product must restore `max_fix_cycles: 3` immediately after this request reaches ACCEPTED.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-13T08:51:58Z
expected_reply:
- IMPLEMENTATION_DONE iteration 3 with implementation commit, changed files, exact Decimal exception mapping, all command exit codes, flat evidence paths, and no unapproved dependencies.
