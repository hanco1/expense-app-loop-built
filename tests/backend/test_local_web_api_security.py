from __future__ import annotations

from tests.backend.local_web_api_support import (
    CSV_FIXTURE,
    CSRF_TOKEN,
    LocalWebApiTestCase,
)
from contracts.local_web_api import LocalWebRequest, LocalWebResponse


class LocalWebApiSecurityTests(LocalWebApiTestCase):
    def test_session_is_stable_local_and_has_no_cors_headers(self) -> None:
        first = self.api.dispatch("GET", "/api/session")
        second = self.api.dispatch("GET", "/api/session")

        self.assertEqual(first.status, 200)
        self.assertEqual(first.body, second.body)
        session = first.json()["data"]
        self.assertEqual(session["csrf_token"], CSRF_TOKEN)
        self.assertTrue(session["local_only"])
        self.assertEqual(session["supported_source_types"], ["csv", "pdf"])
        self.assertEqual(session["parser_modes"], {"csv": "text", "pdf": "text"})
        self.assertNotIn("Access-Control-Allow-Origin", first.headers)
        self.assertEqual(first.headers["Cache-Control"], "no-store")

        typed = self.api.handle(LocalWebRequest("GET", "/api/session"))
        self.assertIsInstance(typed, LocalWebResponse)
        self.assertEqual(typed.body, first.body)

    def test_every_mutation_rejects_missing_or_wrong_csrf_before_write(self) -> None:
        counts_before = self.store.entity_counts()
        headers = {
            "Content-Type": "text/csv",
            "X-Statement-Filename": CSV_FIXTURE.name,
        }
        missing = self.api.dispatch(
            "POST",
            "/api/import",
            headers=headers,
            body=CSV_FIXTURE.read_bytes(),
        )
        headers["X-Local-Expense-CSRF"] = "wrong-token"
        wrong = self.api.dispatch(
            "POST",
            "/api/import",
            headers=headers,
            body=CSV_FIXTURE.read_bytes(),
        )

        self.assertEqual(missing.status, 403)
        self.assertEqual(wrong.status, 403)
        self.assertEqual(missing.json()["error"]["code"], "csrf_failed")
        self.assertEqual(self.store.entity_counts(), counts_before)


if __name__ == "__main__":
    import unittest

    unittest.main()
