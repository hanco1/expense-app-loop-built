from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime
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
    source_name TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL DEFAULT 'unknown'
        CHECK (source_type IN ('unknown', 'csv', 'pdf')),
    exact_reimport_of_run_id TEXT,
    state TEXT NOT NULL DEFAULT 'active'
        CHECK (state IN ('active', 'undone')),
    FOREIGN KEY (exact_reimport_of_run_id) REFERENCES import_runs(run_id)
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

CREATE TABLE IF NOT EXISTS normalized_transactions (
    identity_id TEXT PRIMARY KEY,
    transaction_date TEXT NOT NULL
        CHECK (transaction_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    merchant TEXT NOT NULL CHECK (length(trim(merchant)) > 0),
    amount_minor INTEGER NOT NULL
        CHECK (typeof(amount_minor) = 'integer'),
    currency TEXT NOT NULL
        CHECK (length(currency) = 3 AND currency GLOB '[A-Z][A-Z][A-Z]'),
    is_spending INTEGER NOT NULL CHECK (is_spending IN (0, 1)),
    created_at TEXT NOT NULL,
    CHECK (is_spending = CASE WHEN amount_minor < 0 THEN 1 ELSE 0 END),
    FOREIGN KEY (identity_id) REFERENCES transaction_identities(identity_id)
);

CREATE TABLE IF NOT EXISTS duplicate_links (
    duplicate_link_id TEXT PRIMARY KEY,
    left_identity_id TEXT NOT NULL,
    right_identity_id TEXT NOT NULL,
    link_type TEXT NOT NULL DEFAULT 'suspected_duplicate'
        CHECK (link_type = 'suspected_duplicate'),
    state TEXT NOT NULL DEFAULT 'suspected_pending'
        CHECK (state = 'suspected_pending'),
    created_at TEXT NOT NULL,
    CHECK (left_identity_id < right_identity_id),
    UNIQUE (left_identity_id, right_identity_id, link_type),
    FOREIGN KEY (left_identity_id) REFERENCES transaction_identities(identity_id),
    FOREIGN KEY (right_identity_id) REFERENCES transaction_identities(identity_id)
);

CREATE INDEX IF NOT EXISTS idx_source_records_run
    ON source_records(run_id, created_at, source_record_id);
CREATE INDEX IF NOT EXISTS idx_occurrences_run
    ON imported_occurrences(run_id, created_at, occurrence_id);
CREATE INDEX IF NOT EXISTS idx_corrections_identity
    ON manual_corrections(identity_id, created_at, correction_id);
CREATE INDEX IF NOT EXISTS idx_normalized_transaction_fields
    ON normalized_transactions(
        transaction_date, merchant, amount_minor, currency, identity_id
    );
CREATE INDEX IF NOT EXISTS idx_duplicate_links_right
    ON duplicate_links(right_identity_id, left_identity_id);

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
    OR NEW.source_name IS NOT OLD.source_name
    OR NEW.source_type IS NOT OLD.source_type
    OR NEW.exact_reimport_of_run_id IS NOT OLD.exact_reimport_of_run_id
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

CREATE TRIGGER IF NOT EXISTS normalized_transactions_no_update
BEFORE UPDATE ON normalized_transactions
BEGIN
    SELECT RAISE(ABORT, 'normalized transactions are immutable');
END;

CREATE TRIGGER IF NOT EXISTS normalized_transactions_no_delete
BEFORE DELETE ON normalized_transactions
BEGIN
    SELECT RAISE(ABORT, 'normalized transactions are retained');
END;

CREATE TRIGGER IF NOT EXISTS duplicate_links_no_update
BEFORE UPDATE ON duplicate_links
BEGIN
    SELECT RAISE(ABORT, 'duplicate links are append-only');
END;

CREATE TRIGGER IF NOT EXISTS duplicate_links_no_delete
BEFORE DELETE ON duplicate_links
BEGIN
    SELECT RAISE(ABORT, 'duplicate links are retained');
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

    def create_import_run(
        self,
        source_fingerprint: str,
        *,
        source_name: str = "",
        source_type: str = "unknown",
        exact_reimport_of_run_id: str | None = None,
    ) -> str:
        self._require_nonempty_text(source_fingerprint, "source_fingerprint")
        if not isinstance(source_name, str):
            raise TypeError("source_name must be text")
        if source_type not in {"unknown", "csv", "pdf"}:
            raise ValueError("source_type must be 'unknown', 'csv', or 'pdf'")
        if exact_reimport_of_run_id is not None:
            self._require_nonempty_text(
                exact_reimport_of_run_id,
                "exact_reimport_of_run_id",
            )
        run_id = self._new_id("run")
        with self._connection() as connection, connection:
            connection.execute(
                "INSERT INTO import_runs "
                "(run_id, created_at, source_fingerprint, source_name, source_type, "
                "exact_reimport_of_run_id, state) "
                "VALUES (?, ?, ?, ?, ?, ?, 'active')",
                (
                    run_id,
                    self._now(),
                    source_fingerprint,
                    source_name,
                    source_type,
                    exact_reimport_of_run_id,
                ),
            )
        return run_id

    def get_import_run(self, run_id: str) -> dict[str, Any]:
        return self._fetch_one(
            "SELECT run_id, created_at, source_fingerprint, source_name, "
            "source_type, exact_reimport_of_run_id, state "
            "FROM import_runs WHERE run_id = ?",
            (run_id,),
            entity="import run",
        )

    def find_first_import_run(
        self,
        source_fingerprint: str,
        source_type: str,
    ) -> str | None:
        self._require_nonempty_text(source_fingerprint, "source_fingerprint")
        if source_type not in {"csv", "pdf"}:
            raise ValueError("source_type must be 'csv' or 'pdf'")
        with self._connection() as connection:
            row = connection.execute(
                "SELECT run_id FROM import_runs "
                "WHERE source_fingerprint = ? AND source_type = ? "
                "ORDER BY created_at, run_id LIMIT 1",
                (source_fingerprint, source_type),
            ).fetchone()
        return None if row is None else str(row["run_id"])

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

    def add_normalized_transaction(
        self,
        identity_id: str,
        *,
        transaction_date: str,
        merchant: str,
        amount_minor: int,
        currency: str,
    ) -> bool:
        self._require_nonempty_text(identity_id, "identity_id")
        try:
            date.fromisoformat(transaction_date)
        except (TypeError, ValueError) as error:
            raise ValueError("transaction_date must be a valid ISO calendar day") from error
        self._require_nonempty_text(merchant, "merchant")
        if merchant.strip().isnumeric():
            raise ValueError("merchant must not be numeric-only")
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

        expected = {
            "transaction_date": transaction_date,
            "merchant": merchant.strip(),
            "amount_minor": amount_minor,
            "currency": currency,
            "is_spending": amount_minor < 0,
        }
        with self._connection() as connection, connection:
            cursor = connection.execute(
                "INSERT INTO normalized_transactions "
                "(identity_id, transaction_date, merchant, amount_minor, currency, "
                "is_spending, created_at) VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(identity_id) DO NOTHING",
                (
                    identity_id,
                    transaction_date,
                    merchant.strip(),
                    amount_minor,
                    currency,
                    int(amount_minor < 0),
                    self._now(),
                ),
            )
            row = connection.execute(
                "SELECT transaction_date, merchant, amount_minor, currency, is_spending "
                "FROM normalized_transactions WHERE identity_id = ?",
                (identity_id,),
            ).fetchone()
        if row is None:
            raise RuntimeError("normalized transaction insert did not persist")
        actual = dict(row)
        actual["is_spending"] = bool(actual["is_spending"])
        if actual != expected:
            raise sqlite3.IntegrityError(
                "stable identity already has different normalized transaction facts"
            )
        return cursor.rowcount == 1

    def link_suspected_duplicates(self, identity_id: str) -> list[str]:
        self._require_nonempty_text(identity_id, "identity_id")
        created_link_ids: list[str] = []
        with self._connection() as connection, connection:
            normalized = connection.execute(
                "SELECT transaction_date, merchant, amount_minor, currency "
                "FROM normalized_transactions WHERE identity_id = ?",
                (identity_id,),
            ).fetchone()
            if normalized is None:
                raise KeyError(f"normalized transaction not found: {identity_id}")
            matches = connection.execute(
                "SELECT identity_id FROM normalized_transactions "
                "WHERE identity_id != ? AND transaction_date = ? AND merchant = ? "
                "AND amount_minor = ? AND currency = ? ORDER BY identity_id",
                (
                    identity_id,
                    normalized["transaction_date"],
                    normalized["merchant"],
                    normalized["amount_minor"],
                    normalized["currency"],
                ),
            ).fetchall()
            for match in matches:
                left_identity_id, right_identity_id = sorted(
                    (identity_id, str(match["identity_id"]))
                )
                duplicate_link_id = self._new_id("dup")
                cursor = connection.execute(
                    "INSERT INTO duplicate_links "
                    "(duplicate_link_id, left_identity_id, right_identity_id, "
                    "link_type, state, created_at) "
                    "VALUES (?, ?, ?, 'suspected_duplicate', 'suspected_pending', ?) "
                    "ON CONFLICT(left_identity_id, right_identity_id, link_type) "
                    "DO NOTHING",
                    (
                        duplicate_link_id,
                        left_identity_id,
                        right_identity_id,
                        self._now(),
                    ),
                )
                if cursor.rowcount == 1:
                    created_link_ids.append(duplicate_link_id)
        return created_link_ids

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

    def get_import_run_summary(self, run_id: str) -> dict[str, Any]:
        return self._fetch_one(
            "SELECT r.run_id, r.created_at, r.source_name, r.source_type, "
            "r.source_fingerprint, r.state, r.exact_reimport_of_run_id, "
            "COUNT(DISTINCT s.source_record_id) AS source_record_count, "
            "SUM(CASE WHEN s.parse_status = 'parsed' THEN 1 ELSE 0 END) "
            "AS parsed_count, "
            "SUM(CASE WHEN s.parse_status = 'failed' THEN 1 ELSE 0 END) "
            "AS failed_count, "
            "COUNT(DISTINCT o.occurrence_id) AS occurrence_count "
            "FROM import_runs AS r "
            "LEFT JOIN source_records AS s ON s.run_id = r.run_id "
            "LEFT JOIN imported_occurrences AS o "
            "ON o.source_record_id = s.source_record_id "
            "WHERE r.run_id = ? GROUP BY r.run_id",
            (run_id,),
            entity="import run",
        )

    def get_import_run_detail(self, run_id: str) -> list[dict[str, Any]]:
        with self._connection() as connection:
            run = connection.execute(
                "SELECT run_id FROM import_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if run is None:
                raise KeyError(f"import run not found: {run_id}")
            rows = connection.execute(
                "SELECT s.source_record_id, s.run_id, r.source_name, "
                "r.source_type, r.source_fingerprint, "
                "r.exact_reimport_of_run_id, s.source_locator, "
                "s.retained_input, s.parse_status, s.error_code, "
                "o.occurrence_id, o.identity_id, o.inclusion_state, "
                "o.exclusion_reason, n.transaction_date, n.merchant, "
                "n.amount_minor, n.currency, n.is_spending "
                "FROM source_records AS s "
                "JOIN import_runs AS r ON r.run_id = s.run_id "
                "LEFT JOIN imported_occurrences AS o "
                "ON o.source_record_id = s.source_record_id "
                "LEFT JOIN normalized_transactions AS n "
                "ON n.identity_id = o.identity_id "
                "WHERE s.run_id = ? ORDER BY s.created_at, s.source_record_id",
                (run_id,),
            ).fetchall()
            details: list[dict[str, Any]] = []
            for row in rows:
                identity_id = row["identity_id"]
                duplicate_identity_ids = (
                    []
                    if identity_id is None
                    else self._duplicate_identity_ids(connection, str(identity_id))
                )
                normalized_transaction = None
                if row["transaction_date"] is not None:
                    normalized_transaction = {
                        "transaction_date": row["transaction_date"],
                        "merchant": row["merchant"],
                        "amount_minor": row["amount_minor"],
                        "currency": row["currency"],
                        "is_spending": bool(row["is_spending"]),
                    }
                if row["occurrence_id"] is None:
                    inclusion_reason = f"parse_failed:{row['error_code']}"
                elif row["inclusion_state"] == "included":
                    inclusion_reason = "active_support"
                else:
                    inclusion_reason = row["exclusion_reason"]
                details.append(
                    {
                        "source_record_id": row["source_record_id"],
                        "run_id": row["run_id"],
                        "source_name": row["source_name"],
                        "source_type": row["source_type"],
                        "source_fingerprint": row["source_fingerprint"],
                        "exact_reimport_of_run_id": row["exact_reimport_of_run_id"],
                        "source_locator": row["source_locator"],
                        "retained_input": row["retained_input"],
                        "parse_status": row["parse_status"],
                        "error_code": row["error_code"],
                        "occurrence_id": row["occurrence_id"],
                        "identity_id": identity_id,
                        "normalized_transaction": normalized_transaction,
                        "duplicate_state": (
                            "suspected_pending" if duplicate_identity_ids else "none"
                        ),
                        "suspected_duplicate_identity_ids": duplicate_identity_ids,
                        "inclusion_state": row["inclusion_state"],
                        "inclusion_reason": inclusion_reason,
                    }
                )
        return details

    def list_effective_transactions(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT n.identity_id, n.transaction_date, n.merchant, "
                "n.amount_minor, n.currency, n.is_spending, "
                "COUNT(DISTINCT o.run_id) AS active_support_count "
                "FROM normalized_transactions AS n "
                "JOIN imported_occurrences AS o ON o.identity_id = n.identity_id "
                "JOIN import_runs AS r ON r.run_id = o.run_id "
                "WHERE o.inclusion_state = 'included' AND r.state = 'active' "
                "GROUP BY n.identity_id "
                "ORDER BY n.transaction_date, n.identity_id"
            ).fetchall()
            transactions: list[dict[str, Any]] = []
            for row in rows:
                active_supports = self._active_supports(
                    connection,
                    str(row["identity_id"]),
                )
                duplicate_identity_ids = self._duplicate_identity_ids(
                    connection,
                    str(row["identity_id"]),
                )
                transactions.append(
                    {
                        "identity_id": row["identity_id"],
                        "transaction_date": row["transaction_date"],
                        "merchant": row["merchant"],
                        "amount_minor": row["amount_minor"],
                        "currency": row["currency"],
                        "is_spending": bool(row["is_spending"]),
                        "active_support_count": row["active_support_count"],
                        "active_supports": active_supports,
                        "duplicate_state": (
                            "suspected_pending" if duplicate_identity_ids else "none"
                        ),
                        "suspected_duplicate_identity_ids": duplicate_identity_ids,
                        "inclusion_state": "included",
                        "inclusion_reason": "active_occurrence_support",
                    }
                )
        return transactions

    def list_suspected_duplicate_pairs(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT d.duplicate_link_id, d.left_identity_id, "
                "d.right_identity_id, d.state, "
                "EXISTS(SELECT 1 FROM imported_occurrences AS lo "
                "JOIN import_runs AS lr ON lr.run_id = lo.run_id "
                "WHERE lo.identity_id = d.left_identity_id "
                "AND lo.inclusion_state = 'included' AND lr.state = 'active') "
                "AS left_included, "
                "EXISTS(SELECT 1 FROM imported_occurrences AS ro "
                "JOIN import_runs AS rr ON rr.run_id = ro.run_id "
                "WHERE ro.identity_id = d.right_identity_id "
                "AND ro.inclusion_state = 'included' AND rr.state = 'active') "
                "AS right_included "
                "FROM duplicate_links AS d "
                "ORDER BY d.created_at, d.duplicate_link_id"
            ).fetchall()
        return [
            {
                "duplicate_link_id": row["duplicate_link_id"],
                "left_identity_id": row["left_identity_id"],
                "right_identity_id": row["right_identity_id"],
                "state": row["state"],
                "both_included": bool(row["left_included"] and row["right_included"]),
            }
            for row in rows
        ]

    def get_statement_occurrence_provenance(
        self,
        occurrence_id: str,
    ) -> dict[str, Any]:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT o.occurrence_id, o.run_id, r.source_name, r.source_type, "
                "r.source_fingerprint, o.source_record_id, s.source_locator, "
                "o.identity_id AS transaction_identity_id, "
                "i.fingerprint AS transaction_fingerprint, "
                "n.transaction_date, n.merchant, n.amount_minor, n.currency, "
                "n.is_spending, o.inclusion_state, o.exclusion_reason "
                "FROM imported_occurrences AS o "
                "JOIN import_runs AS r ON r.run_id = o.run_id "
                "JOIN source_records AS s ON s.source_record_id = o.source_record_id "
                "JOIN transaction_identities AS i ON i.identity_id = o.identity_id "
                "JOIN normalized_transactions AS n ON n.identity_id = o.identity_id "
                "WHERE o.occurrence_id = ?",
                (occurrence_id,),
            ).fetchone()
            if row is None:
                raise KeyError("statement occurrence not found")
            duplicate_identity_ids = self._duplicate_identity_ids(
                connection,
                str(row["transaction_identity_id"]),
            )
        return {
            "occurrence_id": row["occurrence_id"],
            "run_id": row["run_id"],
            "source_name": row["source_name"],
            "source_type": row["source_type"],
            "source_fingerprint": row["source_fingerprint"],
            "source_record_id": row["source_record_id"],
            "source_locator": row["source_locator"],
            "transaction_identity_id": row["transaction_identity_id"],
            "transaction_fingerprint": row["transaction_fingerprint"],
            "transaction_date": row["transaction_date"],
            "merchant": row["merchant"],
            "amount_minor": row["amount_minor"],
            "currency": row["currency"],
            "is_spending": bool(row["is_spending"]),
            "duplicate_state": (
                "suspected_pending" if duplicate_identity_ids else "none"
            ),
            "suspected_duplicate_identity_ids": duplicate_identity_ids,
            "inclusion_state": row["inclusion_state"],
            "inclusion_reason": (
                "active_support"
                if row["inclusion_state"] == "included"
                else row["exclusion_reason"]
            ),
        }

    def entity_counts(self) -> dict[str, int]:
        tables = (
            "import_runs",
            "source_records",
            "transaction_identities",
            "imported_occurrences",
            "manual_corrections",
            "normalized_transactions",
            "duplicate_links",
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
    def _duplicate_identity_ids(
        connection: sqlite3.Connection,
        identity_id: str,
    ) -> list[str]:
        rows = connection.execute(
            "SELECT CASE WHEN left_identity_id = ? THEN right_identity_id "
            "ELSE left_identity_id END AS other_identity_id "
            "FROM duplicate_links "
            "WHERE left_identity_id = ? OR right_identity_id = ? "
            "ORDER BY other_identity_id",
            (identity_id, identity_id, identity_id),
        ).fetchall()
        return [str(row["other_identity_id"]) for row in rows]

    @staticmethod
    def _active_supports(
        connection: sqlite3.Connection,
        identity_id: str,
    ) -> list[dict[str, Any]]:
        rows = connection.execute(
            "SELECT o.occurrence_id, o.run_id, r.source_name, r.source_type, "
            "r.source_fingerprint, o.source_record_id, s.source_locator, "
            "o.inclusion_state "
            "FROM imported_occurrences AS o "
            "JOIN import_runs AS r ON r.run_id = o.run_id "
            "JOIN source_records AS s ON s.source_record_id = o.source_record_id "
            "WHERE o.identity_id = ? AND o.inclusion_state = 'included' "
            "AND r.state = 'active' ORDER BY r.created_at, o.occurrence_id",
            (identity_id,),
        ).fetchall()
        return [
            {
                "occurrence_id": row["occurrence_id"],
                "run_id": row["run_id"],
                "source_name": row["source_name"],
                "source_type": row["source_type"],
                "source_fingerprint": row["source_fingerprint"],
                "source_record_id": row["source_record_id"],
                "source_locator": row["source_locator"],
                "inclusion_state": row["inclusion_state"],
                "inclusion_reason": "active_support",
            }
            for row in rows
        ]

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
