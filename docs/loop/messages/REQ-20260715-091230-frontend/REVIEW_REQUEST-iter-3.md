# REVIEW_REQUEST

message_type: REVIEW_REQUEST
request_id: REQ-20260715-091230-frontend
iteration: 3
from_lane: product
to_lane: review
status: REVIEWING
created_at: 2026-07-15T20:08:06Z
implementation_commit: 38479e5
handoff_commit: 2b09659

## Acceptance Contract

- Confirm the default port is 8766 across CLI help and committed startup documentation.
- Confirm every requested port is bound exclusively: an occupied port fails clearly and non-zero before any success URL, database line, fallback, or serve loop.
- Confirm a successful URL is derived from `server.server_address`, including an allocated nonzero `--port 0`, and that the printed origin serves both the expense-app root and `/api/session`.
- Preserve exact loopback Host/security handling, same-origin API/static behavior, privacy, exact-money reconciliation, approved fixture flows, and the unchanged acceptance artifact.
- Confirm the dashboard is untouched and no dependency, browser/runtime/system package, network client, telemetry, OCR, or unrelated scope was added.

## Verification Manifest

- VERIFY `python -m unittest tests.frontend.test_server -v`
- VERIFY `python -m unittest tests.acceptance.test_local_web_app_review -v`
- VERIFY `python -m unittest discover -s tests/frontend -p "test_*.py" -v`
- VERIFY `python -m unittest tests.frontend.test_browser_e2e -v`
- VERIFY `python -m unittest discover -s tests/backend -p "test_*.py" -v`
- VERIFY `python completion_gate.py --loop-dir docs/loop --request-id REQ-20260715-091230-frontend`

## Human QA Hold

- Review assesses code and machine behavior only. Product keeps the request REVIEWING after PASS, starts the actual printed 8766 URL, verifies occupied-port rejection live, and waits for explicit human PASS before ACCEPTED.
