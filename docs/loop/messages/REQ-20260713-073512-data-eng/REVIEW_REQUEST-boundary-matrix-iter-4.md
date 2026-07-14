# REVIEW_REQUEST

message_type: REVIEW_REQUEST
request_id: REQ-20260713-073512-data-eng
parent_request_id:
iteration: 4
from_lane: product
to_lane: review
status: FIX_REQUESTED
phase: pre_implementation_boundary_matrix
created_at: 2026-07-14T06:11:02Z
implementation_commit: e94a09a
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/import-pipeline.md
- docs/loop/messages/REQ-20260713-073512-data-eng/BLOCKED-review-iter-3.md
artifact_scope:
- tests/acceptance/test_statement_import_review.py
- docs/review/REQ-20260713-073512-data-eng-iter-4-boundary-matrix.md
- docs/loop/lanes/review/**
human_direction:
- Review must enumerate the complete numeric boundary matrix before data-eng begins iteration 4. Do not report one new numeric case per later round.
- Amount validation is one positive whitelist: valid if and only if the raw token is a decimal number whose value is finite, non-negative without negative zero, exactly representable in CAD cents, and within the allowed SQLite minor-unit range.
- All non-whitelisted inputs become retained row-level `invalid_amount` records and create no normalized transaction or occurrence, whether failure would otherwise throw or silently round, underflow, or overflow.
required_matrix:
- Valid ordinary and boundary representatives, so the fix cannot over-reject: zero and cent-exact values, trailing fractional zeros, inclusive maximum, and scientific notation that represents an exact in-range cent value.
- Invalid exceptional values: signed/unsigned NaN and signaling NaN spellings, positive and negative Infinity spellings, and negative zero spellings.
- Invalid exactness/range values: fractional cents, very long fractional tails, just-over-maximum values, huge positive exponents, tiny/subnormal/underflowing exponents, and long mantissas that exercise context independence.
- Token grammar cases: thousands/grouping separators, currency symbols/codes, locale decimal separators, underscores, empty and whitespace-only cells, leading/trailing spaces or tabs, embedded whitespace, malformed exponents, and non-ASCII digit variants.
- Scientific notation forms must include both valid exact/in-range representatives and invalid fractional-cent, over-range, underflow, and malformed representatives.
- Exercise both Debit and Credit paths, preserve the separate `missing_amount` behavior, and ensure every invalid token remains inspectable with no effective support.
review_deliverables:
- A documented table mapping every raw token to expected valid/invalid outcome and expected minor units when valid.
- One consolidated acceptance-test update covering the matrix; identify which assertions are red against e94a09a and which are green guardrails.
- A review-owned commit and exact test command/output evidence.
- A typed LOOP_STATUS handoff to product and data-eng. Product will use it to create the final iteration-4 FIX_REQUEST; review must not ask data-eng to implement before the matrix is complete.
policy:
- The human approved temporary `max_fix_cycles: 7` for iteration 4.
- Product must restore `max_fix_cycles: 3` immediately after ACCEPTED.
- No system dependency, OCR engine, network path, or unrelated feature is authorized.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-14T06:13:10Z
expected_reply:
- LOOP_STATUS with the complete matrix document, review-owned red-capable test commit, red/green case inventory, exact command evidence, and a data-eng-ready acceptance contract.
