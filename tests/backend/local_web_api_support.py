from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from backend.local_web_api import LocalWebApi
from backend.persistence import CoreStore
from contracts.local_web_api import LocalWebResponse


FIXTURE_DIR = Path(__file__).parent / "fixtures"
CSV_FIXTURE = FIXTURE_DIR / "td-mock-2026-06.csv"
PDF_FIXTURE = FIXTURE_DIR / "td-mock-2026-05.pdf"
CSRF_TOKEN = "test-local-csrf-token"


class LocalWebApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self._temporary_directory.name) / "expenses.sqlite"
        self.store = CoreStore(self.database_path)
        self.store.initialize()
        self.api = LocalWebApi(
            self.store,
            csrf_token=CSRF_TOKEN,
            max_upload_bytes=1_000_000,
        )

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    @staticmethod
    def data(response: LocalWebResponse, status: int = 200) -> Any:
        if response.status != status:
            raise AssertionError(response.json())
        return response.json()["data"]

    def import_fixture(
        self,
        kind: str,
        *,
        filename: str | None = None,
    ) -> dict[str, Any]:
        if kind == "csv":
            fixture = CSV_FIXTURE
            media_type = "text/csv"
        elif kind == "pdf":
            fixture = PDF_FIXTURE
            media_type = "application/pdf"
        else:
            raise ValueError("kind must be csv or pdf")
        response = self.api.dispatch(
            "POST",
            "/api/import",
            headers={
                "Content-Type": media_type,
                "X-Local-Expense-CSRF": CSRF_TOKEN,
                "X-Statement-Filename": filename or fixture.name,
            },
            body=fixture.read_bytes(),
        )
        return self.data(response, 201)

    def post_json(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        csrf_token: str | None = CSRF_TOKEN,
    ) -> LocalWebResponse:
        headers = {"Content-Type": "application/json"}
        if csrf_token is not None:
            headers["X-Local-Expense-CSRF"] = csrf_token
        return self.api.dispatch(
            "POST",
            path,
            headers=headers,
            body=json.dumps(payload, sort_keys=True).encode("utf-8"),
        )

    def seed_duplicate_group(self, labels: str = "ABC") -> dict[str, str]:
        identities: dict[str, str] = {}
        for index, label in enumerate(labels, start=1):
            run_id = self.store.create_import_run(
                f"synthetic-api-duplicate-run:{label}",
                source_name=f"synthetic-{label}.csv",
                source_type="csv",
            )
            source_record_id = self.store.add_source_record(
                run_id,
                source_locator="csv-row:2",
                retained_input=f"synthetic duplicate {label}",
                parse_status="parsed",
            )
            identity_id = self.store.get_or_create_identity(
                f"synthetic-api-duplicate-identity:{label}"
            )
            self.store.add_normalized_transaction(
                identity_id,
                transaction_date="2026-06-30",
                merchant="SYNTHETIC API DUPLICATE",
                amount_minor=-100,
                currency="CAD",
            )
            self.store.link_suspected_duplicates(identity_id)
            self.store.add_occurrence(
                run_id,
                source_record_id=source_record_id,
                identity_id=identity_id,
                amount_minor=-100,
                currency="CAD",
            )
            identities[label] = identity_id
        return identities

    def duplicate_for(
        self,
        left_identity_id: str,
        right_identity_id: str,
    ) -> dict[str, Any]:
        expected = {left_identity_id, right_identity_id}
        for candidate in self.data(self.api.dispatch("GET", "/api/duplicates")):
            actual = {
                candidate["left"]["identity_id"],
                candidate["right"]["identity_id"],
            }
            if actual == expected:
                return candidate
        raise AssertionError(f"duplicate candidate not found: {expected}")
