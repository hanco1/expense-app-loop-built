from __future__ import annotations

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


if __name__ == "__main__":
    import unittest

    unittest.main()
