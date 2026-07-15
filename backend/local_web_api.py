from __future__ import annotations

import hmac
import json
import re
import secrets
import sqlite3
import threading
from dataclasses import dataclass
from os import PathLike
from typing import Any, Mapping

from backend.analysis import AnalysisService
from backend.persistence import CoreStore
from backend.statement_import import StatementImportFailure, StatementImportService
from contracts.analysis import (
    CANONICAL_CATEGORIES,
    AnalysisTransaction,
    CategoryState,
    DuplicateCandidate,
    MonthSummary,
)
from contracts.local_web_api import LocalWebRequest, LocalWebResponse


DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024
JSON_CONTENT_TYPE = "application/json"
IMPORT_MEDIA_TYPES = {
    "application/pdf": "pdf",
    "text/csv": "csv",
}
RUN_DETAIL_PATTERN = re.compile(r"/api/import-runs/([^/]+)")
RUN_UNDO_PATTERN = re.compile(r"/api/import-runs/([^/]+)/undo")
MONTH_DETAIL_PATTERN = re.compile(r"/api/months/([0-9]{4}-(?:0[1-9]|1[0-2]))")
CATEGORY_PATTERN = re.compile(r"/api/transactions/([^/]+)/category")
DUPLICATE_DECISION_PATTERN = re.compile(r"/api/duplicates/([^/]+)/decision")


@dataclass(frozen=True)
class _ApiError(Exception):
    status: int
    code: str
    message: str
    details: Mapping[str, Any]


class LocalWebApi:
    """Local JSON facade with no listener, network client, or raw-data logging."""

    def __init__(
        self,
        store: CoreStore,
        *,
        max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
        csrf_token: str | None = None,
    ) -> None:
        if not isinstance(store, CoreStore):
            raise TypeError("store must be a CoreStore")
        if type(max_upload_bytes) is not int or max_upload_bytes <= 0:
            raise ValueError("max_upload_bytes must be a positive integer")
        if csrf_token is not None and (
            not isinstance(csrf_token, str)
            or not csrf_token
            or not csrf_token.isascii()
        ):
            raise ValueError("csrf_token must be non-empty ASCII text")
        self.store = store
        self.imports = StatementImportService(store)
        self.analysis = AnalysisService(store)
        self.max_upload_bytes = max_upload_bytes
        self._csrf_token = csrf_token or secrets.token_urlsafe(32)
        self._write_lock = threading.RLock()

    @classmethod
    def from_database(
        cls,
        database_path: str | PathLike[str],
        *,
        max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
        csrf_token: str | None = None,
    ) -> LocalWebApi:
        store = CoreStore(database_path)
        store.initialize()
        return cls(
            store,
            max_upload_bytes=max_upload_bytes,
            csrf_token=csrf_token,
        )

    def handle(self, request: LocalWebRequest) -> LocalWebResponse:
        if not isinstance(request, LocalWebRequest):
            raise TypeError("request must be a LocalWebRequest")
        return self.dispatch(
            request.method,
            request.path,
            headers=request.headers,
            body=request.body,
        )

    def dispatch(
        self,
        method: str,
        path: str,
        *,
        headers: Mapping[str, str] | None = None,
        body: bytes = b"",
    ) -> LocalWebResponse:
        try:
            normalized_method = self._normalize_method(method)
            normalized_path = self._normalize_path(path)
            normalized_headers = self._normalize_headers(headers)
            if type(body) is not bytes:
                raise _ApiError(
                    400,
                    "validation_error",
                    "request body must be bytes",
                    {"field": "body"},
                )
            if normalized_method == "POST":
                self._require_csrf(normalized_headers)
                with self._write_lock:
                    return self._dispatch_request(
                        normalized_method,
                        normalized_path,
                        normalized_headers,
                        body,
                    )
            return self._dispatch_request(
                normalized_method,
                normalized_path,
                normalized_headers,
                body,
            )
        except _ApiError as error:
            return self._error_response(error)
        except KeyError:
            return self._error_response(
                _ApiError(
                    404,
                    "not_found",
                    "requested resource was not found",
                    {},
                )
            )
        except sqlite3.IntegrityError:
            return self._error_response(
                _ApiError(
                    409,
                    "conflict",
                    "request conflicts with the current resource state",
                    {},
                )
            )
        except (TypeError, ValueError):
            return self._error_response(
                _ApiError(
                    400,
                    "validation_error",
                    "request validation failed",
                    {},
                )
            )
        except Exception:
            return self._error_response(
                _ApiError(
                    500,
                    "internal_error",
                    "an unexpected local application error occurred",
                    {},
                )
            )

    def _dispatch_request(
        self,
        method: str,
        path: str,
        headers: Mapping[str, str],
        body: bytes,
    ) -> LocalWebResponse:
        if method == "GET" and path == "/api/session":
            return self._success(self._session_data())
        if method == "GET" and path == "/api/import-runs":
            summaries = [
                self._serialize_run_summary(summary)
                for summary in self.store.list_import_run_summaries()
            ]
            return self._success(summaries)
        run_detail_match = RUN_DETAIL_PATTERN.fullmatch(path)
        if method == "GET" and run_detail_match is not None:
            return self._success(self._serialize_run(run_detail_match.group(1)))
        if method == "GET" and path == "/api/months":
            return self._success(list(self.analysis.list_months()))
        month_match = MONTH_DETAIL_PATTERN.fullmatch(path)
        if method == "GET" and month_match is not None:
            try:
                summary = self.analysis.get_month_summary(month_match.group(1))
            except ValueError:
                raise _ApiError(
                    409,
                    "analysis_state_conflict",
                    "month cannot be represented under the current analysis state",
                    {"month": month_match.group(1)},
                ) from None
            return self._success(
                self._serialize_month(summary)
            )
        if method == "GET" and path == "/api/duplicates":
            return self._success(
                [
                    self._serialize_duplicate(candidate)
                    for candidate in self.analysis.list_duplicate_candidates()
                ]
            )
        if method == "POST" and path == "/api/import":
            return self._import_statement(headers, body)
        undo_match = RUN_UNDO_PATTERN.fullmatch(path)
        if method == "POST" and undo_match is not None:
            return self._undo_run(undo_match.group(1))
        category_match = CATEGORY_PATTERN.fullmatch(path)
        if method == "POST" and category_match is not None:
            return self._set_category(
                category_match.group(1),
                headers,
                body,
            )
        decision_match = DUPLICATE_DECISION_PATTERN.fullmatch(path)
        if method == "POST" and decision_match is not None:
            return self._set_duplicate_decision(
                decision_match.group(1),
                headers,
                body,
            )

        known_path = self._known_path(path)
        if known_path:
            raise _ApiError(
                405,
                "method_not_allowed",
                "method is not allowed for this resource",
                {},
            )
        raise _ApiError(
            404,
            "not_found",
            "requested resource was not found",
            {},
        )

    def _session_data(self) -> dict[str, Any]:
        descriptors = self.imports.parser_descriptors()
        return {
            "canonical_categories": list(CANONICAL_CATEGORIES),
            "csrf_token": self._csrf_token,
            "local_only": True,
            "max_upload_bytes": self.max_upload_bytes,
            "parser_modes": {
                source_type: str(descriptors[source_type]["mode"])
                for source_type in sorted(descriptors)
            },
            "supported_media_types": {
                media_type: IMPORT_MEDIA_TYPES[media_type]
                for media_type in sorted(IMPORT_MEDIA_TYPES)
            },
            "supported_source_types": sorted(descriptors),
        }

    def _import_statement(
        self,
        headers: Mapping[str, str],
        body: bytes,
    ) -> LocalWebResponse:
        media_type = headers.get("content-type")
        if media_type not in IMPORT_MEDIA_TYPES:
            raise _ApiError(
                415,
                "unsupported_media_type",
                "statement Content-Type is not supported",
                {"supported": sorted(IMPORT_MEDIA_TYPES)},
            )
        filename = headers.get("x-statement-filename")
        if not self._valid_filename(filename):
            raise _ApiError(
                400,
                "validation_error",
                "statement filename is invalid",
                {"field": "X-Statement-Filename"},
            )
        if not body:
            raise _ApiError(
                400,
                "validation_error",
                "statement body must not be empty",
                {"field": "body"},
            )
        if len(body) > self.max_upload_bytes:
            raise _ApiError(
                413,
                "upload_too_large",
                "statement exceeds the configured upload limit",
                {"max_upload_bytes": self.max_upload_bytes},
            )
        try:
            run_id = self.imports.import_bytes(
                body,
                filename=filename.strip(),
                source_type=IMPORT_MEDIA_TYPES[media_type],
            )
        except StatementImportFailure as error:
            raise _ApiError(
                422,
                "statement_import_failed",
                "statement import could not be completed",
                {
                    "run_id": error.run_id,
                    "run": self._serialize_run(error.run_id),
                },
            ) from None
        return self._success(self._serialize_run(run_id), status=201)

    def _undo_run(self, run_id: str) -> LocalWebResponse:
        if not self.store.undo_import_run_if_active(run_id):
            summary = self.store.get_import_run_summary(run_id)
            raise _ApiError(
                409,
                "run_state_conflict",
                "only an active import run can be undone",
                {"run_id": run_id, "state": summary["state"]},
            )
        return self._success(self._serialize_run(run_id))

    def _set_category(
        self,
        identity_id: str,
        headers: Mapping[str, str],
        body: bytes,
    ) -> LocalWebResponse:
        payload = self._json_object(headers, body)
        if set(payload) != {"category"}:
            raise _ApiError(
                400,
                "validation_error",
                "category request must contain exactly one category",
                {"fields": ["category"]},
            )
        category = payload["category"]
        if not isinstance(category, str) or category not in CANONICAL_CATEGORIES:
            raise _ApiError(
                400,
                "validation_error",
                "category is not canonical",
                {"field": "category"},
            )
        return self._success(
            self._serialize_category_state(
                self.analysis.set_category(identity_id, category)
            )
        )

    def _set_duplicate_decision(
        self,
        duplicate_link_id: str,
        headers: Mapping[str, str],
        body: bytes,
    ) -> LocalWebResponse:
        payload = self._json_object(headers, body)
        if not set(payload) <= {"decision", "kept_identity_id"} or (
            "decision" not in payload
        ):
            raise _ApiError(
                400,
                "validation_error",
                "duplicate decision request has invalid fields",
                {"fields": ["decision", "kept_identity_id"]},
            )
        decision = payload["decision"]
        kept_identity_id = payload.get("kept_identity_id")
        if decision not in {"same_transaction", "distinct"}:
            raise _ApiError(
                400,
                "validation_error",
                "duplicate decision is invalid",
                {"field": "decision"},
            )
        candidate = self.analysis.get_duplicate_candidate(duplicate_link_id)
        if decision == "same_transaction":
            if (
                not isinstance(kept_identity_id, str)
                or not kept_identity_id
                or kept_identity_id
                not in {
                    candidate.left_identity_id,
                    candidate.right_identity_id,
                }
            ):
                raise _ApiError(
                    400,
                    "validation_error",
                    "kept identity must belong to the duplicate pair",
                    {"field": "kept_identity_id"},
                )
        elif kept_identity_id is not None:
            raise _ApiError(
                400,
                "validation_error",
                "a distinct decision cannot name a kept identity",
                {"field": "kept_identity_id"},
            )
        try:
            updated = self.analysis.set_duplicate_decision(
                duplicate_link_id,
                decision,
                kept_identity_id,
            )
        except ValueError:
            raise _ApiError(
                409,
                "duplicate_graph_conflict",
                "duplicate decision conflicts with the component invariant",
                {"duplicate_link_id": duplicate_link_id},
            ) from None
        return self._success(self._serialize_duplicate(updated))

    def _serialize_run(self, run_id: str) -> dict[str, Any]:
        summary = self.store.get_import_run_summary(run_id)
        records = self.store.get_import_run_detail(run_id)
        analysis_transactions = self._analysis_transactions_by_identity()
        candidates_by_identity: dict[str, list[DuplicateCandidate]] = {}
        for candidate in self.analysis.list_duplicate_candidates():
            candidates_by_identity.setdefault(
                candidate.left_identity_id,
                [],
            ).append(candidate)
            candidates_by_identity.setdefault(
                candidate.right_identity_id,
                [],
            ).append(candidate)
        return {
            "records": [
                self._serialize_run_record(
                    record,
                    analysis_transactions.get(str(record["identity_id"])),
                    tuple(
                        sorted(
                            candidates_by_identity.get(
                                str(record["identity_id"]),
                                [],
                            ),
                            key=lambda candidate: candidate.duplicate_link_id,
                        )
                    ),
                )
                for record in records
            ],
            "summary": self._serialize_run_summary(summary),
        }

    def _analysis_transactions_by_identity(
        self,
    ) -> dict[str, AnalysisTransaction]:
        # Run inspection needs effective inclusion/category state but must not
        # perform the single-currency monthly aggregation used by month reads.
        return {
            transaction.identity_id: transaction
            for transaction in self.analysis._active_transactions()
        }

    @staticmethod
    def _serialize_run_summary(summary: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "created_at": str(summary["created_at"]),
            "exact_reimport_of_run_id": summary["exact_reimport_of_run_id"],
            "failed_count": int(summary["failed_count"]),
            "occurrence_count": int(summary["occurrence_count"]),
            "parsed_count": int(summary["parsed_count"]),
            "run_id": str(summary["run_id"]),
            "source_fingerprint": str(summary["source_fingerprint"]),
            "source_name": str(summary["source_name"]),
            "source_record_count": int(summary["source_record_count"]),
            "source_type": str(summary["source_type"]),
            "state": str(summary["state"]),
        }

    @staticmethod
    def _serialize_run_record(
        record: Mapping[str, Any],
        analysis_transaction: AnalysisTransaction | None,
        duplicate_candidates: tuple[DuplicateCandidate, ...],
    ) -> dict[str, Any]:
        normalized = record["normalized_transaction"]
        normalized_json = None
        if normalized is not None:
            normalized_json = {
                "amount_minor": str(normalized["amount_minor"]),
                "currency": str(normalized["currency"]),
                "is_spending": bool(normalized["is_spending"]),
                "merchant": str(normalized["merchant"]),
                "transaction_date": str(normalized["transaction_date"]),
            }
        if not duplicate_candidates:
            duplicate_state = "none"
        elif any(
            candidate.effective_decision == "same_transaction"
            for candidate in duplicate_candidates
        ):
            duplicate_state = "same_transaction"
        elif any(
            candidate.effective_decision == "distinct"
            for candidate in duplicate_candidates
        ):
            duplicate_state = "distinct"
        else:
            duplicate_state = "pending"
        effective_included = bool(
            analysis_transaction is not None and analysis_transaction.included
        )
        effective_inclusion_reason = (
            analysis_transaction.inclusion_reason
            if analysis_transaction is not None
            else str(record["inclusion_reason"])
        )
        return {
            "duplicate_link_ids": [
                candidate.duplicate_link_id for candidate in duplicate_candidates
            ],
            "duplicate_state": duplicate_state,
            "effective_included": effective_included,
            "effective_inclusion_reason": effective_inclusion_reason,
            "error_code": record["error_code"],
            "exact_reimport_of_run_id": record["exact_reimport_of_run_id"],
            "identity_id": record["identity_id"],
            "inclusion_reason": str(record["inclusion_reason"]),
            "inclusion_state": record["inclusion_state"],
            "normalized_transaction": normalized_json,
            "occurrence_id": record["occurrence_id"],
            "parse_status": str(record["parse_status"]),
            "run_id": str(record["run_id"]),
            "source_fingerprint": str(record["source_fingerprint"]),
            "source_locator": str(record["source_locator"]),
            "source_name": str(record["source_name"]),
            "source_record_id": str(record["source_record_id"]),
            "source_type": str(record["source_type"]),
            "suspected_duplicate_identity_ids": list(
                record["suspected_duplicate_identity_ids"]
            ),
        }

    def _serialize_duplicate(
        self,
        candidate: DuplicateCandidate,
    ) -> dict[str, Any]:
        return {
            "duplicate_link_id": candidate.duplicate_link_id,
            "effective_decision": candidate.effective_decision,
            "effective_decision_id": candidate.effective_decision_id,
            "history": [
                {
                    "created_at": decision.created_at,
                    "decision": decision.decision,
                    "decision_id": decision.decision_id,
                    "duplicate_link_id": decision.duplicate_link_id,
                    "kept_identity_id": decision.kept_identity_id,
                }
                for decision in candidate.history
            ],
            "kept_identity_id": candidate.kept_identity_id,
            "left": self._serialize_duplicate_side(
                candidate.left_identity_id,
                candidate.left_included,
            ),
            "right": self._serialize_duplicate_side(
                candidate.right_identity_id,
                candidate.right_included,
            ),
        }

    def _serialize_duplicate_side(
        self,
        identity_id: str,
        included: bool,
    ) -> dict[str, Any]:
        transaction = self.store.get_normalized_transaction(identity_id)
        return {
            "amount_minor": str(transaction["amount_minor"]),
            "currency": str(transaction["currency"]),
            "identity_id": identity_id,
            "included": included,
            "merchant": str(transaction["merchant"]),
            "transaction_date": str(transaction["transaction_date"]),
        }

    @staticmethod
    def _serialize_category_state(state: CategoryState) -> dict[str, Any]:
        return {
            "auto_category": state.auto_category,
            "category_rule_version": state.category_rule_version,
            "category_source": state.category_source,
            "effective_category": state.effective_category,
            "effective_correction_id": state.effective_correction_id,
            "history": [
                {
                    "category": correction.category,
                    "correction_id": correction.correction_id,
                    "created_at": correction.created_at,
                    "identity_id": correction.identity_id,
                }
                for correction in state.history
            ],
            "identity_id": state.identity_id,
        }

    @staticmethod
    def _serialize_month(summary: MonthSummary) -> dict[str, Any]:
        return {
            "category_breakdown": [
                {
                    "category": bucket.category,
                    "contributing_identity_ids": list(
                        bucket.contributing_identity_ids
                    ),
                    "spending_minor": str(bucket.spending_minor),
                    "transaction_count": bucket.transaction_count,
                }
                for bucket in summary.category_breakdown
            ],
            "credit_total_minor": str(summary.credit_total_minor),
            "credit_transaction_count": summary.credit_transaction_count,
            "currency": summary.currency,
            "month": summary.month,
            "spending_total_minor": str(summary.spending_total_minor),
            "spending_transaction_count": summary.spending_transaction_count,
            "transaction_count": summary.transaction_count,
            "transactions": [
                LocalWebApi._serialize_analysis_transaction(transaction)
                for transaction in summary.transactions
            ],
        }

    @staticmethod
    def _serialize_analysis_transaction(
        transaction: AnalysisTransaction,
    ) -> dict[str, Any]:
        return {
            "active_supports": [
                {
                    "occurrence_id": support.occurrence_id,
                    "run_id": support.run_id,
                    "source_fingerprint": support.source_fingerprint,
                    "source_locator": support.source_locator,
                    "source_name": support.source_name,
                    "source_record_id": support.source_record_id,
                    "source_type": support.source_type,
                }
                for support in transaction.active_supports
            ],
            "amount_minor": str(transaction.amount_minor),
            "auto_category": transaction.auto_category,
            "category_rule_version": transaction.category_rule_version,
            "category_source": transaction.category_source,
            "correction_ids": list(transaction.correction_ids),
            "currency": transaction.currency,
            "duplicate_decision": transaction.duplicate_decision,
            "duplicate_decision_id": transaction.duplicate_decision_id,
            "duplicate_link_ids": list(transaction.duplicate_link_ids),
            "effective_category": transaction.effective_category,
            "effective_correction_id": transaction.effective_correction_id,
            "identity_id": transaction.identity_id,
            "included": transaction.included,
            "inclusion_reason": transaction.inclusion_reason,
            "is_spending": transaction.is_spending,
            "merchant": transaction.merchant,
            "transaction_date": transaction.transaction_date,
        }

    @staticmethod
    def _normalize_method(method: object) -> str:
        if not isinstance(method, str) or not method:
            raise _ApiError(
                400,
                "validation_error",
                "request method is invalid",
                {"field": "method"},
            )
        normalized = method.upper()
        if normalized not in {"GET", "POST"}:
            raise _ApiError(
                405,
                "method_not_allowed",
                "request method is not supported",
                {},
            )
        return normalized

    @staticmethod
    def _normalize_path(path: object) -> str:
        if (
            not isinstance(path, str)
            or not path.startswith("/")
            or "?" in path
            or "#" in path
        ):
            raise _ApiError(
                400,
                "validation_error",
                "request path is invalid",
                {"field": "path"},
            )
        return path

    @staticmethod
    def _normalize_headers(
        headers: Mapping[str, str] | None,
    ) -> dict[str, str]:
        if headers is None:
            return {}
        if not isinstance(headers, Mapping):
            raise _ApiError(
                400,
                "validation_error",
                "request headers are invalid",
                {"field": "headers"},
            )
        normalized: dict[str, str] = {}
        for name, value in headers.items():
            if not isinstance(name, str) or not isinstance(value, str):
                raise _ApiError(
                    400,
                    "validation_error",
                    "request headers must contain text names and values",
                    {"field": "headers"},
                )
            normalized_name = name.casefold()
            if normalized_name in normalized:
                raise _ApiError(
                    400,
                    "validation_error",
                    "request contains duplicate header names",
                    {"field": "headers"},
                )
            normalized[normalized_name] = value
        return normalized

    def _require_csrf(self, headers: Mapping[str, str]) -> None:
        provided = headers.get("x-local-expense-csrf")
        if provided is None or not hmac.compare_digest(
            provided,
            self._csrf_token,
        ):
            raise _ApiError(
                403,
                "csrf_failed",
                "a valid local CSRF token is required",
                {},
            )

    @staticmethod
    def _valid_filename(filename: object) -> bool:
        if not isinstance(filename, str):
            return False
        candidate = filename.strip()
        return bool(
            candidate
            and candidate not in {".", ".."}
            and len(candidate) <= 255
            and "/" not in candidate
            and "\\" not in candidate
            and all(
                ord(character) >= 32 and ord(character) != 127
                for character in candidate
            )
        )

    @staticmethod
    def _json_object(
        headers: Mapping[str, str],
        body: bytes,
    ) -> dict[str, Any]:
        if headers.get("content-type") != JSON_CONTENT_TYPE:
            raise _ApiError(
                415,
                "unsupported_media_type",
                "mutation Content-Type must be application/json",
                {"supported": [JSON_CONTENT_TYPE]},
            )
        if not body:
            raise _ApiError(
                400,
                "validation_error",
                "JSON body must not be empty",
                {"field": "body"},
            )
        try:
            payload = json.loads(
                body.decode("utf-8"),
                object_pairs_hook=LocalWebApi._unique_json_object,
                parse_constant=LocalWebApi._reject_json_constant,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            raise _ApiError(
                400,
                "validation_error",
                "JSON body is invalid",
                {"field": "body"},
            ) from None
        if not isinstance(payload, dict):
            raise _ApiError(
                400,
                "validation_error",
                "JSON body must be an object",
                {"field": "body"},
            )
        return payload

    @staticmethod
    def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    @staticmethod
    def _reject_json_constant(_: str) -> Any:
        raise ValueError("non-finite JSON number")

    @staticmethod
    def _known_path(path: str) -> bool:
        return bool(
            path
            in {
                "/api/session",
                "/api/import-runs",
                "/api/months",
                "/api/duplicates",
                "/api/import",
            }
            or RUN_DETAIL_PATTERN.fullmatch(path)
            or RUN_UNDO_PATTERN.fullmatch(path)
            or MONTH_DETAIL_PATTERN.fullmatch(path)
            or CATEGORY_PATTERN.fullmatch(path)
            or DUPLICATE_DECISION_PATTERN.fullmatch(path)
        )

    @staticmethod
    def _success(data: Any, *, status: int = 200) -> LocalWebResponse:
        return LocalWebApi._json_response(status, {"data": data})

    @staticmethod
    def _error_response(error: _ApiError) -> LocalWebResponse:
        return LocalWebApi._json_response(
            error.status,
            {
                "error": {
                    "code": error.code,
                    "details": dict(error.details),
                    "message": error.message,
                }
            },
        )

    @staticmethod
    def _json_response(
        status: int,
        payload: Mapping[str, Any],
    ) -> LocalWebResponse:
        body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return LocalWebResponse(
            status=status,
            headers={
                "Cache-Control": "no-store",
                "Content-Type": "application/json; charset=utf-8",
                "X-Content-Type-Options": "nosniff",
            },
            body=body,
        )


LocalExpenseApi = LocalWebApi


__all__ = [
    "DEFAULT_MAX_UPLOAD_BYTES",
    "LocalExpenseApi",
    "LocalWebApi",
]
