# Evidence

Completion-gate evidence lives here. Store one JSON record per verification
command so `SHIP_CHECK_OK` can be justified from repo files alone.

## File contract (flat, one JSON object per command)

Write one file per verification command directly in this directory, named:

```text
docs/loop/evidence/<request_id>-iter-<n>-<command>.json
```

`<command>` is slugified: lowercase it and replace every run of non-alphanumeric
characters with a single `-` (for example `npm test` -> `npm-test`,
`pytest -q` -> `pytest-q`). `<n>` is the request's current iteration.

Each file is a single JSON object with exactly these five fields:

```json
{
  "request_id": "REQ-20260623-101500-implementation",
  "checkpoint": "mvp-color-match",
  "command": "npm test",
  "exit_code": 0,
  "ran_at": "2026-06-23T11:00:00Z"
}
```

All five fields are required. Record the real process exit code; never
normalize a non-zero exit to `0`. A checkpoint is only verified when every
record for the request reports `exit_code` 0.

## Warning: the gate reads this directory with a NON-RECURSIVE glob

The completion gate collects evidence with `glob('*.json')` on this directory
only. It does not recurse. Consequences:

- A file in a subdirectory (for example `evidence/<subdir>/foo.json`) is
  INVISIBLE to the gate. Do not nest evidence under per-request folders.
- A non-JSON file (for example a `.txt` transcript) is INVISIBLE to the gate.
  Capture the exit code in the JSON record above, not in a side `.txt` file.

Keep every evidence record as a flat `*.json` file in this directory, or the
gate will not count it.
