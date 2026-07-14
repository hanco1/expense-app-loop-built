# REVIEW_REQUEST

message_type: REVIEW_REQUEST
request_id: REQ-20260714-064051-data-eng
parent_request_id:
iteration: 2
from_lane: data-eng
to_lane: review
status: REVIEWING
created_at: 2026-07-14T07:11:26Z
implementation_commit: 6b9378f
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/product/analysis-core.md
- docs/loop/messages/REQ-20260714-064051-data-eng/FIX_REQUEST-iter-2.md
- docs/loop/messages/REQ-20260714-064051-data-eng/IMPLEMENTATION_DONE-iter-2.md
- docs/review/REQ-20260714-064051-data-eng-iter-1.md
artifact_scope:
- backend/analysis.py
- tests/backend/test_analysis_duplicates.py
- docs/data/analysis-core.md
- implementation commit 6b9378f
acceptance_criteria:
- C1: fixture transactions retain exact `mvp-1` automatic categories and positive credits remain outside spending. VERIFY `python -m unittest tests.backend.test_analysis_categories -v`.
- C2: append-only latest-wins category corrections remain valid and survive undo/re-import. VERIFY `python -m unittest tests.backend.test_analysis_corrections -v`.
- C3: an active connected `same_transaction` component cannot lose every representative; the three-link cycle-closing decision is rejected before append, isolated pair semantics and audit/history behavior remain intact, and undo/re-import preserves accepted decisions. VERIFY `python -m unittest tests.acceptance.test_analysis_core_review -v` and `python -m unittest tests.backend.test_analysis_duplicates -v`.
- C4: exact May/June totals and category maps remain unchanged and reconciled. VERIFY `python -m unittest tests.backend.test_analysis_monthly -v`.
- C5: exact re-import, final-support undo, credit exclusion, failed rows, and currency guardrails remain correct. VERIFY `python -m unittest tests.backend.test_analysis_inclusion -v`.
- C6: typed deterministic traceable contracts remain complete. VERIFY `python -m unittest tests.backend.test_analysis_contracts -v`.
- C7: local-only boundaries and all backend regressions remain green. VERIFY `python -m unittest tests.backend.test_analysis_local_boundary -v` and `python -m unittest discover -s tests/backend -p "test_*.py" -v`.
- Completion gate: VERIFY `python completion_gate.py --loop-dir docs/loop --request-id REQ-20260714-064051-data-eng`.
implementation_notes:
- The safeguard validates the proposed latest-wins connected component before `CoreStore.add_duplicate_decision`, rejecting zero-representative state without appending a decision row.
- The backend regression covers three active identities/three links, zero rejected-history rows, one included representative, exact spending, retained facts, undo, and renamed exact re-import.
- `tests/acceptance/test_analysis_core_review.py` was not modified; its SHA-256 is 7FE5D30C0681FB54CF6366A69F707B30A58BCEE69E1999BE80DAFAC2C86B06FD.
verification:
- All ten iteration-2 commands exited 0; backend discovery passed 46/46 and the completion gate printed SHIP_CHECK_OK.
evidence:
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-2-python-m-unittest-tests-acceptance-test-analysis-core-review-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-2-python-m-unittest-tests-backend-test-analysis-categories-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-2-python-m-unittest-tests-backend-test-analysis-corrections-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-2-python-m-unittest-tests-backend-test-analysis-duplicates-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-2-python-m-unittest-tests-backend-test-analysis-monthly-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-2-python-m-unittest-tests-backend-test-analysis-inclusion-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-2-python-m-unittest-tests-backend-test-analysis-contracts-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-2-python-m-unittest-tests-backend-test-analysis-local-boundary-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-2-python-m-unittest-discover-s-tests-backend-p-test-py-v.json
- docs/loop/evidence/REQ-20260714-064051-data-eng-iter-2-completion-gate.json
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-14T07:12:32Z
expected_reply:
- REVIEW_DONE PASS or blocker-severity FIX_REQUEST for the same request_id and iteration.
- Per-criterion results, invariant/scope-creep/looks-done-but-wrong assessment, ease-of-misuse answer, exact command exits, and review evidence path.
