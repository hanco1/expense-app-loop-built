# REVIEW_REQUEST

message_type: REVIEW_REQUEST
request_id: REQ-20260713-073512-data-eng
parent_request_id:
iteration: 2
from_lane: data-eng
to_lane: review
status: REVIEWING
created_at: 2026-07-13T08:03:32Z
implementation_commit: 6bca89e
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/import-pipeline.md
- docs/loop/messages/REQ-20260713-073512-data-eng/FIX_REQUEST-iter-2.md
- docs/loop/messages/REQ-20260713-073512-data-eng/IMPLEMENTATION_DONE-iter-2.md
artifact_scope:
- backend/statement_import.py
- backend/persistence.py
- tests/backend/test_statement_import_csv.py
- tests/acceptance/test_statement_import_review.py
acceptance_criteria:
- A source record whose amount cannot be represented in exact SQLite minor units is retained with explicit `invalid_amount` failure and does not create a normalized transaction.
- Unexpected failure at any persistence step leaves no active/effective partial support and returns `StatementImportFailure.run_id` for inspection.
- A failed import retains introduced facts, marks its run terminal `failed`, excludes introduced occurrences with `import_failed`, and reports a parsed row without an occurrence as `persistence_incomplete`.
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
- Eight flat JSON records prefixed `REQ-20260713-073512-data-eng-iter-2-` in docs/loop/evidence; all record exit_code 0 and ran_at 2026-07-13T08:02:11Z.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-13T08:04:09Z
expected_reply:
- REVIEW_DONE PASS or blocker-severity FIX_REQUEST
- per-criterion result, scope-creep result, looks-done-but-wrong assessment, ease-of-misuse answer, exact commands/exit codes, and review evidence path
