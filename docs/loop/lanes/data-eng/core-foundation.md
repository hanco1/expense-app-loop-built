# Core persistence foundation

The core is a Python 3.12 standard-library module backed by one caller-provided
SQLite file. It performs no network calls, creates no parent directories, and
does not log retained source content.

## Persistence model

- `import_runs` gives every import an opaque `run_id`, source fingerprint, and
  explicit `active` or `undone` state.
- `source_records` retains one immutable input representation and parse result
  per run locator. Failed input requires an inspectable error code.
- `transaction_identities` maps a unique stable fingerprint to an immutable
  identity independent of import runs.
- `imported_occurrences` links one source record and run to one stable identity,
  stores integer minor units plus a three-letter uppercase currency, and uses
  inclusion state instead of deletion.
- `manual_corrections` is append-only and belongs to a stable identity, so its
  history survives undo and re-import.

Foreign keys and uniqueness constraints enforce run/source membership. Triggers
prevent deletion of domain entities and mutation of source, identity, money, and
correction facts. Undo is a single SQLite transaction that excludes every
occurrence in the run and marks the run undone; any failure rolls back the whole
operation.

## Public API

`backend.persistence.CoreStore` initializes a database and exposes focused
methods to create and inspect runs, retain source records, get or create stable
identities, add occurrences and manual corrections, undo a run, and retrieve
structured occurrence provenance. It intentionally contains no parser,
categorizer, aggregator, HTTP, OCR, or UI boundary.

Amounts passed to `add_occurrence` must have Python type `int`; floats and
booleans are rejected before SQLite is called. Currency is mandatory and must
have the uppercase three-letter ISO shape. Provenance deliberately omits retained
input content.
