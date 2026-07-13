# Bounded statement import pipeline

## Input and parser boundary

`StatementImportService.import_bytes` accepts local `bytes`, a display filename,
and an explicit `csv` or `pdf` type. It never opens a caller path. Parsers conform
to the `contracts.statement_import.StatementParser` text-parser protocol. The PDF
implementation uses the project-level `pypdf` dependency and exposes no scanned
image or system-process path.

## Identity and duplicate decisions

- Every call creates a new opaque run and stores source name, type, SHA-256
  content fingerprint, and an explicit link to the first exact import when one
  exists.
- Stable transaction identity hashes the content fingerprint plus source
  locator. File renames therefore preserve identity, while two equal-looking
  rows at different locators remain distinct.
- Normalized transaction facts are immutable and attached to stable identity.
- Equal date, merchant, signed amount, and currency across distinct identities
  creates an inspectable `suspected_pending` link. It does not exclude either
  identity.

## Effective and run-query decisions

An effective transaction is one stable identity with at least one included
occurrence belonging to an active run. Exact re-import adds support without
adding an effective identity. Undo removes only the selected run's support and
retains runs, source records, normalized facts, occurrences, suspected links,
and correction history.

Run summary returns source metadata and parsed/failed/occurrence counts. Run
detail returns every retained source record, parse result, normalized transaction,
identity, source fingerprint, suspected-duplicate state, and inclusion reason.
Each effective transaction includes every active supporting run, occurrence,
fingerprint, and locator. Statement provenance adds the same normalized and
duplicate state to the existing core trace fields.
