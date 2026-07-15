from __future__ import annotations

import json

from backend.local_web_api import LocalWebApi
from tests.backend.local_web_api_support import CSRF_TOKEN, LocalWebApiTestCase


class LocalWebApiImportTests(LocalWebApiTestCase):
    def test_fixture_imports_expose_structured_rows_without_retained_input(self) -> None:
        csv_run = self.import_fixture("csv")
        pdf_run = self.import_fixture("pdf")

        self.assertEqual(
            {
                key: csv_run["summary"][key]
                for key in (
                    "source_record_count",
                    "parsed_count",
                    "failed_count",
                    "occurrence_count",
                )
            },
            {
                "source_record_count": 23,
                "parsed_count": 22,
                "failed_count": 1,
                "occurrence_count": 22,
            },
        )
        self.assertEqual(
            {
                key: pdf_run["summary"][key]
                for key in (
                    "source_record_count",
                    "parsed_count",
                    "failed_count",
                    "occurrence_count",
                )
            },
            {
                "source_record_count": 12,
                "parsed_count": 12,
                "failed_count": 0,
                "occurrence_count": 12,
            },
        )
        failed = [
            row for row in csv_run["records"] if row["parse_status"] == "failed"
        ]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["source_locator"], "csv-row:21")
        self.assertEqual(failed[0]["error_code"], "missing_amount")
        self.assertIsNone(failed[0]["normalized_transaction"])
        self.assertNotIn("retained_input", json.dumps(csv_run, sort_keys=True))
        self.assertNotIn("retained_input", json.dumps(pdf_run, sort_keys=True))
        self.assertTrue(
            all(
                row["source_locator"].startswith("pdf-page:1:record:")
                for row in pdf_run["records"]
            )
        )

    def test_all_run_states_are_persisted_newest_first_across_recreation(self) -> None:
        csv_run = self.import_fixture("csv")
        self.import_fixture("pdf")
        failed_response = self.api.dispatch(
            "POST",
            "/api/import",
            headers={
                "Content-Type": "text/csv",
                "X-Local-Expense-CSRF": CSRF_TOKEN,
                "X-Statement-Filename": "invalid.csv",
            },
            body=b"not,the,approved,header",
        )
        self.assertEqual(failed_response.status, 422)
        failed_run_id = failed_response.json()["error"]["details"]["run_id"]
        self.store.undo_import_run(csv_run["summary"]["run_id"])

        recreated = LocalWebApi.from_database(
            self.database_path,
            csrf_token=CSRF_TOKEN,
            max_upload_bytes=1_000_000,
        )
        summaries = self.data(recreated.dispatch("GET", "/api/import-runs"))
        self.assertEqual(len(summaries), 3)
        self.assertEqual(
            {summary["state"] for summary in summaries},
            {"active", "failed", "undone"},
        )
        self.assertIn(failed_run_id, {summary["run_id"] for summary in summaries})
        ordering = [
            (summary["created_at"], summary["run_id"]) for summary in summaries
        ]
        self.assertEqual(ordering, sorted(ordering, reverse=True))


if __name__ == "__main__":
    import unittest

    unittest.main()
