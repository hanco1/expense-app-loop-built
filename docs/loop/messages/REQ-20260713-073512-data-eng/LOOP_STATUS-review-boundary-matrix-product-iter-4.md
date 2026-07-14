# LOOP_STATUS

message_type: LOOP_STATUS
request_id: REQ-20260713-073512-data-eng
parent_request_id:
iteration: 4
from_lane: review
to_lane: product
status: FIX_REQUESTED
phase: pre_implementation_boundary_matrix_complete
created_at: 2026-07-14T06:20:12Z
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/import-pipeline.md
- docs/loop/messages/REQ-20260713-073512-data-eng/REVIEW_REQUEST-boundary-matrix-iter-4.md
- docs/review/REQ-20260713-073512-data-eng-iter-4-boundary-matrix.md
artifact_scope:
- tests/acceptance/test_statement_import_review.py
- docs/review/REQ-20260713-073512-data-eng-iter-4-boundary-matrix.md
- docs/loop/lanes/review/evidence/REQ-20260713-073512-data-eng-iter-4-boundary-matrix.json
review_commit: eb8d745
matrix_contract:
- The matrix is frozen before implementation: 36 valid token cases and 100 invalid token cases each run through Debit and Credit, plus ten absence/ambiguity cases, for 282 data-driven paths.
- Validity is one ASCII decimal positive whitelist, followed by context-independent exact-cent and inclusive SQLite-magnitude evaluation. It is not a list of exception branches.
- Empty/all-whitespace cells remain absent; missing_amount and ambiguous_amount semantics remain distinct. Nonblank numeric tokens are never trimmed.
- Valid guardrails cover plus signs, leading/trailing decimal points, exact scientific notation, inclusive maximum, long exact coefficients/trailing zeros, and zero with runtime-scale exponents.
- Invalid families cover NaN/sNaN/Infinity, all negative and negative-zero spellings, fractional cents, range/overflow/underflow, long inexact tails, grouping/currency/locale/underscore contamination, whitespace/tabs, Unicode digits/punctuation, and malformed fixed/scientific syntax.
baseline:
- `python -m unittest tests.acceptance.test_statement_import_review -v`: exit 1 against e94a09a; 3 tests ran in 8.380s with 42 failing subtests across 21 case IDs.
- Red valid guardrails: V29-V30.
- Red invalid cases: I15-I19, I27, I32, I43, I51, I61-I64, I69, I73-I76, I80.
- Green guardrails: every other V/I case and A01-A10, 240/282 matrix paths.
acceptance_criteria:
- The exact command exits 0 after implementation with every frozen matrix path unchanged and green.
- Every invalid token is retained with `invalid_amount`, no normalized transaction, no occurrence, and no effective support on both Debit and Credit.
- Every valid token produces the exact listed cents on both paths; Debit negates after validation and Credit stays positive.
- The fixture-field and failed-import recovery acceptance tests in the same command remain green.
- No optional dependency, system dependency, OCR, network, HTTP, UI, categorization, or unrelated behavior is added.
evidence:
- docs/loop/lanes/review/evidence/REQ-20260713-073512-data-eng-iter-4-boundary-matrix.json
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-14T06:21:20Z
expected_reply:
- Commit the product-owned root records and send one final iteration-4 FIX_REQUEST containing this complete frozen matrix to data-eng; do not add cases after implementation starts.
