# IMPLEMENTATION_DONE

message_type: IMPLEMENTATION_DONE
request_id: REQ-20260713-073512-data-eng
parent_request_id:
iteration: 1
from_lane: data-eng
to_lane: product
status: IMPLEMENTATION_DONE
created_at: 2026-07-13T07:50:21Z
implementation_commit: 9fccab6
code_commit: c714460
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-13T07:51:07Z
changed_files:
- backend/__init__.py
- backend/persistence.py
- backend/requirements.txt
- backend/statement_import.py
- contracts/__init__.py
- contracts/statement_import.py
- tests/backend/fixtures/.gitattributes
- tests/backend/fixtures/td-mock-2026-05.pdf
- tests/backend/fixtures/td-mock-2026-06.csv
- tests/backend/statement_support.py
- tests/backend/test_statement_fixtures.py
- tests/backend/test_statement_import_csv.py
- tests/backend/test_statement_import_pdf.py
- tests/backend/test_statement_import_idempotency.py
- tests/backend/test_statement_import_runs.py
- tests/backend/test_statement_import_local_boundary.py
- docs/loop/lanes/data-eng/import-pipeline.md
- docs/loop/lanes/data-eng/current.md
- docs/loop/lanes/data-eng/worklog.md
parser_decisions:
- `StatementImportService.import_bytes` accepts local bytes plus display filename and explicit `csv`/`pdf` source type; it never opens a caller path.
- TD-style CSV parsing preserves each data row and explicit per-row failures. Text PDF parsing uses the `StatementParser` protocol and project-level `pypdf==6.12.2`; no OCR or system process exists.
identity_and_duplicate_decisions:
- Stable identity hashes content SHA-256 plus source locator, so renamed exact bytes reuse identity while same-looking distinct rows remain separate.
- Exact re-import is an explicit run link and adds occurrence support without increasing effective identities.
- Same date, merchant, signed amount, and currency across distinct identities creates a retained `suspected_pending` link; neither side is auto-excluded.
run_query_decisions:
- Run summary exposes source metadata and counts; run detail exposes every retained row, normalized transaction, stable identity, duplicate state, and inclusion reason.
- Effective transactions are one per stable identity with at least one active included occurrence and list every active supporting run/fingerprint/locator.
- Undo removes only the selected run's support while preserving facts, duplicate links, and correction history.
fixture_hashes:
- td-mock-2026-06.csv: 9F93F107DDD02AEE2FB0A0AE19EB962180C680D1FB06D4D90959C96ED8CD7BAA
- td-mock-2026-05.pdf: F4B6B524D7C6140EE3F3E24CE87C4A36F0B40619395B5DC17B03F1B99DBC11F8
verification:
- command: python -m unittest tests.backend.test_statement_fixtures -v
  exit_code: 0
  evidence: docs/loop/evidence/REQ-20260713-073512-data-eng-iter-1-python-m-unittest-tests-backend-test-statement-fixtures-v.json
- command: python -m unittest tests.backend.test_statement_import_csv -v
  exit_code: 0
  evidence: docs/loop/evidence/REQ-20260713-073512-data-eng-iter-1-python-m-unittest-tests-backend-test-statement-import-csv-v.json
- command: python -m unittest tests.backend.test_statement_import_pdf -v
  exit_code: 0
  evidence: docs/loop/evidence/REQ-20260713-073512-data-eng-iter-1-python-m-unittest-tests-backend-test-statement-import-pdf-v.json
- command: python -m unittest tests.backend.test_statement_import_idempotency -v
  exit_code: 0
  evidence: docs/loop/evidence/REQ-20260713-073512-data-eng-iter-1-python-m-unittest-tests-backend-test-statement-import-idempotency-v.json
- command: python -m unittest tests.backend.test_statement_import_runs -v
  exit_code: 0
  evidence: docs/loop/evidence/REQ-20260713-073512-data-eng-iter-1-python-m-unittest-tests-backend-test-statement-import-runs-v.json
- command: python -m unittest tests.backend.test_statement_import_local_boundary -v
  exit_code: 0
  evidence: docs/loop/evidence/REQ-20260713-073512-data-eng-iter-1-python-m-unittest-tests-backend-test-statement-import-local-boundary-v.json
- command: python -m unittest discover -s tests/backend -p "test_*.py" -v
  exit_code: 0
  evidence: docs/loop/evidence/REQ-20260713-073512-data-eng-iter-1-python-m-unittest-discover-s-tests-backend-p-test-py-v.json
dependencies:
- `pypdf 6.12.2` was already available as a pip package and is pinned in `backend/requirements.txt`; no package installation was needed.
- No system dependency, OCR engine, network client, telemetry, or subprocess integration was added.
blockers:
- None. Product must commit the root-level evidence and message records because they are outside data-eng's static commit scope.
