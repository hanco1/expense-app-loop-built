# REVIEW_REQUEST

message_type: REVIEW_REQUEST
request_id: REQ-20260714-064051-data-eng
parent_request_id:
iteration: 1
from_lane: data-eng
to_lane: review
status: REVIEWING
created_at: 2026-07-14T06:55:38Z
implementation_commit: 8aa5b6f
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/analysis-core.md
- docs/loop/messages/REQ-20260714-064051-data-eng/IMPLEMENTATION_REQUEST-iter-1.md
- docs/loop/messages/REQ-20260714-064051-data-eng/IMPLEMENTATION_DONE-iter-1.md
artifact_scope:
- backend/**
- contracts/**
- tests/backend/**
- docs/data/**
- docs/loop/lanes/data-eng/**
acceptance_criteria:
- C1: every fixture transaction has the exact `mvp-1` automatic category and provenance; positive refund/income remain non-spending credits.
- C2: canonical category corrections are append-only/latest-wins; invalid values append nothing; effective state survives exact re-import, all-support undo, and later re-import.
- C3: duplicate decisions are append-only/latest-wins; pending includes both Tim Hortons identities, `same_transaction` excludes only non-kept, and later `distinct` restores both without deleting facts.
- C4: May is 50340 spending/60000 credits/12 transactions and June is 277617 spending/72999 credits/22 transactions, with every documented category amount exact and reconciled.
- C5: exact re-import is idempotent; undo changes analysis only after final support; credits and failed rows do not enter spending/aggregates; mixed currencies are rejected.
- C6: typed contracts expose deterministic months, summary rows/buckets, source supports, category provenance/history IDs, duplicate decisions/history, inclusion reasons, and contributing identity IDs.
- C7: all previous backend behavior remains green with no network, OCR, telemetry, subprocess, system dependency, raw-data logging, or fixture-hash change.
verification:
- python -m unittest tests.backend.test_analysis_categories -v
- python -m unittest tests.backend.test_analysis_corrections -v
- python -m unittest tests.backend.test_analysis_duplicates -v
- python -m unittest tests.backend.test_analysis_monthly -v
- python -m unittest tests.backend.test_analysis_inclusion -v
- python -m unittest tests.backend.test_analysis_contracts -v
- python -m unittest tests.backend.test_analysis_local_boundary -v
- python -m unittest discover -s tests/backend -p "test_*.py" -v
- python completion_gate.py --loop-dir docs/loop --request-id REQ-20260714-064051-data-eng
evidence:
- Nine flat JSON records prefixed `REQ-20260714-064051-data-eng-iter-1-` in `docs/loop/evidence/`; every record has exit_code 0.
- Backend discovery passed 45/45; fixture hashes and exact May/June/category oracles are recorded without raw financial content.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-14T06:57:02Z
expected_reply:
- REVIEW_DONE PASS or blocker-severity FIX_REQUEST.
- Per-criterion results, invariant/scope-creep/looks-done-but-wrong assessment, ease-of-misuse answer, exact command exits, and review evidence path.
