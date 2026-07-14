from __future__ import annotations

import hashlib
import inspect
import io
import logging
import socket
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

import backend.analysis
from backend.analysis import AnalysisService
from backend.persistence import CoreStore
from backend.statement_import import StatementImportService
from tests.backend.analysis_support import AnalysisStoreTestCase
from tests.backend.statement_support import CSV_FIXTURE, PDF_FIXTURE


class AnalysisLocalBoundaryTests(AnalysisStoreTestCase):
    def test_analysis_uses_only_local_in_process_storage_and_does_not_log_rows(self) -> None:
        retained_marker = "SYNTHETIC_ANALYSIS_PRIVATE_MARKER_8675309"
        content = (
            "Date,Description,Debit,Credit,Balance\r\n"
            f"06/01/2026,{retained_marker},1.00,,0.00\r\n"
        ).encode("utf-8")
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        self.addCleanup(root_logger.removeHandler, handler)

        with mock.patch.object(
            socket,
            "socket",
            side_effect=AssertionError("network used"),
        ), mock.patch.object(
            subprocess,
            "run",
            side_effect=AssertionError("subprocess used"),
        ), mock.patch.object(
            subprocess,
            "Popen",
            side_effect=AssertionError("subprocess used"),
        ):
            self.importer.import_bytes(
                content,
                filename="synthetic-local.csv",
                source_type="csv",
            )
            summary = self.analysis.get_month_summary("2026-06")
            self.assertEqual(summary.spending_total_minor, 100)

        handler.flush()
        self.assertNotIn(retained_marker, stream.getvalue())
        source = inspect.getsource(backend.analysis).casefold()
        for forbidden in ("import requests", "import socket", "subprocess.", "telemetry", "pytesseract"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_analysis_writes_only_the_provided_database_and_adds_no_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as local_dir:
            database_path = Path(local_dir) / "analysis.sqlite3"
            store = CoreStore(database_path)
            store.initialize()
            importer = StatementImportService(store)
            importer.import_bytes(
                CSV_FIXTURE.read_bytes(),
                filename="approved.csv",
                source_type="csv",
            )
            AnalysisService(store).get_month_summary("2026-06")
            self.assertEqual(
                {path.resolve() for path in Path(local_dir).iterdir()},
                {database_path.resolve()},
            )
        requirements = Path("backend/requirements.txt").read_text(encoding="utf-8")
        self.assertEqual(requirements.strip(), "pypdf==6.12.2")

    def test_approved_fixture_hashes_are_unchanged(self) -> None:
        self.assertEqual(
            hashlib.sha256(CSV_FIXTURE.read_bytes()).hexdigest().upper(),
            "9F93F107DDD02AEE2FB0A0AE19EB962180C680D1FB06D4D90959C96ED8CD7BAA",
        )
        self.assertEqual(
            hashlib.sha256(PDF_FIXTURE.read_bytes()).hexdigest().upper(),
            "F4B6B524D7C6140EE3F3E24CE87C4A36F0B40619395B5DC17B03F1B99DBC11F8",
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
