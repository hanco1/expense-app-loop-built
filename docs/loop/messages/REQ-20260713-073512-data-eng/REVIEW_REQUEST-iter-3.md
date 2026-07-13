# REVIEW_REQUEST

message_type: REVIEW_REQUEST
request_id: REQ-20260713-073512-data-eng
parent_request_id:
iteration: 3
from_lane: data-eng
to_lane: review
status: REVIEWING
created_at: 2026-07-13T08:55:13Z
implementation_commit: e94a09a
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/import-pipeline.md
- docs/loop/messages/REQ-20260713-073512-data-eng/FIX_REQUEST-iter-3.md
- docs/loop/messages/REQ-20260713-073512-data-eng/IMPLEMENTATION_DONE-iter-3.md
- docs/review/REQ-20260713-073512-data-eng-iter-2.md
artifact_scope:
- backend/statement_import.py
- tests/backend/test_statement_import_csv.py
- tests/acceptance/test_statement_import_review.py
acceptance_criteria:
- A valid-shape CSV row containing `NaN` remains an explicit retained `invalid_amount` failure with no normalized transaction or occurrence.
- A valid-shape CSV row containing `1e999999` remains an explicit retained `invalid_amount` failure with no normalized transaction or occurrence.
- Decimal construction, arithmetic, comparison, integral-value, and integer-conversion exceptions cannot abort the full import or remove the candidate row.
- Every iteration-2 behavior remains green, no dependency changes, and the completion gate returns SHIP_CHECK_OK.
verification:
- python -m unittest tests.backend.test_statement_fixtures -v
- python -m unittest tests.backend.test_statement_import_csv -v
- python -m unittest tests.backend.test_statement_import_pdf -v
- python -m unittest tests.backend.test_statement_import_idempotency -v
- python -m unittest tests.backend.test_statement_import_runs -v
- python -m unittest tests.backend.test_statement_import_local_boundary -v
- python -m unittest discover -s tests/backend -p "test_*.py" -v
- python -m unittest tests.acceptance.test_statement_import_review -v
evidence:
- Eight flat JSON records prefixed `REQ-20260713-073512-data-eng-iter-3-` in docs/loop/evidence; every record has exit_code 0 and ran_at 2026-07-13T08:54:25Z.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-13T08:55:54Z
expected_reply:
- REVIEW_DONE PASS or blocker-severity FIX_REQUEST
- per-criterion results, scope-creep result, looks-done-but-wrong assessment, ease-of-misuse answer, exact commands/exit codes, and review evidence path
