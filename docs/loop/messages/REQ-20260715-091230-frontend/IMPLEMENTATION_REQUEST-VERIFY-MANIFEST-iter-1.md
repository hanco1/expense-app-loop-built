# IMPLEMENTATION_REQUEST VERIFY Manifest Supplement

message_type: IMPLEMENTATION_REQUEST
request_id: REQ-20260715-091230-frontend
parent_request_id:
iteration: 1
from_lane: product
to_lane: review
status: REVIEWING
created_at: 2026-07-15T09:42:22Z
source_docs:
- docs/loop/messages/REQ-20260715-091230-frontend/IMPLEMENTATION_REQUEST-iter-1.md
- docs/product/local-web-app.md
purpose:
- Supply the protocol parser's literal backticked VERIFY manifest for the four commands already declared verbatim in the original request. This supplement changes no C1-C7 criterion, scope, implementation requirement, human-QA hold, command, or evidence expectation.
acceptance_criteria:
- C1-C6 frontend and browser behavior VERIFY `python -m unittest discover -s tests/frontend -p "test_*.py" -v`
- C6 real-browser fixture flow VERIFY `python -m unittest tests.frontend.test_browser_e2e -v`
- C7 backend regression VERIFY `python -m unittest discover -s tests/backend -p "test_*.py" -v`
- Completion gate VERIFY `python completion_gate.py --loop-dir docs/loop --request-id REQ-20260715-091230-frontend`
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: pending
- sent_at:
expected_reply:
- Review uses the unchanged C1-C7 contract, four committed root evidence records, and its separate review-owned red-capable acceptance. This supplement only repairs archived manifest syntax.
