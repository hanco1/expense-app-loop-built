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

Statement imports now begin in the non-effective `importing` state and become
`active` only after every persistence step succeeds. An unexpected parser or
persistence exception atomically excludes any introduced occurrences, marks the
run `failed`, and raises `StatementImportFailure` with the inspectable `run_id`.
If failure cleanup itself cannot finish, the original `importing` state still
cannot support an effective transaction. Parsed source records without a
completed occurrence report `persistence_incomplete` instead of a parse error.

CSV amounts are validated against SQLite's signed 64-bit integer range before
normalization. An out-of-range amount remains a failed source record with
`invalid_amount`; public money persistence methods also reject integers outside
that range before SQLite binding.

Amount conversion uses one whole-token ASCII decimal whitelist and exact string/
integer structure rather than `Decimal`. It derives the coefficient, fractional
digit count, and a bounded exponent; nonzero values must reduce exactly to cents
and fit `0..9223372036854775807`, while zero remains zero for any exponent size.
Debit negation happens only after unsigned validation. Every other nonblank token
is retained as one `invalid_amount` record without a transaction or occurrence;
blank-cell `missing_amount` and two-present-cell `ambiguous_amount` remain distinct.

Run summary returns source metadata and parsed/failed/occurrence counts. Run
detail returns every retained source record, parse result, normalized transaction,
identity, source fingerprint, suspected-duplicate state, and inclusion reason.
Each effective transaction includes every active supporting run, occurrence,
fingerprint, and locator. Statement provenance adds the same normalized and
duplicate state to the existing core trace fields.
