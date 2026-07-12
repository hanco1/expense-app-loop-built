from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.persistence import CoreStore


class StoreTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.database_path = Path(self.temp_dir.name) / "core.sqlite3"
        self.store = CoreStore(self.database_path)
        self.store.initialize()

    def add_parsed_occurrence(
        self,
        run_id: str,
        *,
        locator: str,
        identity_fingerprint: str,
        amount_minor: int = -1234,
        currency: str = "CAD",
    ) -> tuple[str, str, str]:
        source_record_id = self.store.add_source_record(
            run_id,
            source_locator=locator,
            retained_input=f"synthetic:{locator}",
            parse_status="parsed",
        )
        identity_id = self.store.get_or_create_identity(identity_fingerprint)
        occurrence_id = self.store.add_occurrence(
            run_id,
            source_record_id=source_record_id,
            identity_id=identity_id,
            amount_minor=amount_minor,
            currency=currency,
        )
        return source_record_id, identity_id, occurrence_id
