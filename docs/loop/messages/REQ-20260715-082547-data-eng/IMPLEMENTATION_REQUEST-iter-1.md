# IMPLEMENTATION_REQUEST

message_type: IMPLEMENTATION_REQUEST
request_id: REQ-20260715-082547-data-eng
parent_request_id:
iteration: 1
from_lane: product
to_lane: data-eng
status: REQUESTED
created_at: 2026-07-15T08:25:47Z
user_facing: false
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/import-pipeline.md
- docs/product/analysis-core.md
- docs/product/local-web-api.md
artifact_scope:
- backend/**
- contracts/**
- tests/backend/**
- docs/data/**
- docs/loop/lanes/data-eng/**
purpose:
- Add the local JSON-ready application boundary and persistent import-run listing required by the browser UI, without adding a listener or frontend assets.
implementation_requirements:
- Implement every request/response, exact-money, CSRF, error, privacy, and ordering rule in `docs/product/local-web-api.md`.
- Route all writes through the already accepted StatementImportService, AnalysisService, and CoreStore invariants; do not duplicate or weaken import, category, duplicate-component, or undo logic.
- Add persistent newest-first run discovery covering active, failed, and undone runs.
- Serialize all minor-unit money as base-10 JSON strings and never expose retained raw source input, tracebacks, or permissive CORS headers.
- Cross the facade with both approved fixtures, including retained bad-row visibility, exact re-import idempotency, exact May/June totals, credits, corrections, duplicate history, and per-run undo.
non_goals:
- HTML, CSS, browser JavaScript, drag-and-drop, pie-chart rendering, static serving, or live browser QA
- socket binding, LAN/public access, network clients, telemetry, subprocesses, cloud services, OCR, scanned receipts, or system dependencies
- new bank formats, exchange rates, authentication, or financial advice
acceptance_criteria:
- C1 session/security: session metadata is deterministic; every mutation requires the per-process CSRF token; rejected tokens make no write; no CORS allowance or raw-data logging. Verify `python -m unittest tests.backend.test_local_web_api_security -v`.
- C2 import/run read model: both fixtures import from raw bytes, failed CSV row is visible by locator/error, all runs persist newest first across facade recreation, and detail never exposes retained input. Verify `python -m unittest tests.backend.test_local_web_api_imports -v`.
- C3 exact idempotency/undo: exact re-import adds a run without double counting; individual undo is inspectable and preserves category correction history through complete support loss and re-import. Verify `python -m unittest tests.backend.test_local_web_api_runs -v`.
- C4 monthly JSON: May and June exact oracles and every category reconcile; all money is a decimal string; Amazon refund and E-Transfer remain non-spending credits. Verify `python -m unittest tests.backend.test_local_web_api_months -v`.
- C5 human decisions: category and duplicate routes append exactly once, expose history, retain the legitimate Tim Hortons pair pending/distinct, and atomically reject invalid component proposals with 409/no append. Verify `python -m unittest tests.backend.test_local_web_api_decisions -v`.
- C6 errors/privacy: status/error envelopes are stable for validation, missing, conflict, media, size, parser, and unexpected failures; no response or logs leak raw statement content. Verify `python -m unittest tests.backend.test_local_web_api_errors -v`.
- C7 regressions/boundary: full backend discovery stays green and the slice adds no listener, network client, OCR, subprocess, telemetry, or system dependency. Verify `python -m unittest tests.backend.test_local_web_api_boundary -v` plus backend discovery.
verification:
- python -m unittest tests.backend.test_local_web_api_security -v
- python -m unittest tests.backend.test_local_web_api_imports -v
- python -m unittest tests.backend.test_local_web_api_runs -v
- python -m unittest tests.backend.test_local_web_api_months -v
- python -m unittest tests.backend.test_local_web_api_decisions -v
- python -m unittest tests.backend.test_local_web_api_errors -v
- python -m unittest tests.backend.test_local_web_api_boundary -v
- python -m unittest discover -s tests/backend -p "test_*.py" -v
- python completion_gate.py --loop-dir docs/loop --request-id REQ-20260715-082547-data-eng
evidence_requirements:
- One flat JSON evidence record per verification command under docs/loop/evidence/, bound to this request and iteration 1.
- Report fixture counts, exact totals as integer/string pairs, run states, decision/correction history counts, response statuses, exit codes, and unchanged fixture hashes without logging non-approved raw financial data.
dependencies:
- Prefer the Python standard library and existing `pypdf`. A pip-only project dependency may follow policy; stop and ask before any system-level installation.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-15T08:27:46Z
expected_reply:
- IMPLEMENTATION_DONE with implementation commit, changed files, facade/store contract decisions, exact verification results, flat evidence paths, dependency statement, and blockers.
- Then REVIEW_REQUEST to the verified review thread using the same request_id and iteration.
