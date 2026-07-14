# IMPLEMENTATION_REQUEST VERIFY Manifest Supplement

message_type: IMPLEMENTATION_REQUEST
request_id: REQ-20260714-064051-data-eng
parent_request_id:
iteration: 1
from_lane: product
to_lane: data-eng
status: REVIEWING
created_at: 2026-07-14T07:00:15Z
source_docs:
- docs/loop/messages/REQ-20260714-064051-data-eng/IMPLEMENTATION_REQUEST-iter-1.md
- docs/product/analysis-core.md
purpose:
- Supply the protocol parser's literal backticked VERIFY manifest for the nine commands already declared verbatim in the original request. This supplement changes no criterion, scope, implementation requirement, or evidence expectation.
acceptance_criteria:
- C1 VERIFY `python -m unittest tests.backend.test_analysis_categories -v`
- C2 VERIFY `python -m unittest tests.backend.test_analysis_corrections -v`
- C3 VERIFY `python -m unittest tests.backend.test_analysis_duplicates -v`
- C4 VERIFY `python -m unittest tests.backend.test_analysis_monthly -v`
- C5 VERIFY `python -m unittest tests.backend.test_analysis_inclusion -v`
- C6 VERIFY `python -m unittest tests.backend.test_analysis_contracts -v`
- C7 local-boundary VERIFY `python -m unittest tests.backend.test_analysis_local_boundary -v`
- C7 regression VERIFY `python -m unittest discover -s tests/backend -p "test_*.py" -v`
- Completion gate VERIFY `python completion_gate.py --loop-dir docs/loop --request-id REQ-20260714-064051-data-eng`
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-14T07:01:37Z
expected_reply:
- Review uses the unchanged C1-C7 contract and existing nine evidence records; this supplement only repairs manifest syntax.
