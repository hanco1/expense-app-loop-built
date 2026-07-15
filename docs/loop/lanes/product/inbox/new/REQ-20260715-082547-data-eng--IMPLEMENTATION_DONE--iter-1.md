# IMPLEMENTATION_DONE

message_type: IMPLEMENTATION_DONE
request_id: REQ-20260715-082547-data-eng
parent_request_id:
iteration: 1
from_lane: data-eng
to_lane: product
status: IMPLEMENTATION_DONE
created_at: 2026-07-15T08:41:53Z
implementation_commit: efff2f4
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/import-pipeline.md
- docs/product/analysis-core.md
- docs/product/local-web-api.md
- docs/loop/messages/REQ-20260715-082547-data-eng/IMPLEMENTATION_REQUEST-iter-1.md
artifact_scope:
- backend/**
- contracts/**
- tests/backend/**
- docs/data/**
- docs/loop/lanes/data-eng/**
changed_files:
- backend/__init__.py
- backend/local_web_api.py
- backend/persistence.py
- contracts/__init__.py
- contracts/local_web_api.py
- docs/data/local-web-api.md
- docs/loop/lanes/data-eng/current.md
- docs/loop/lanes/data-eng/inbox/cur/REQ-20260715-082547-data-eng--IMPLEMENTATION_REQUEST--iter-1.md
- tests/backend/local_web_api_support.py
- tests/backend/test_local_web_api_security.py
- tests/backend/test_local_web_api_imports.py
- tests/backend/test_local_web_api_runs.py
- tests/backend/test_local_web_api_months.py
- tests/backend/test_local_web_api_decisions.py
- tests/backend/test_local_web_api_errors.py
- tests/backend/test_local_web_api_boundary.py
facade_store_contract_decisions:
- `LocalWebApi` is an in-process method/path/header/bytes dispatcher returning typed `LocalWebResponse` JSON bytes. `LocalExpenseApi` is an exported compatibility alias; no listener or static serving was added.
- `LocalWebApi.from_database()` initializes and reopens only the caller-provided SQLite path. `CoreStore.list_import_run_summaries()` returns every active, failed, and undone run ordered by `(created_at DESC, run_id DESC)`.
- All writes delegate to the accepted `StatementImportService`, `AnalysisService`, and `CoreStore`; the facade does not duplicate parser, identity, category, duplicate-component, aggregation, or undo rules.
- Every POST checks the per-instance CSRF token with constant-time comparison before dispatch and is serialized by an in-process lock. Invalid or duplicate JSON/header members fail before writes.
- Run detail removes `retained_input`, preserves structured locator/error/provenance, and adds current duplicate state plus effective inclusion reason. Duplicate read models include both sides' date, merchant, exact amount, currency, inclusion, and append-only history.
- Every minor-unit integer is converted to a base-10 string only at JSON serialization. Counts remain integers and currency remains explicit.
- Stable errors map validation/security/missing/conflict/size/media/parser/unexpected classes to 400/403/404/409/413/415/422/500 without exception text, traceback, raw input, logging, or CORS allowance.
approved_fixture_results:
- CSV: 23 source records, 22 parsed transactions, one `csv-row:21` `missing_amount` failure, 22 occurrences.
- PDF: 12 source records, 12 parsed transactions, no failed record, 12 occurrences.
- Persistent run listing covers active, failed, and undone states newest first across facade recreation.
- May: spending integer/string `50340`/`"50340"`, credits `60000`/`"60000"`, 12 transactions.
- June: spending integer/string `277617`/`"277617"`, credits `72999`/`"72999"`, 22 transactions.
- Exact CSV re-import creates a distinct linked run without changing June totals/counts; correction history count remains one after all support is undone and later restored.
- Tim Hortons starts pending with both included; same then distinct produces two append-only decisions and restores both. The invalid three-identity component proposal returns 409 and appends zero rows.
verification:
- command: python -m unittest tests.backend.test_local_web_api_security -v
  exit_code: 0
  result: 2 tests passed; stable session, typed boundary, CSRF rejection/no-write, and no CORS allowance are green.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-tests-backend-test-local-web-api-security-v.json
- command: python -m unittest tests.backend.test_local_web_api_imports -v
  exit_code: 0
  result: 2 tests passed; fixture counts, visible failed row, privacy-safe detail, persistent active/failed/undone listing, and newest-first ordering are green.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-tests-backend-test-local-web-api-imports-v.json
- command: python -m unittest tests.backend.test_local_web_api_runs -v
  exit_code: 0
  result: 1 test passed; exact re-import, per-run undo, repeated-undo conflict, complete support loss, correction survival, and later restore are green.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-tests-backend-test-local-web-api-runs-v.json
- command: python -m unittest tests.backend.test_local_web_api_months -v
  exit_code: 0
  result: 1 test passed; exact May/June string-money oracles, category reconciliation, and zero-spending credits are green.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-tests-backend-test-local-web-api-months-v.json
- command: python -m unittest tests.backend.test_local_web_api_decisions -v
  exit_code: 0
  result: 2 tests passed; canonical category history, Tim Hortons same/distinct history, effective run-detail exclusion, and atomic 409 graph rejection are green.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-tests-backend-test-local-web-api-decisions-v.json
- command: python -m unittest tests.backend.test_local_web_api_errors -v
  exit_code: 0
  result: 3 tests passed; 400/404/409/413/415/422/500 envelopes, mixed-currency conflict, inspectable failed run, and no raw/traceback leak are green.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-tests-backend-test-local-web-api-errors-v.json
- command: python -m unittest tests.backend.test_local_web_api_boundary -v
  exit_code: 0
  result: 2 tests passed; no listener, network, subprocess, OCR, telemetry, dependency, raw logging, or out-of-path persistence was introduced; fixture hashes unchanged.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-tests-backend-test-local-web-api-boundary-v.json
- command: python -m unittest discover -s tests/backend -p "test_*.py" -v
  exit_code: 0
  result: 65 tests passed with no failures or errors.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-discover-s-tests-backend-p-test-py-v.json
- command: python completion_gate.py --loop-dir docs/loop --request-id REQ-20260715-082547-data-eng
  exit_code: 0
  result: SHIP_CHECK_OK REQ-20260715-082547-data-eng
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-completion-gate.json
fixture_hashes:
- CSV: 9F93F107DDD02AEE2FB0A0AE19EB962180C680D1FB06D4D90959C96ED8CD7BAA
- PDF: F4B6B524D7C6140EE3F3E24CE87C4A36F0B40619395B5DC17B03F1B99DBC11F8
dependency_statement:
- No dependency was added or installed. The existing project pin remains `pypdf==6.12.2`; no system dependency was used.
blockers:
- None.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-15T08:42:50Z
needs_review_by: review
expected_reply:
- Product retains final acceptance authority.
- Review evaluates implementation commit efff2f4 against C1-C7, all nine evidence records, prior accepted invariants, scope, privacy, and ease of misuse, then returns REVIEW_DONE PASS or a blocker-severity FIX_REQUEST.
