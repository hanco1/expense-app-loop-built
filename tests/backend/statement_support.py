from __future__ import annotations

from pathlib import Path

from backend.statement_import import StatementImportService
from tests.backend.support import StoreTestCase


FIXTURE_DIR = Path(__file__).parent / "fixtures"
CSV_FIXTURE = FIXTURE_DIR / "td-mock-2026-06.csv"
PDF_FIXTURE = FIXTURE_DIR / "td-mock-2026-05.pdf"


class StatementStoreTestCase(StoreTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.importer = StatementImportService(self.store)

    def import_csv(self, filename: str = "td-mock-2026-06.csv") -> str:
        return self.importer.import_bytes(
            CSV_FIXTURE.read_bytes(),
            filename=filename,
            source_type="csv",
        )

    def import_pdf(self, filename: str = "td-mock-2026-05.pdf") -> str:
        return self.importer.import_bytes(
            PDF_FIXTURE.read_bytes(),
            filename=filename,
            source_type="pdf",
        )
