from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from os import PathLike
from pathlib import Path
from typing import Any
from uuid import uuid4


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS import_runs (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    source_fingerprint TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'active'
        CHECK (state IN ('active', 'undone'))
);

CREATE TABLE IF NOT EXISTS source_records (
    source_record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    retained_input TEXT NOT NULL,
    parse_status TEXT NOT NULL
        CHECK (parse_status IN ('parsed', 'failed')),
    error_code TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (run_id, source_locator),
    UNIQUE (source_record_id, run_id),
    CHECK (
        (parse_status = 'parsed' AND error_code IS NULL)
        OR
        (parse_status = 'failed' AND error_code IS NOT NULL AND length(error_code) > 0)
    ),
    FOREIGN KEY (run_id) REFERENCES import_runs(run_id)
);

CREATE TABLE IF NOT EXISTS transaction_identities (
    identity_id TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS imported_occurrences (
    occurrence_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    source_record_id TEXT NOT NULL UNIQUE,
    identity_id TEXT NOT NULL,
    amount_minor INTEGER NOT NULL
        CHECK (typeof(amount_minor) = 'integer'),
    currency TEXT NOT NULL
        CHECK (length(currency) = 3 AND currency GLOB '[A-Z][A-Z][A-Z]'),
    inclusion_state TEXT NOT NULL DEFAULT 'included'
        CHECK (inclusion_state IN ('included', 'excluded')),
    exclusion_reason TEXT,
    created_at TEXT NOT NULL,
    CHECK (
        (inclusion_state = 'included' AND exclusion_reason IS NULL)
        OR
        (inclusion_state = 'excluded' AND exclusion_reason IS NOT NULL)
    ),
    FOREIGN KEY (run_id) REFERENCES import_runs(run_id),
    FOREIGN KEY (source_record_id, run_id)
        REFERENCES source_records(source_record_id, run_id),
    FOREIGN KEY (identity_id) REFERENCES transaction_identities(identity_id)
);

CREATE TABLE IF NOT EXISTS manual_corrections (
    correction_id TEXT PRIMARY KEY,
    identity_id TEXT NOT NULL,
    correction_type TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (identity_id) REFERENCES transaction_identities(identity_id)
);

CREATE INDEX IF NOT EXISTS idx_source_records_run
    ON source_records(run_id, created_at, source_record_id);
CREATE INDEX IF NOT EXISTS idx_occurrences_run
    ON imported_occurrences(run_id, created_at, occurrence_id);
CREATE INDEX IF NOT EXISTS idx_corrections_identity
    ON manual_corrections(identity_id, created_at, correction_id);

CREATE TRIGGER IF NOT EXISTS import_runs_no_delete
BEFORE DELETE ON import_runs
BEGIN
    SELECT RAISE(ABORT, 'import runs are retained');
END;

CREATE TRIGGER IF NOT EXISTS import_runs_immutable_fields
BEFORE UPDATE ON import_runs
WHEN NEW.run_id IS NOT OLD.run_id
    OR NEW.created_at IS NOT OLD.created_at
    OR NEW.source_fingerprint IS NOT OLD.source_fingerprint
BEGIN
    SELECT RAISE(ABORT, 'import run identity is immutable');
END;

CREATE TRIGGER IF NOT EXISTS import_runs_no_reactivate
BEFORE UPDATE OF state ON import_runs
WHEN OLD.state = 'undone' AND NEW.state != 'undone'
BEGIN
    SELECT RAISE(ABORT, 'undone import runs are terminal');
END;

CREATE TRIGGER IF NOT EXISTS source_records_require_active_run
BEFORE INSERT ON source_records
WHEN (SELECT state FROM import_runs WHERE run_id = NEW.run_id) != 'active'
BEGIN
    SELECT RAISE(ABORT, 'source records require an active import run');
END;

CREATE TRIGGER IF NOT EXISTS source_records_no_update
BEFORE UPDATE ON source_records
BEGIN
    SELECT RAISE(ABORT, 'source records are append-only');
END;

CREATE TRIGGER IF NOT EXISTS source_records_no_delete
BEFORE DELETE ON source_records
BEGIN
    SELECT RAISE(ABORT, 'source records are retained');
END;

CREATE TRIGGER IF NOT EXISTS transaction_identities_no_update
BEFORE UPDATE ON transaction_identities
BEGIN
    SELECT RAISE(ABORT, 'transaction identities are immutable');
END;

CREATE TRIGGER IF NOT EXISTS transaction_identities_no_delete
BEFORE DELETE ON transaction_identities
BEGIN
    SELECT RAISE(ABORT, 'transaction identities are retained');
END;

CREATE TRIGGER IF NOT EXISTS occurrences_immutable_fields
BEFORE UPDATE ON imported_occurrences
WHEN NEW.occurrence_id IS NOT OLD.occurrence_id
    OR NEW.run_id IS NOT OLD.run_id
    OR NEW.source_record_id IS NOT OLD.source_record_id
    OR NEW.identity_id IS NOT OLD.identity_id
    OR NEW.amount_minor IS NOT OLD.amount_minor
    OR NEW.currency IS NOT OLD.currency
    OR NEW.created_at IS NOT OLD.created_at
BEGIN
    SELECT RAISE(ABORT, 'occurrence facts are immutable');
END;

CREATE TRIGGER IF NOT EXISTS occurrences_require_active_run
BEFORE INSERT ON imported_occurrences
WHEN (SELECT state FROM import_runs WHERE run_id = NEW.run_id) != 'active'
BEGIN
    SELECT RAISE(ABORT, 'occurrences require an active import run');
END;

CREATE TRIGGER IF NOT EXISTS occurrences_no_delete
BEFORE DELETE ON imported_occurrences
BEGIN
    SELECT RAISE(ABORT, 'occurrences are retained');
END;

CREATE TRIGGER IF NOT EXISTS manual_corrections_no_update
BEFORE UPDATE ON manual_corrections
BEGIN
    SELECT RAISE(ABORT, 'manual corrections are append-only');
END;

CREATE TRIGGER IF NOT EXISTS manual_corrections_no_delete
BEFORE DELETE ON manual_corrections
BEGIN
    SELECT RAISE(ABORT, 'manual corrections are retained');
END;
"""


class CoreStore:
    """SQLite-backed, local-only persistence for reversible import primitives."""

    def __init__(self, database_path: str | PathLike[str]) -> None:
        if not isinstance(database_path, (str, PathLike)):
            raise TypeError("database_path must be a filesystem path")
        self.database_path = Path(database_path)
        if not self.database_path.parent.is_dir():
            raise FileNotFoundError(
                f"database parent directory does not exist: {self.database_path.parent}"
            )
        if self.database_path.exists() and not self.database_path.is_file():
            raise ValueError("database_path must identify a file")

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(SCHEMA)

    def create_import_run(self, source_fingerprint: str) -> str:
        self._require_nonempty_text(source_fingerprint, "source_fingerprint")
        run_id = self._new_id("run")
        with self._connection() as connection, connection:
            connection.execute(
                "INSERT INTO import_runs "
                "(run_id, created_at, source_fingerprint, state) "
                "VALUES (?, ?, ?, 'active')",
                (run_id, self._now(), source_fingerprint),
            )
        return run_id

    def get_import_run(self, run_id: str) -> dict[str, Any]:
        return self._fetch_one(
            "SELECT run_id, created_at, source_fingerprint, state "
            "FROM import_runs WHERE run_id = ?",
            (run_id,),
            entity="import run",
        )

    def add_source_record(
        self,
        run_id: str,
        *,
        source_locator: str,
        retained_input: str,
        parse_status: str,
        error_code: str | None = None,
    ) -> str:
        self._require_nonempty_text(run_id, "run_id")
        self._require_nonempty_text(source_locator, "source_locator")
        if not isinstance(retained_input, str):
            raise TypeError("retained_input must be text")
        if parse_status not in {"parsed", "failed"}:
            raise ValueError("parse_status must be 'parsed' or 'failed'")
        if parse_status == "failed":
            self._require_nonempty_text(error_code, "error_code")
        elif error_code is not None:
            raise ValueError("a parsed source record cannot have an error_code")

        source_record_id = self._new_id("src")
        with self._connection() as connection, connection:
            connection.execute(
                "INSERT INTO source_records "
                "(source_record_id, run_id, source_locator, retained_input, "
                "parse_status, error_code, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    source_record_id,
                    run_id,
                    source_locator,
                    retained_input,
                    parse_status,
                    error_code,
                    self._now(),
                ),
            )
        return source_record_id

    def get_source_record(self, source_record_id: str) -> dict[str, Any]:
        return self._fetch_one(
            "SELECT source_record_id, run_id, source_locator, retained_input, "
            "parse_status, error_code, created_at FROM source_records "
            "WHERE source_record_id = ?",
            (source_record_id,),
            entity="source record",
        )

    def list_source_records(self, run_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            "SELECT source_record_id, run_id, source_locator, retained_input, "
            "parse_status, error_code, created_at FROM source_records "
            "WHERE run_id = ? ORDER BY created_at, source_record_id",
            (run_id,),
        )

    def get_or_create_identity(self, fingerprint: str) -> str:
        self._require_nonempty_text(fingerprint, "fingerprint")
        with self._connection() as connection, connection:
            row = connection.execute(
                "SELECT identity_id FROM transaction_identities WHERE fingerprint = ?",
                (fingerprint,),
            ).fetchone()
            if row is not None:
                return str(row["identity_id"])
            identity_id = self._new_id("txn")
            connection.execute(
                "INSERT INTO transaction_identities "
                "(identity_id, fingerprint, created_at) VALUES (?, ?, ?)",
                (identity_id, fingerprint, self._now()),
            )
            return identity_id

    def add_occurrence(
        self,
        run_id: str,
        *,
        source_record_id: str,
        identity_id: str,
        amount_minor: int,
        currency: str,
    ) -> str:
        self._require_nonempty_text(run_id, "run_id")
        self._require_nonempty_text(source_record_id, "source_record_id")
        self._require_nonempty_text(identity_id, "identity_id")
        if type(amount_minor) is not int:
            raise TypeError("amount_minor must be an integer, never a binary float")
        if (
            not isinstance(currency, str)
            or len(currency) != 3
            or not currency.isascii()
            or not currency.isalpha()
            or not currency.isupper()
        ):
            raise ValueError("currency must be a three-letter uppercase ISO code")

        occurrence_id = self._new_id("occ")
        with self._connection() as connection, connection:
            connection.execute(
                "INSERT INTO imported_occurrences "
                "(occurrence_id, run_id, source_record_id, identity_id, amount_minor, "
                "currency, inclusion_state, exclusion_reason, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 'included', NULL, ?)",
                (
                    occurrence_id,
                    run_id,
                    source_record_id,
                    identity_id,
                    amount_minor,
                    currency,
                    self._now(),
                ),
            )
        return occurrence_id

    def get_occurrence(self, occurrence_id: str) -> dict[str, Any]:
        return self._fetch_one(
            "SELECT occurrence_id, run_id, source_record_id, identity_id, "
            "amount_minor, currency, inclusion_state, exclusion_reason, created_at "
            "FROM imported_occurrences WHERE occurrence_id = ?",
            (occurrence_id,),
            entity="occurrence",
        )

    def list_occurrences(self, run_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            "SELECT occurrence_id, run_id, source_record_id, identity_id, "
            "amount_minor, currency, inclusion_state, exclusion_reason, created_at "
            "FROM imported_occurrences WHERE run_id = ? "
            "ORDER BY created_at, occurrence_id",
            (run_id,),
        )

    def add_manual_correction(
        self,
        identity_id: str,
        *,
        correction_type: str,
        value: str,
    ) -> str:
        self._require_nonempty_text(identity_id, "identity_id")
        self._require_nonempty_text(correction_type, "correction_type")
        self._require_nonempty_text(value, "value")
        correction_id = self._new_id("cor")
        with self._connection() as connection, connection:
            connection.execute(
                "INSERT INTO manual_corrections "
                "(correction_id, identity_id, correction_type, value, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    correction_id,
                    identity_id,
                    correction_type,
                    value,
                    self._now(),
                ),
            )
        return correction_id

    def list_manual_corrections(self, identity_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            "SELECT correction_id, identity_id, correction_type, value, created_at "
            "FROM manual_corrections WHERE identity_id = ? "
            "ORDER BY created_at, correction_id",
            (identity_id,),
        )

    def undo_import_run(self, run_id: str) -> None:
        self._require_nonempty_text(run_id, "run_id")
        with self._connection() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            run = connection.execute(
                "SELECT state FROM import_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if run is None:
                raise KeyError(f"import run not found: {run_id}")
            connection.execute(
                "UPDATE imported_occurrences "
                "SET inclusion_state = 'excluded', exclusion_reason = 'run_undone' "
                "WHERE run_id = ?",
                (run_id,),
            )
            connection.execute(
                "UPDATE import_runs SET state = 'undone' WHERE run_id = ?",
                (run_id,),
            )

    def get_occurrence_provenance(self, occurrence_id: str) -> dict[str, Any]:
        return self._fetch_one(
            "SELECT o.occurrence_id, o.run_id, r.source_fingerprint, "
            "o.source_record_id, s.source_locator, "
            "o.identity_id AS transaction_identity_id, "
            "i.fingerprint AS transaction_fingerprint, "
            "o.inclusion_state, o.exclusion_reason "
            "FROM imported_occurrences AS o "
            "JOIN import_runs AS r ON r.run_id = o.run_id "
            "JOIN source_records AS s ON s.source_record_id = o.source_record_id "
            "JOIN transaction_identities AS i ON i.identity_id = o.identity_id "
            "WHERE o.occurrence_id = ?",
            (occurrence_id,),
            entity="occurrence",
        )

    def entity_counts(self) -> dict[str, int]:
        tables = (
            "import_runs",
            "source_records",
            "transaction_identities",
            "imported_occurrences",
            "manual_corrections",
        )
        with self._connection() as connection:
            return {
                table: int(
                    connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                )
                for table in tables
            }

    def _fetch_one(
        self,
        statement: str,
        parameters: tuple[Any, ...],
        *,
        entity: str,
    ) -> dict[str, Any]:
        with self._connection() as connection:
            row = connection.execute(statement, parameters).fetchone()
        if row is None:
            raise KeyError(f"{entity} not found")
        return dict(row)

    def _fetch_all(
        self,
        statement: str,
        parameters: tuple[Any, ...],
    ) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(statement, parameters).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex}"

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")

    @staticmethod
    def _require_nonempty_text(value: object, field: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be non-empty text")
