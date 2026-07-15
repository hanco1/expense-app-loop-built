# Local JSON Facade Decisions

## Application boundary

- `LocalWebApi` is an in-process dispatcher over `LocalWebRequest` and
  `LocalWebResponse`. It accepts method, path, text headers, and bytes and
  returns deterministic UTF-8 JSON bytes; it does not bind a socket or serve
  files.
- `LocalWebApi.from_database()` initializes a caller-provided local SQLite
  path. Recreating the facade over that path retains run discovery and every
  accepted core fact or human decision.
- A per-instance CSRF token is stable for the instance and is returned only by
  `GET /api/session`. Every `POST` is checked with constant-time comparison
  before dispatching a write. Mutations are serialized by an in-process lock;
  underlying writes still use the accepted service and SQLite transactions.

## Persistence and service reuse

- `CoreStore.list_import_run_summaries()` is the only new persistence query.
  It returns active, failed, and undone runs ordered by
  `(created_at DESC, run_id DESC)` with the same count fields as the single-run
  summary.
- Imports call `StatementImportService`, category and duplicate changes call
  `AnalysisService`, and run undo calls `CoreStore`. The facade does not copy
  parser, identity, correction, duplicate-component, aggregation, or undo
  rules.
- Run JSON removes `retained_input`. It exposes structured locators, parse
  errors, normalized facts, occurrence state, current duplicate decision, and
  effective inclusion reason. Duplicate JSON enriches each side with the
  normalized date, merchant, signed amount, currency, and inclusion state.

## JSON and errors

- Every minor-unit field is converted from its exact Python integer to a
  base-10 JSON string at the final serialization boundary. Counts remain JSON
  integers and currency remains explicit.
- Success envelopes contain only `data`; failures contain `error.code`,
  `error.message`, and `error.details`. Validation, missing, conflict,
  unsupported-media, oversized-upload, parser/import, and unexpected failures
  map to stable 400, 404, 409, 415, 413, 422, and 500 responses.
- Unexpected exceptions, parser exception text, tracebacks, retained source
  input, and raw request bodies are never returned or logged. Responses include
  `Cache-Control: no-store` and no permissive CORS header.

## Local boundary

- The facade uses the Python standard library and the accepted project-pinned
  `pypdf`; it adds no dependency.
- No listener, network client, OCR path, telemetry, subprocess, static assets,
  or frontend implementation is present in this slice.
