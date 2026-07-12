# Core Foundation Slice

## Purpose

Establish the smallest local persistence model that makes later PDF/CSV ingestion safe: immutable source records, stable transaction identity, run-scoped occurrences, independent human corrections, exact money, and reversible import runs.

## Required Domain Shape

- `ImportRun`: opaque unique `run_id`, creation time, source fingerprint, and explicit active/undone state.
- `SourceRecord`: append-only source occurrence tied to one run, with source locator, retained input representation, parse status, and error state.
- `TransactionIdentity`: stable identity/fingerprint representing a possible real-world transaction independently of a particular import occurrence.
- `ImportedOccurrence`: link between a source record, its run, and a transaction identity; undo changes inclusion state without physical deletion.
- `ManualCorrection`: append-only human decision linked to stable transaction identity so it survives undo and later re-import.
- Money values use integer minor units plus an explicit ISO currency code. No binary floating-point storage or implicit conversion.

## Local Boundary

- Use Python 3.12 standard library and SQLite for this slice.
- Runtime database files remain ignored by Git.
- Synthetic test data only; do not request, inspect, copy, or commit a real statement.
- No network client, telemetry, cloud API, or system-level dependency.
