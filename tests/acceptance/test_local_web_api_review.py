from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from backend.local_web_api import LocalWebApi
from tests.backend.local_web_api_support import (
    CSV_FIXTURE,
    CSRF_TOKEN,
    LocalWebApiTestCase,
)


class LocalWebApiIndependentReviewTests(LocalWebApiTestCase):
    def test_database_factory_rejects_unc_before_persistence(self) -> None:
        with (
            patch("backend.persistence.Path.is_dir", return_value=True),
            patch("backend.persistence.Path.exists", return_value=False),
            patch("backend.persistence.sqlite3.connect") as connect,
        ):
            with self.assertRaisesRegex(ValueError, "local"):
                LocalWebApi.from_database(
                    r"\\server\share\expenses.sqlite",
                    csrf_token=CSRF_TOKEN,
                )
        connect.assert_not_called()

    def test_any_accepted_configured_csrf_token_is_usable(self) -> None:
        csrf_token = "revïew-token"
        try:
            api = LocalWebApi(
                self.store,
                csrf_token=csrf_token,
                max_upload_bytes=1_000_000,
            )
        except ValueError:
            # Rejecting an unsupported configuration up front is also safe.
            return
        session = self.data(api.dispatch("GET", "/api/session"))
        self.assertEqual(session["csrf_token"], csrf_token)

        response = api.dispatch(
            "POST",
            "/api/import",
            headers={
                "Content-Type": "text/csv",
                "X-Local-Expense-CSRF": csrf_token,
                "X-Statement-Filename": CSV_FIXTURE.name,
            },
            body=CSV_FIXTURE.read_bytes(),
        )
        self.assertEqual(response.status, 201, response.json())

    def _add_transaction(
        self,
        *,
        label: str,
        currency: str,
    ) -> tuple[str, str]:
        run_id = self.store.create_import_run(
            f"review-mixed-run:{label}",
            source_name=f"review-{label}.csv",
            source_type="csv",
        )
        source_record_id = self.store.add_source_record(
            run_id,
            source_locator="csv-row:2",
            retained_input=f"review mixed currency {label}",
            parse_status="parsed",
        )
        identity_id = self.store.get_or_create_identity(
            f"review-mixed-identity:{label}"
        )
        self.store.add_normalized_transaction(
            identity_id,
            transaction_date="2026-07-01",
            merchant=f"REVIEW {label}",
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
        return run_id, identity_id

    def test_mixed_currency_conflict_does_not_hide_inspectable_run_detail(self) -> None:
        runs = (
            self._add_transaction(label="CAD", currency="CAD"),
            self._add_transaction(label="USD", currency="USD"),
        )

        month = self.api.dispatch("GET", "/api/months/2026-07")
        self.assertEqual(month.status, 409)
        self.assertEqual(
            month.json()["error"]["code"],
            "analysis_state_conflict",
        )
        self.assertEqual(
            len(self.data(self.api.dispatch("GET", "/api/import-runs"))),
            2,
        )

        for run_id, identity_id in runs:
            with self.subTest(run_id=run_id):
                detail = self.api.dispatch(
                    "GET",
                    f"/api/import-runs/{run_id}",
                )
                self.assertEqual(detail.status, 200, detail.json())
                payload = detail.json()["data"]
                self.assertEqual(payload["summary"]["run_id"], run_id)
                self.assertEqual(len(payload["records"]), 1)
                self.assertEqual(payload["records"][0]["identity_id"], identity_id)

    def test_concurrent_repeated_undo_has_one_success_and_one_conflict(self) -> None:
        run_id = self.store.create_import_run(
            "review-concurrent-undo",
            source_name="review.csv",
            source_type="csv",
        )
        other_api = LocalWebApi.from_database(
            self.database_path,
            csrf_token=CSRF_TOKEN,
            max_upload_bytes=1_000_000,
        )
        barrier = threading.Barrier(2)

        def gated_summary(api: LocalWebApi):
            original = api.store.get_import_run_summary
            first_active_read = False
            state_lock = threading.Lock()

            def wrapped(requested_run_id: str):
                nonlocal first_active_read
                summary = original(requested_run_id)
                should_wait = False
                if requested_run_id == run_id and summary["state"] == "active":
                    with state_lock:
                        if not first_active_read:
                            first_active_read = True
                            should_wait = True
                if should_wait:
                    barrier.wait(timeout=5)
                return summary

            return patch.object(api.store, "get_import_run_summary", wrapped)

        def undo(api: LocalWebApi) -> int:
            return api.dispatch(
                "POST",
                f"/api/import-runs/{run_id}/undo",
                headers={"X-Local-Expense-CSRF": CSRF_TOKEN},
            ).status

        with gated_summary(self.api), gated_summary(other_api):
            with ThreadPoolExecutor(max_workers=2) as executor:
                statuses = sorted(
                    executor.map(undo, (self.api, other_api))
                )

        self.assertEqual(statuses, [200, 409])
        self.assertEqual(self.store.get_import_run_summary(run_id)["state"], "undone")


if __name__ == "__main__":
    import unittest

    unittest.main()
