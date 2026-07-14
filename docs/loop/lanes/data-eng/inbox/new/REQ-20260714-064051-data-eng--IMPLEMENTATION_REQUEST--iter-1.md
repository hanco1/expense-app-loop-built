# IMPLEMENTATION_REQUEST

message_type: IMPLEMENTATION_REQUEST
request_id: REQ-20260714-064051-data-eng
parent_request_id:
iteration: 1
from_lane: product
to_lane: data-eng
status: REQUESTED
created_at: 2026-07-14T06:40:51Z
user_facing: false
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/core-foundation.md
- docs/product/import-pipeline.md
- docs/product/analysis-core.md
artifact_scope:
- backend/**
- contracts/**
- tests/backend/**
- docs/data/**
- docs/loop/lanes/data-eng/**
purpose:
- Add deterministic automatic categories, append-only human category and duplicate decisions, exact monthly aggregation, and stable local service contracts for the later browser UI.
implementation_requirements:
- Implement the exact canonical vocabulary, `mvp-1` category rules, duplicate-decision semantics, monthly arithmetic, traceability fields, and typed service surface in `docs/product/analysis-core.md`.
- Human corrections and duplicate decisions are append-only, latest-wins deterministically, survive undo/re-import/reprocessing, and never mutate retained source or normalized facts.
- Monthly spending is the positive magnitude of included negative CAD transactions only. Positive Amazon refund and E-Transfer income remain visible credits and contribute zero to spending.
- Preserve exact-reimport idempotency, legitimate Tim Hortons lookalikes, run undo, source provenance, local-only privacy, and every accepted prior invariant.
scope:
- backend/analysis.py or an equivalently focused local analysis service
- compatible persistence additions in backend/persistence.py
- typed contracts in contracts/**
- focused backend tests and data-eng lane records
non_goals:
- HTTP server or endpoints
- browser UI or pie-chart rendering
- OCR, scanned receipts, network, telemetry, cloud services, subprocesses, or system dependencies
- ML categorization, custom category creation, budgets, exchange rates, or financial advice
acceptance_criteria:
- Criterion C1: every fixture transaction receives the exact `mvp-1` automatic category and category provenance; positive refund/income categories are visible but never spending. Red-capable verify: `python -m unittest tests.backend.test_analysis_categories -v`.
- Criterion C2: canonical human category corrections are append-only/latest-wins, invalid categories append nothing, and the effective correction survives exact re-import, complete undo, and later re-import. Red-capable verify: `python -m unittest tests.backend.test_analysis_corrections -v`.
- Criterion C3: duplicate decisions are append-only/latest-wins; the Tim Hortons pair starts pending with both included, `same_transaction` excludes only the non-kept identity from analysis, and a later `distinct` restores both without deleting facts. Red-capable verify: `python -m unittest tests.backend.test_analysis_duplicates -v`.
- Criterion C4: fixture month summaries exactly equal May 50340 spending/60000 credits/12 transactions and June 277617 spending/72999 credits/22 transactions, with every category amount matching the oracle and category sums reconciling exactly. Red-capable verify: `python -m unittest tests.backend.test_analysis_monthly -v`.
- Criterion C5: exact re-import does not change month totals/counts; undo affects a transaction only after its final active support is gone; credits never enter spending; failed rows never enter aggregates. Red-capable verify: `python -m unittest tests.backend.test_analysis_inclusion -v`.
- Criterion C6: typed contracts expose stable months, summary, transaction/category provenance, correction history, duplicate decisions, inclusion reasons, and contributing identity IDs in deterministic order. Red-capable verify: `python -m unittest tests.backend.test_analysis_contracts -v`.
- Criterion C7: all prior backend behavior remains green and the slice adds no network/OCR/telemetry/subprocess/system-dependency or raw-data logging surface. Red-capable verify: `python -m unittest tests.backend.test_analysis_local_boundary -v` plus backend discovery.
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
evidence_requirements:
- One flat JSON evidence record per verification command under docs/loop/evidence/, all bound to this request_id and iteration 1.
- Report exact May/June totals, category maps, correction/duplicate history assertions, test counts, exit codes, and unchanged fixture hashes without logging raw financial data beyond the approved synthetic assertions.
dependencies:
- No dependency is expected. A pip-only project package may follow policy; stop and ask the human before any system-level installation.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: pending
- sent_at:
expected_reply:
- IMPLEMENTATION_DONE with implementation commit, changed files, schema/API decisions, exact verification commands and exit codes, flat evidence paths, dependency statement, and blockers.
- Then REVIEW_REQUEST to the verified review thread using the same request_id and iteration.
