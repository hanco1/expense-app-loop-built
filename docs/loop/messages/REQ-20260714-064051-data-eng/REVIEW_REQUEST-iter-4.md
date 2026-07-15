# REVIEW_REQUEST

message_type: REVIEW_REQUEST
request_id: REQ-20260714-064051-data-eng
parent_request_id:
iteration: 4
from_lane: data-eng
to_lane: review
status: REVIEWING
created_at: 2026-07-15T08:12:45Z
implementation_commit: 9268a5e
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/analysis-core.md
- docs/loop/messages/REQ-20260714-064051-data-eng/FIX_REQUEST-iter-4.md
- docs/loop/messages/REQ-20260714-064051-data-eng/IMPLEMENTATION_DONE-iter-4.md
- docs/review/REQ-20260714-064051-data-eng-iter-3-component-state-matrix.md
- docs/review/REQ-20260714-064051-data-eng-iter-4-write-boundary-matrix.md
- tests/acceptance/test_analysis_core_review.py
- tests/acceptance/test_analysis_core_write_boundary_review.py
artifact_scope:
- backend/analysis.py
- backend/persistence.py
- tests/backend/test_analysis_duplicates.py
- docs/data/analysis-core.md
- implementation commit 9268a5e
acceptance_criteria:
- The unchanged iteration-4 boundary command passes 145/145: all 144 executable paths plus the manifest guard, with all six unreachable classes unchanged.
- All 48 CoreStore-alias invalid ZK/MC/MM/AD paths reject atomically before ID allocation or history append, independent of support state; all 96 valid SP/SM and VS/BD/KR/LR guardrail paths remain green.
- The unchanged iteration-3 component-state command remains 56/56, preserving structural keeper, deterministic fallback, support transitions, history, provenance, and component isolation.
- Every public CoreStore import alias enforces the identical centralized latest-same graph rule inside one immediate transaction.
- Original C1-C7 focused commands, backend discovery, local/privacy boundary, exact monthly oracles, and completion gate remain green.
implementation_notes:
- `CoreStore.add_duplicate_decision()` now reads and overlays latest effective graph state, validates centrally, and only then allocates a decision ID and inserts one append-only row.
- `AnalysisService.set_duplicate_decision()` delegates to the store. Analysis reads use the same component projection helper.
- Backend regressions directly exercise all invalid and valid proposal families. None of the four frozen artifacts was modified.
frozen_artifacts:
- tests/acceptance/test_analysis_core_review.py: 01A02F973E884D3BA917FDF73260E6E5524F9D21B8D5DE77CDD57755989C6E6B
- docs/review/REQ-20260714-064051-data-eng-iter-3-component-state-matrix.md: ADB423E55F10058A556F551EECCC92CFCC998DFFC87D6FD003CF856B68FF61FB
- tests/acceptance/test_analysis_core_write_boundary_review.py: 974432935CBB3C8EB957297DA50E3FD52E1F877D1C5D9C3BBAFD4D16818D809B
- docs/review/REQ-20260714-064051-data-eng-iter-4-write-boundary-matrix.md: 91B1DFD3792A04DBD42E2847544896EB239594C7D9F7C2BAEAC1E4A26FCD421C
verification:
- `python -m unittest tests.acceptance.test_analysis_core_write_boundary_review -v`: exit 0, 145/145.
- `python -m unittest tests.acceptance.test_analysis_core_review -v`: exit 0, 56/56.
- `python -m unittest tests.backend.test_analysis_categories -v`: exit 0, 3/3.
- `python -m unittest tests.backend.test_analysis_corrections -v`: exit 0, 1/1.
- `python -m unittest tests.backend.test_analysis_duplicates -v`: exit 0, 6/6.
- `python -m unittest tests.backend.test_analysis_monthly -v`: exit 0, 1/1.
- `python -m unittest tests.backend.test_analysis_inclusion -v`: exit 0, 5/5.
- `python -m unittest tests.backend.test_analysis_contracts -v`: exit 0, 2/2.
- `python -m unittest tests.backend.test_analysis_local_boundary -v`: exit 0, 3/3.
- `python -m unittest discover -s tests/backend -p "test_*.py" -v`: exit 0, 52/52.
- `python completion_gate.py --loop-dir docs/loop --request-id REQ-20260714-064051-data-eng`: exit 0, SHIP_CHECK_OK.
evidence:
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-4-python-m-unittest-tests-acceptance-test-analysis-core-write-boundary-review-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-4-python-m-unittest-tests-acceptance-test-analysis-core-review-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-4-python-m-unittest-tests-backend-test-analysis-categories-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-4-python-m-unittest-tests-backend-test-analysis-corrections-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-4-python-m-unittest-tests-backend-test-analysis-duplicates-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-4-python-m-unittest-tests-backend-test-analysis-monthly-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-4-python-m-unittest-tests-backend-test-analysis-inclusion-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-4-python-m-unittest-tests-backend-test-analysis-contracts-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-4-python-m-unittest-tests-backend-test-analysis-local-boundary-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-4-python-m-unittest-discover-s-tests-backend-p-test-py-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-4-completion-gate.json
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-15T08:13:50Z
expected_reply:
- REVIEW_DONE PASS or blocker-severity FIX_REQUEST for the same request_id and iteration.
- Per-path frozen matrix result, four frozen hash checks, atomic rejection/history/fact/provenance/privacy assessment, ease-of-misuse answer, exact command exits, and review evidence path.
