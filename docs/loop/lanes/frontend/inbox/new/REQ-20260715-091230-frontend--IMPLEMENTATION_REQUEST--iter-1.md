# IMPLEMENTATION_REQUEST

message_type: IMPLEMENTATION_REQUEST
request_id: REQ-20260715-091230-frontend
parent_request_id:
iteration: 1
from_lane: product
to_lane: frontend
status: REQUESTED
created_at: 2026-07-15T09:12:30Z
user_facing: true
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/import-pipeline.md
- docs/product/analysis-core.md
- docs/product/local-web-api.md
- docs/product/local-web-app.md
artifact_scope:
- frontend/**
- tests/frontend/**
- docs/design/**
- docs/loop/lanes/frontend/**
purpose:
- Deliver the complete loopback-only browser MVP over the accepted LocalWebApi, including import/run review, duplicate/category decisions, exact monthly analysis, a reconciled pie chart, reproducible startup, and browser-test evidence.
implementation_requirements:
- Implement every runtime, security, UI, accessibility, exact-money, reconciliation, fixture-oracle, and startup rule in `docs/product/local-web-app.md`.
- Keep the HTTP listener strictly on `127.0.0.1`, serve assets and `/api/**` same-origin, reject invalid/non-loopback Host values, and delegate every API operation to the accepted LocalWebApi without duplicating business rules.
- Provide file picker and drag-and-drop for CSV/text-PDF, sequential per-file runs, visible failed rows, persistent run history/detail, confirmed run undo, category correction, and duplicate same/distinct decisions.
- Default to the newest month and show exact spending, credits, count, category table, included transactions, provenance, and an accessible pie chart that reconciles from the same response without floating-point money arithmetic.
- Add deterministic UI/server tests plus one real browser end-to-end fixture flow. Use only the approved synthetic fixtures; never copy or log real statement data.
- Update root README startup instructions only through a product-owned follow-up request or return the exact proposed text/path to product, because README.md is outside frontend write scope.
non_goals:
- OCR execution or OCR-engine installation
- LAN/public binding, CORS, remote assets, analytics, telemetry, cloud/network clients, service workers, deployment, authentication, or multi-user support
- new bank formats, exchange rates, direct bank connections, or changes to accepted backend business rules
acceptance_criteria:
- C1 loopback/security: listener binds only 127.0.0.1, assets and API are same-origin, invalid/non-loopback Host is rejected, CSP/security headers are present, CSRF protects every mutation, and logs contain no statement/token/transaction content.
- C2 import/run UX: picker and drop each accept CSV/PDF without a path textbox; multiple files become distinct sequential runs; CSV shows 23/22/1/22 with visible `missing_amount`, PDF shows 12/12/0/12, history persists, detail is structured, and confirmed undo refreshes all affected views.
- C3 dashboard/reconciliation: newest month defaults; May is 50340/60000/12 and June is 277617/72999/22; exact string money is formatted without floating-point arithmetic; category rows, included transaction rows, spending total, and pie/legend reconcile exactly; credits remain outside slices.
- C4 human decisions: category corrections, Tim Hortons pending/same/distinct flows, kept-identity choice, 409 no-optimism behavior, append-only history, reload persistence, complete-support undo, and re-import restoration are visible and correct.
- C5 accessibility/failures: keyboard navigation, focus, semantic labels, live status, non-color-only chart legend, zero/empty/loading/error/conflict states, safe text rendering, and per-action double-submit prevention are covered.
- C6 browser end-to-end: a real local browser crosses the real loopback adapter with both approved fixtures, asserts the exact oracle and bad row, exercises correction/duplicate/re-import/undo, verifies reload persistence, and records privacy-safe screenshots or structured evidence.
- C7 regressions/delivery: frontend tests and full backend discovery are green; no system dependency, OCR, remote network, raw logging, or accepted-fixture hash change is introduced; startup and shutdown are reproducible.
verification:
- python -m unittest discover -s tests/frontend -p "test_*.py" -v
- python -m unittest discover -s tests/backend -p "test_*.py" -v
- a deterministic browser E2E command documented by the implementation and runnable from the repository root
- python completion_gate.py --loop-dir docs/loop --request-id REQ-20260715-091230-frontend
evidence_requirements:
- One flat JSON evidence record per verification command under docs/loop/evidence/, bound to this request and iteration 1.
- Record exit codes, test counts, HTTP statuses, exact fixture counts/totals, reconciliation booleans, browser viewport/route/actions, and unchanged fixture hashes. Evidence may reference synthetic fixture content but must not contain raw source bytes, CSRF tokens, database contents, or real financial data.
dependencies:
- Prefer the standard library and browser-native HTML/CSS/JavaScript. Existing Python Playwright may be used for automated browser verification. A project/pip dependency may follow policy; stop and ask before any system package or browser/system-runtime installation.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: pending
- sent_at:
expected_reply:
- IMPLEMENTATION_DONE with implementation commit, changed files, runtime/security decisions, UI behavior, exact fixture and reconciliation results, browser evidence, all verification exits, dependency statement, and blockers.
- Then REVIEW_REQUEST to the verified review thread using the same request_id and iteration. Product retains final acceptance and human-QA authority.
