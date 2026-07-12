# IMPLEMENTATION_REQUEST

message_type: IMPLEMENTATION_REQUEST
request_id: REQ-20260712-200417-data-eng
parent_request_id:
iteration: 1
from_lane: product
to_lane: data-eng
status: REQUESTED
created_at: 2026-07-12T20:04:17Z
source_docs:
- docs/loop/goal.md
- docs/loop/tracker.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/core-foundation.md
design_system:
- none; this is a non-UI request and the human disabled optional skills
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-12T20:06:02Z
goal: Implement the local SQLite-backed core data foundation for safe, reversible imports before adding any PDF/CSV parser or UI.
user_facing: false
scope:
- backend/**
- tests/backend/**
- docs/data/**
- docs/loop/lanes/data-eng/**
- docs/loop/messages/REQ-20260712-200417-data-eng/**
- docs/loop/evidence/**
non_goals:
- Do not implement PDF or CSV parsing, HTTP APIs, categorization rules, monthly aggregation, frontend code, charts, OCR, authentication, or cloud/network integration.
- Do not use or request real financial data; use deterministic synthetic fixtures only.
- Do not install a system dependency or add a network-capable service.
invariants:
- INV-1 no silent data loss and INV-3 add-only ingest: VERIFY `python -m unittest tests.backend.test_ingest_invariants -v` (fails if an invalid source row disappears, an existing source record is overwritten, or undo physically deletes it).
- INV-2 human edits outrank automation and INV-4 recoverable run units: VERIFY `python -m unittest tests.backend.test_import_runs -v` (fails if a run cannot list its introduced records, cannot be undone as a unit, or correction history is lost across undo and re-import).
- INV-6 traceability: VERIFY `python -m unittest tests.backend.test_traceability -v` (fails if an occurrence cannot identify its run, source fingerprint, source locator, transaction identity, and inclusion state).
- INV-7 exact money: VERIFY `python -m unittest tests.backend.test_money -v` (fails if a binary float is accepted, currency is absent, or minor units change on round-trip).
- INV-8 local privacy: VERIFY `python -m unittest tests.backend.test_local_boundary -v` (fails if core persistence attempts a network socket, logs retained source content, or writes outside the provided local database path).
- INV-5 no double counting is not yet exercised because this slice creates identity and occurrence primitives but does not compute monthly results; it remains binding for the later deduplication/aggregation slice.
acceptance_criteria:
- A fresh local SQLite database can initialize the required import-run, source-record, stable-identity, occurrence, and manual-correction persistence model. VERIFY `python -m unittest tests.backend.test_schema -v` (fails on a missing entity, relationship, or uniqueness constraint).
- Two imports receive distinct opaque `run_id` values and each run lists exactly its own introduced source records and occurrences. VERIFY `python -m unittest tests.backend.test_import_runs -v` (fails on an ID collision, cross-run leakage, or incorrect membership).
- Undo is state-based and atomic: every occurrence from the selected run becomes excluded without deleting the run, source records, identities, or manual-correction history; re-import links the stable identity to preserved corrections. VERIFY `python -m unittest tests.backend.test_import_runs -v` (fails on partial undo, physical deletion, or lost corrections).
- Invalid/unparsed synthetic input remains stored with an explicit failure state and error code. VERIFY `python -m unittest tests.backend.test_ingest_invariants -v` (fails if the record is missing or lacks inspectable failure state).
- Money round-trips as integer minor units with explicit original currency, and public persistence APIs reject binary float amounts. VERIFY `python -m unittest tests.backend.test_money -v` (fails on rounding drift, missing currency, or accepted float input).
- Every occurrence can produce structured provenance without exposing raw content in logs. VERIFY `python -m unittest tests.backend.test_traceability -v` (fails when run/source/locator/identity/inclusion fields are absent) and `python -m unittest tests.backend.test_local_boundary -v` (fails when retained source content reaches logs).
- The entire backend suite passes. VERIFY `python -m unittest discover -s tests/backend -p "test_*.py" -v` (fails on any regression).
expected_reply:
- changed_files
- schema and API decisions
- exact verification commands, exit codes, and evidence paths
- blockers, if any
- IMPLEMENTATION_DONE followed by REVIEW_REQUEST to the registered review lane when all evidence is green
