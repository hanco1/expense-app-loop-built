from __future__ import annotations

from unittest.mock import patch

from tests.backend.local_web_api_support import CSRF_TOKEN, LocalWebApiTestCase


class LocalWebApiErrorTests(LocalWebApiTestCase):
    def test_status_and_error_envelopes_cover_all_declared_classes(self) -> None:
        missing = self.api.dispatch("GET", "/api/import-runs/run_missing")
        validation = self.api.dispatch(
            "POST",
            "/api/transactions/identity/category",
            headers={
                "Content-Type": "application/json",
                "X-Local-Expense-CSRF": CSRF_TOKEN,
            },
            body=b"not-json",
        )
        unsupported = self.api.dispatch(
            "POST",
            "/api/import",
            headers={
                "Content-Type": "application/octet-stream",
                "X-Local-Expense-CSRF": CSRF_TOKEN,
                "X-Statement-Filename": "statement.bin",
            },
            body=b"content",
        )
        small_api = type(self.api)(
            self.store,
            csrf_token=CSRF_TOKEN,
            max_upload_bytes=1,
        )
        oversized = small_api.dispatch(
            "POST",
            "/api/import",
            headers={
                "Content-Type": "text/csv",
                "X-Local-Expense-CSRF": CSRF_TOKEN,
                "X-Statement-Filename": "statement.csv",
            },
            body=b"xx",
        )
        run_id = self.store.create_import_run(
            "synthetic-api-undo-conflict",
            source_name="synthetic.csv",
            source_type="csv",
        )
        first_undo = self.api.dispatch(
            "POST",
            f"/api/import-runs/{run_id}/undo",
            headers={"X-Local-Expense-CSRF": CSRF_TOKEN},
        )
        conflict = self.api.dispatch(
            "POST",
            f"/api/import-runs/{run_id}/undo",
            headers={"X-Local-Expense-CSRF": CSRF_TOKEN},
        )

        expected = (
            (missing, 404, "not_found"),
            (validation, 400, "validation_error"),
            (unsupported, 415, "unsupported_media_type"),
            (oversized, 413, "upload_too_large"),
            (conflict, 409, "run_state_conflict"),
        )
        self.assertEqual(first_undo.status, 200)
        for response, status, code in expected:
            self.assertEqual(response.status, status)
            error = response.json()["error"]
            self.assertEqual(set(error), {"code", "details", "message"})
            self.assertEqual(error["code"], code)

    def test_parser_and_unexpected_failures_never_leak_raw_content(self) -> None:
        sentinel = "PRIVATE-STATEMENT-SENTINEL"
        parser_failure = self.api.dispatch(
            "POST",
            "/api/import",
            headers={
                "Content-Type": "text/csv",
                "X-Local-Expense-CSRF": CSRF_TOKEN,
                "X-Statement-Filename": "invalid.csv",
            },
            body=sentinel.encode("utf-8"),
        )
        self.assertEqual(parser_failure.status, 422)
        parser_error = parser_failure.json()["error"]
        self.assertEqual(parser_error["code"], "statement_import_failed")
        self.assertEqual(parser_error["details"]["run"]["summary"]["state"], "failed")
        self.assertNotIn(sentinel, parser_failure.body.decode("utf-8"))
        self.assertNotIn("retained_input", parser_failure.body.decode("utf-8"))

        with patch.object(
            self.store,
            "list_import_run_summaries",
            side_effect=RuntimeError(sentinel),
        ):
            unexpected = self.api.dispatch("GET", "/api/import-runs")
        self.assertEqual(unexpected.status, 500)
        unexpected_text = unexpected.body.decode("utf-8")
        self.assertNotIn(sentinel, unexpected_text)
        self.assertNotIn("Traceback", unexpected_text)
        self.assertEqual(unexpected.json()["error"]["code"], "internal_error")

    def test_mixed_currency_analysis_state_is_a_conflict(self) -> None:
        runs: list[tuple[str, str]] = []
        for label, currency in (("CAD", "CAD"), ("USD", "USD")):
            run_id = self.store.create_import_run(
                f"synthetic-mixed-{label}",
                source_name=f"synthetic-{label}.csv",
                source_type="csv",
            )
            source_record_id = self.store.add_source_record(
                run_id,
                source_locator="csv-row:2",
                retained_input=f"synthetic mixed currency {label}",
                parse_status="parsed",
            )
            identity_id = self.store.get_or_create_identity(
                f"synthetic-mixed-identity-{label}"
            )
            self.store.add_normalized_transaction(
                identity_id,
                transaction_date="2026-07-01",
                merchant=f"SYNTHETIC {label}",
                amount_minor=-100,
                currency=currency,
            )
            self.store.add_occurrence(
                run_id,
                source_record_id=source_record_id,
                identity_id=identity_id,
                amount_minor=-100,
                currency=currency,
            )
            runs.append((run_id, identity_id))

        response = self.api.dispatch("GET", "/api/months/2026-07")
        self.assertEqual(response.status, 409)
        self.assertEqual(
            response.json()["error"]["code"],
            "analysis_state_conflict",
        )
        for run_id, identity_id in runs:
            with self.subTest(run_id=run_id):
                detail = self.api.dispatch("GET", f"/api/import-runs/{run_id}")
                self.assertEqual(detail.status, 200, detail.json())
                payload = detail.json()["data"]
                self.assertEqual(payload["summary"]["run_id"], run_id)
                self.assertEqual(payload["records"][0]["identity_id"], identity_id)


if __name__ == "__main__":
    import unittest

    unittest.main()
