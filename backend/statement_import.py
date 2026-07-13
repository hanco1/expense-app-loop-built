from __future__ import annotations

import csv
import hashlib
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO

from pypdf import PdfReader

from backend.persistence import CoreStore, SQLITE_INTEGER_MAX
from contracts.statement_import import (
    ParsedSourceRecord,
    ParsedTransaction,
    StatementParser,
)


CSV_HEADER = ["Date", "Description", "Debit", "Credit", "Balance"]
PDF_DATE_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}\s{2}")


class RecordParseFailure(ValueError):
    def __init__(self, error_code: str) -> None:
        super().__init__(error_code)
        self.error_code = error_code


class StatementImportFailure(RuntimeError):
    """Reports an inspectable failed run without exposing retained source content."""

    def __init__(self, run_id: str) -> None:
        super().__init__(f"statement import failed; inspect run_id {run_id}")
        self.run_id = run_id


class TdCsvStatementParser:
    source_type = "csv"
    mode = "text"

    def parse(self, content: bytes) -> list[ParsedSourceRecord]:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ValueError("CSV statement must be UTF-8 text") from error
        lines = text.splitlines()
        if not lines or next(csv.reader([lines[0]]), []) != CSV_HEADER:
            raise ValueError("unsupported TD-style CSV header")

        records: list[ParsedSourceRecord] = []
        for row_number, retained_input in enumerate(lines[1:], start=2):
            values = next(csv.reader([retained_input]), [])
            try:
                if len(values) != len(CSV_HEADER):
                    raise RecordParseFailure("invalid_column_count")
                transaction = _normalize_transaction(
                    raw_date=values[0],
                    raw_merchant=values[1],
                    raw_debit=values[2],
                    raw_credit=values[3],
                )
            except RecordParseFailure as error:
                records.append(
                    ParsedSourceRecord(
                        source_locator=f"csv-row:{row_number}",
                        retained_input=retained_input,
                        parse_status="failed",
                        error_code=error.error_code,
                        transaction=None,
                    )
                )
            else:
                records.append(
                    ParsedSourceRecord(
                        source_locator=f"csv-row:{row_number}",
                        retained_input=retained_input,
                        parse_status="parsed",
                        error_code=None,
                        transaction=transaction,
                    )
                )
        return records


class TdTextPdfStatementParser:
    source_type = "pdf"
    mode = "text"

    def parse(self, content: bytes) -> list[ParsedSourceRecord]:
        reader = PdfReader(BytesIO(content))
        records: list[ParsedSourceRecord] = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text is None:
                continue
            record_number = 0
            for retained_input in text.splitlines():
                if PDF_DATE_PATTERN.match(retained_input) is None:
                    continue
                record_number += 1
                try:
                    transaction = _normalize_transaction(
                        raw_date=retained_input[0:10],
                        raw_merchant=retained_input[12:47],
                        raw_debit=retained_input[47:61],
                        raw_credit=retained_input[61:73],
                    )
                except RecordParseFailure as error:
                    records.append(
                        ParsedSourceRecord(
                            source_locator=(
                                f"pdf-page:{page_number}:record:{record_number}"
                            ),
                            retained_input=retained_input,
                            parse_status="failed",
                            error_code=error.error_code,
                            transaction=None,
                        )
                    )
                else:
                    records.append(
                        ParsedSourceRecord(
                            source_locator=(
                                f"pdf-page:{page_number}:record:{record_number}"
                            ),
                            retained_input=retained_input,
                            parse_status="parsed",
                            error_code=None,
                            transaction=transaction,
                        )
                    )
        if not records:
            raise ValueError("text PDF contains no TD-style transaction records")
        return records


class StatementImportService:
    """Imports browser-supplied bytes into local, inspectable run units."""

    def __init__(
        self,
        store: CoreStore,
        parsers: dict[str, StatementParser] | None = None,
    ) -> None:
        self.store = store
        self.parsers: dict[str, StatementParser] = parsers or {
            "csv": TdCsvStatementParser(),
            "pdf": TdTextPdfStatementParser(),
        }

    def import_bytes(
        self,
        content: bytes,
        *,
        filename: str,
        source_type: str,
    ) -> str:
        if type(content) is not bytes:
            raise TypeError("content must be bytes supplied by the local caller")
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("filename must be non-empty display text")
        if source_type not in self.parsers:
            raise ValueError(f"unsupported statement source_type: {source_type}")

        source_fingerprint = hashlib.sha256(content).hexdigest().upper()
        exact_reimport_of_run_id = self.store.find_first_import_run(
            source_fingerprint,
            source_type,
        )
        run_id = self.store.create_import_run(
            source_fingerprint,
            source_name=filename,
            source_type=source_type,
            exact_reimport_of_run_id=exact_reimport_of_run_id,
            initial_state="importing",
        )
        try:
            records = self.parsers[source_type].parse(content)
            for record in records:
                source_record_id = self.store.add_source_record(
                    run_id,
                    source_locator=record.source_locator,
                    retained_input=record.retained_input,
                    parse_status=record.parse_status,
                    error_code=record.error_code,
                )
                if record.transaction is None:
                    continue
                identity_id = self.store.get_or_create_identity(
                    _stable_identity_fingerprint(
                        source_fingerprint,
                        record.source_locator,
                    )
                )
                created = self.store.add_normalized_transaction(
                    identity_id,
                    transaction_date=record.transaction.transaction_date,
                    merchant=record.transaction.merchant,
                    amount_minor=record.transaction.amount_minor,
                    currency=record.transaction.currency,
                )
                if created:
                    self.store.link_suspected_duplicates(identity_id)
                self.store.add_occurrence(
                    run_id,
                    source_record_id=source_record_id,
                    identity_id=identity_id,
                    amount_minor=record.transaction.amount_minor,
                    currency=record.transaction.currency,
                )
            self.store.complete_import_run(run_id)
        except Exception as error:
            try:
                self.store.fail_import_run(run_id)
            except Exception:
                # The run began in a non-effective state, so even failed cleanup
                # cannot expose partial support. The caller still receives its ID.
                pass
            raise StatementImportFailure(run_id) from error
        return run_id

    def parser_descriptors(self) -> dict[str, dict[str, str]]:
        return {
            source_type: {
                "mode": parser.mode,
                "parser": type(parser).__name__,
            }
            for source_type, parser in self.parsers.items()
        }


def _normalize_transaction(
    *,
    raw_date: str,
    raw_merchant: str,
    raw_debit: str,
    raw_credit: str,
) -> ParsedTransaction:
    try:
        transaction_date = datetime.strptime(
            raw_date.strip(),
            "%m/%d/%Y",
        ).date().isoformat()
    except ValueError as error:
        raise RecordParseFailure("invalid_date") from error

    merchant = " ".join(raw_merchant.split())
    if not merchant:
        raise RecordParseFailure("missing_merchant")
    if merchant.isnumeric():
        raise RecordParseFailure("numeric_merchant")

    debit = raw_debit.strip()
    credit = raw_credit.strip()
    if not debit and not credit:
        raise RecordParseFailure("missing_amount")
    if debit and credit:
        raise RecordParseFailure("ambiguous_amount")
    amount_minor = _parse_cents(credit if credit else debit)
    if debit:
        amount_minor = -amount_minor
    return ParsedTransaction(
        transaction_date=transaction_date,
        merchant=merchant,
        amount_minor=amount_minor,
    )


def _parse_cents(raw_amount: str) -> int:
    try:
        amount = Decimal(raw_amount)
    except InvalidOperation as error:
        raise RecordParseFailure("invalid_amount") from error
    cents = amount * 100
    if (
        amount < 0
        or cents != cents.to_integral_value()
        or cents > SQLITE_INTEGER_MAX
    ):
        raise RecordParseFailure("invalid_amount")
    return int(cents)


def _stable_identity_fingerprint(
    source_fingerprint: str,
    source_locator: str,
) -> str:
    identity_material = f"{source_fingerprint}\x00{source_locator}".encode("utf-8")
    return "statement-source:" + hashlib.sha256(identity_material).hexdigest().upper()
