# FIX_REQUEST

message_type: FIX_REQUEST
request_id: REQ-20260713-073512-data-eng
parent_request_id:
iteration: 4
from_lane: product
to_lane: data-eng
status: FIX_REQUESTED
created_at: 2026-07-14T06:22:27Z
implementation_commit: e94a09a
review_commit: eb8d745
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/import-pipeline.md
- docs/review/REQ-20260713-073512-data-eng-iter-4-boundary-matrix.md
- docs/loop/lanes/review/evidence/REQ-20260713-073512-data-eng-iter-4-boundary-matrix.json
- docs/loop/messages/REQ-20260713-073512-data-eng/BLOCKED-review-iter-3.md
artifact_scope:
- backend/statement_import.py
- tests/backend/test_statement_import_csv.py
- docs/loop/lanes/data-eng/**
frozen_review_artifacts:
- tests/acceptance/test_statement_import_review.py
- docs/review/REQ-20260713-073512-data-eng-iter-4-boundary-matrix.md
requested_fix:
- Replace failure-specific Decimal handling with one positive-whitelist amount parser. Do not branch on NaN, Infinity, underflow, whitespace, Unicode, or any other named failure family.
- A nonblank raw Debit or Credit token is valid if and only if its whole token matches the frozen ASCII decimal grammar, has no minus sign or negative-zero spelling, is mathematically finite, converts exactly to non-negative integer CAD cents without Decimal-context behavior, and falls in `0..9223372036854775807` inclusive.
- Evaluate the decimal coefficient, fractional-digit count, and exponent as exact integer/string structure. Zero coefficients map to zero cents regardless of exponent magnitude. Nonzero negative scales require exact divisibility by the required power of ten; non-negative scales append zeros only when the resulting magnitude remains in range. Avoid ambient Decimal precision, flags, traps, rounding, underflow, overflow, and unbounded power allocation.
- Reject every non-whitelisted token as one retained row-level `invalid_amount`; create no normalized transaction or occurrence and leave the import run active/inspectable.
- Preserve `missing_amount` for both absent/all-whitespace cells and `ambiguous_amount` when both cells are present, exactly as A01-A10 specify.
- Exercise the same whitelist through both Debit and Credit; apply Debit's negative sign only after the non-negative magnitude is validated.
- Add backend coverage for the parser rule as a class, including representative red IDs and valid guardrails. Do not edit the frozen acceptance test or matrix document.
frozen_matrix:
- 36 valid tokens and 100 invalid tokens each run through Debit and Credit, plus A01-A10 absence/ambiguity semantics: 282 paths total.
- Baseline against e94a09a: 42 red paths across V29-V30; I15-I19, I27, I32, I43, I51, I61-I64, I69, I73-I76, and I80.
- The remaining 240 paths are green guardrails and must stay green.
- No case may be added, removed, or changed after review commit eb8d745.
acceptance_criteria:
- `python -m unittest tests.acceptance.test_statement_import_review -v` exits 0 with all 282 matrix paths and the two existing acceptance behaviors green.
- Every invalid matrix token is retained with `parse_status=failed`, `error_code=invalid_amount`, no normalized transaction/occurrence, and `parse_failed:invalid_amount`.
- Every valid matrix token yields the exact documented cents on both Debit and Credit, including extreme-exponent zero and inclusive SQLite maximum cases.
- The original fixture, idempotency, duplicate, run undo, manual-correction, provenance, privacy, and failed-import recovery behavior remains green.
- No new dependency, system installation, OCR, network client, telemetry, or subprocess path is introduced.
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
- The human approved temporary `max_fix_cycles: 7` for iteration 4.
- Do not append another FIX_REQUESTED target row. Data-eng's authoritative start is the single `FIX_REQUESTED -> IMPLEMENTING` transition, reaching raw 7/7.
- Product must restore `max_fix_cycles: 3` immediately after ACCEPTED.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: pending
- sent_at:
expected_reply:
- IMPLEMENTATION_DONE iteration 4 with the whitelist design, implementation commit, changed files, unchanged frozen matrix, exact command exits, flat evidence records, and no unapproved dependencies.
