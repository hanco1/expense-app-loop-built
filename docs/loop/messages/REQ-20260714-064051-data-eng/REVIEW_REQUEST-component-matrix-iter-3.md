# REVIEW_REQUEST

message_type: REVIEW_REQUEST
request_id: REQ-20260714-064051-data-eng
parent_request_id:
iteration: 3
from_lane: product
to_lane: review
status: FIX_REQUESTED
phase: pre_implementation_component_state_matrix
created_at: 2026-07-14T17:55:58Z
implementation_commit: 6b9378f
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/analysis-core.md
- docs/review/REQ-20260714-064051-data-eng-iter-2.md
- docs/loop/messages/REQ-20260714-064051-data-eng/BLOCKED-review-support-transition-iter-2.md
artifact_scope:
- tests/acceptance/test_analysis_core_review.py
- docs/review/REQ-20260714-064051-data-eng-iter-3-component-state-matrix.md
- docs/loop/lanes/review/**
human_direction:
- Freeze the complete `same_transaction` component-state by state-changing-operation matrix before data-eng begins iteration 3. Do not report one new state transition per later round.
- Define one component-level invariant: every `same_transaction` connected component with at least one active identity must always have at least one included active kept representative.
- Existing INV-5 remains the upper bound: a component representing one real transaction must not be double-counted. The combined expected effective state is exactly one included active representative whenever the component has active identities, and zero when none are active.
- Prefer the human-designated keeper while it is active. If it has no active support, choose one deterministic active fallback without rewriting or deleting append-only decision history. When keeper support returns, the human-designated keeper resumes.
- The implementation must use one centralized component-state projection/validation rule across all state-changing paths, preferably at the write boundary; scattered operation-specific patches are not acceptable.
required_matrix_axes:
- Component topology: isolated pair, three-identity chain, three-identity cycle/triangle, component merge by a new suspected link, component split by latest `distinct`, and multiple disconnected components to prove isolation.
- Active-support state: all identities active; only designated keeper active; keeper inactive with one other active; keeper inactive with multiple active; one identity with multiple supporting runs and partial/final support loss; all identities inactive; support later restored.
- Effective decision state: pending, `same_transaction`, `distinct`, latest-wins transitions among them, keeper changes, conflicting edge choices, and rejected cycle-closing proposals with zero appended history.
- State-changing operation: append/import a new source identity or support; create/accept a suspected duplicate link; append a human same/distinct/keeper redecision; undo one run; undo final support; exact re-import; renamed exact re-import; restore keeper support; and operations on a disconnected component.
- Sequence obligations: exercise each relevant operation from every compatible pre-state, including transitions that merge or split components. Record which combinations are impossible and why rather than silently omitting them.
expected_assertions_per_case:
- Active identity set, effective included representative set, and exactly-one/zero cardinality.
- Deterministic fallback identity and restoration of the human-designated keeper when its support returns.
- Append-only decision-history length and IDs: fallback/support changes do not create, mutate, or delete human decisions; rejected decisions append nothing.
- Exact month presence, transaction count, spending/category totals, audit-row inclusion reason, duplicate provenance, and active run/source supports.
- No silent fact loss, no double counting, no mutation/deletion of retained facts, and no cross-component effect.
review_deliverables:
- A frozen document containing a stable case ID for every compatible matrix cell, its pre-state, operation, expected post-state, and named invariant/criterion.
- One consolidated data-driven acceptance update covering the complete matrix. Identify every assertion that is red against `6b9378f` and every green guardrail.
- A review-owned commit and structured evidence for the exact command `python -m unittest tests.acceptance.test_analysis_core_review -v`.
- A typed LOOP_STATUS handoff to product with the frozen artifact hashes, total path count, red/green inventory, and a data-eng-ready acceptance contract. Review must not dispatch implementation.
acceptance_criteria:
- The matrix covers every compatible cross-product of topology/support/decision state and state-changing operation, with impossible cells explicitly justified; the document and acceptance test are frozen before implementation.
- `python -m unittest tests.acceptance.test_analysis_core_review -v` exits non-zero against `6b9378f` for every currently unsafe operation family while all previously safe cells remain green guardrails.
- Every matrix cell asserts the component-level lower bound, INV-5 upper bound, deterministic fallback/restoration, append-only history, exact aggregation, provenance, and cross-component isolation where applicable.
- No data-eng implementation starts and no matrix case changes after the review-owned freeze commit; product alone converts the frozen contract into the single authoritative iteration-3 FIX_REQUEST.
policy:
- The human approved temporary `max_fix_cycles: 5` for iteration 3.
- This BLOCKED to FIX_REQUESTED transition raises the raw count to 4/5. Do not add a same-status FIX_REQUESTED run-log row; the only remaining counted transition is data-eng's later `FIX_REQUESTED -> IMPLEMENTING`, reaching 5/5.
- Product must restore `max_fix_cycles: 3` immediately after ACCEPTED.
- No system dependency, OCR engine, network path, UI work, or unrelated feature is authorized.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-14T17:57:45Z
expected_reply:
- LOOP_STATUS with the frozen matrix document, consolidated review-owned red-capable test commit, total/compatible/impossible case counts, red/green inventory, artifact hashes, exact command evidence, and the data-eng-ready acceptance contract.
