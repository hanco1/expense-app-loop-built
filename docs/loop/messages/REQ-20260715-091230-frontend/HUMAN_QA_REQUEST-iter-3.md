# HUMAN_QA_REQUEST

message_type: HUMAN_QA_REQUEST
request_id: REQ-20260715-091230-frontend
iteration: 3
from_lane: product
to_lane: human
status: REVIEWING
created_at: 2026-07-15T20:15:22Z
implementation_commit: 38479e5
review_commit: c56c4e1

## Live Origin

- Open `http://127.0.0.1:8766`.
- Startup printed exactly `Local expense app: http://127.0.0.1:8766`.
- The live listener is expense-app PID 176376; the loop dashboard remains PID 73908 on port 8765.

## Product Probes

- Expense-app root: HTTP 200, title `Monthly Expense Review`.
- Expense-app `/api/session`: HTTP 200 with `local_only: true` and a session CSRF token.
- Second default-port startup: exit code 1, clear `Unable to bind local expense app at 127.0.0.1:8766` error, empty stdout, and no success URL.

## Human Check

- Confirm that 8766 visibly opens the expense app rather than the loop dashboard.
- Return explicit PASS if this issue is resolved, or report the next concrete issue. The request remains REVIEWING until then.
