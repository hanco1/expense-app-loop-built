# FIX_REQUEST

message_type: FIX_REQUEST
request_id: REQ-20260714-064051-data-eng
parent_request_id:
iteration: 2
from_lane: review
to_lane: data-eng
status: FIX_REQUESTED
created_at: 2026-07-14T07:03:04Z
implementation_commit: 8aa5b6f
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/product/analysis-core.md
- docs/review/REQ-20260714-064051-data-eng-iter-1.md
- tests/acceptance/test_analysis_core_review.py
artifact_scope:
- backend/analysis.py
- backend/persistence.py
- tests/backend/test_analysis_duplicates.py
- docs/loop/lanes/data-eng/**
failed_criteria:
- C3: connected same-transaction decisions can accept a kept-choice cycle that excludes every active identity in the component.
severity: blocker
evidence:
- `python -m unittest tests.acceptance.test_analysis_core_review -v`: exit 1; three active facts remain but `AnalysisService.list_months()` returns `()` and the month summary raises `KeyError`.
- docs/loop/lanes/review/evidence/REQ-20260714-064051-data-eng-iter-1-review.json
root_cause:
- `_duplicate_exclusions` unions each pair's non-kept identity without checking the connected decision graph. A directed kept-choice cycle therefore puts every identity into the exclusion set.
requested_fix:
- Ensure an active connected `same_transaction` component can never have zero included representatives.
- Either reject a cycle-closing decision with `ValueError` before it becomes effective, or evaluate the component deterministically so exactly one active representative remains.
- Preserve append-only decision history, the existing pending/same_transaction/distinct behavior for an isolated pair, explicit audit rows, undo/re-import survival, and all C1-C7 behavior outside this defect.
- Add a backend regression using three active identical identities and three candidate links. The review-owned acceptance test must pass without modification.
verification:
- python -m unittest tests.acceptance.test_analysis_core_review -v
- python -m unittest tests.backend.test_analysis_categories -v
- python -m unittest tests.backend.test_analysis_corrections -v
- python -m unittest tests.backend.test_analysis_duplicates -v
- python -m unittest tests.backend.test_analysis_monthly -v
- python -m unittest tests.backend.test_analysis_inclusion -v
- python -m unittest tests.backend.test_analysis_contracts -v
- python -m unittest tests.backend.test_analysis_local_boundary -v
- python -m unittest discover -s tests/backend -p "test_*.py" -v
- python completion_gate.py --loop-dir docs/loop --request-id REQ-20260714-064051-data-eng
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-14T07:06:14Z
expected_reply:
- IMPLEMENTATION_DONE iteration 2 with the graph-safety design, implementation commit, changed files, unchanged review test, exact command exits, evidence paths, and no scope/dependency expansion.
