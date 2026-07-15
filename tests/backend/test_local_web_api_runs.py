from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from backend.local_web_api import LocalWebApi
from tests.backend.local_web_api_support import CSRF_TOKEN, LocalWebApiTestCase


class LocalWebApiRunTests(LocalWebApiTestCase):
    def test_exact_reimport_undo_and_later_reimport_preserve_correction(self) -> None:
        first = self.import_fixture("csv")
        june = self.data(self.api.dispatch("GET", "/api/months/2026-06"))
        target = next(
            transaction
            for transaction in june["transactions"]
            if transaction["merchant"].startswith("LOBLAWS")
        )
        correction = self.post_json(
            f"/api/transactions/{target['identity_id']}/category",
            {"category": "Dining"},
        )
        self.assertEqual(correction.status, 200)
        self.assertEqual(len(correction.json()["data"]["history"]), 1)

        second = self.import_fixture("csv", filename="renamed-june.csv")
        self.assertNotEqual(
            first["summary"]["run_id"],
            second["summary"]["run_id"],
        )
        self.assertIsNotNone(second["summary"]["exact_reimport_of_run_id"])
        after_reimport = self.data(
            self.api.dispatch("GET", "/api/months/2026-06")
        )
        self.assertEqual(after_reimport["spending_total_minor"], "277617")
        self.assertEqual(after_reimport["transaction_count"], 22)

        for run in (first, second):
            response = self.api.dispatch(
                "POST",
                f"/api/import-runs/{run['summary']['run_id']}/undo",
                headers={"X-Local-Expense-CSRF": CSRF_TOKEN},
            )
            self.assertEqual(response.status, 200)
            self.assertEqual(response.json()["data"]["summary"]["state"], "undone")

        self.assertEqual(self.data(self.api.dispatch("GET", "/api/months")), [])
        repeated = self.api.dispatch(
            "POST",
            f"/api/import-runs/{first['summary']['run_id']}/undo",
            headers={"X-Local-Expense-CSRF": CSRF_TOKEN},
        )
        self.assertEqual(repeated.status, 409)

        restored = self.import_fixture("csv", filename="restored.csv")
        self.assertEqual(restored["summary"]["state"], "active")
        restored_month = self.data(
            self.api.dispatch("GET", "/api/months/2026-06")
        )
        restored_target = next(
            transaction
            for transaction in restored_month["transactions"]
            if transaction["identity_id"] == target["identity_id"]
        )
        self.assertEqual(restored_target["effective_category"], "Dining")
        self.assertEqual(restored_target["category_source"], "human")
        self.assertEqual(len(restored_target["correction_ids"]), 1)
        summaries = self.data(self.api.dispatch("GET", "/api/import-runs"))
        self.assertEqual(len(summaries), 3)
        self.assertEqual(
            [summary["state"] for summary in summaries].count("undone"),
            2,
        )

    def test_concurrent_facades_atomically_allow_only_one_run_undo(self) -> None:
        run_id = self.store.create_import_run(
            "synthetic-api-concurrent-undo",
            source_name="synthetic.csv",
            source_type="csv",
        )
        source_record_id = self.store.add_source_record(
            run_id,
            source_locator="csv-row:2",
            retained_input="synthetic concurrent undo",
            parse_status="parsed",
        )
        identity_id = self.store.get_or_create_identity(
            "synthetic-api-concurrent-undo-identity"
        )
        self.store.add_normalized_transaction(
            identity_id,
            transaction_date="2026-07-01",
            merchant="SYNTHETIC CONCURRENT UNDO",
            amount_minor=-100,
            currency="CAD",
        )
        self.store.add_occurrence(
            run_id,
            source_record_id=source_record_id,
            identity_id=identity_id,
            amount_minor=-100,
            currency="CAD",
        )
        self.store.add_manual_correction(
            identity_id,
            correction_type="category",
            value="Dining",
        )
        counts_before = self.store.entity_counts()
        correction_ids_before = [
            row["correction_id"]
            for row in self.store.list_category_corrections(identity_id)
        ]
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
            response = api.dispatch(
                "POST",
                f"/api/import-runs/{run_id}/undo",
                headers={"X-Local-Expense-CSRF": CSRF_TOKEN},
            )
            return response.status

        with gated_summary(self.api), gated_summary(other_api):
            with ThreadPoolExecutor(max_workers=2) as executor:
                statuses = sorted(executor.map(undo, (self.api, other_api)))

        self.assertEqual(statuses, [200, 409])
        self.assertEqual(self.store.get_import_run_summary(run_id)["state"], "undone")
        self.assertEqual(self.store.entity_counts(), counts_before)
        self.assertEqual(
            [
                row["correction_id"]
                for row in self.store.list_category_corrections(identity_id)
            ],
            correction_ids_before,
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
