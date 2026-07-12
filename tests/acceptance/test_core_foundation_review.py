from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.persistence import CoreStore


class CoreFoundationMisuseTests(unittest.TestCase):
    def test_undone_run_cannot_gain_an_included_occurrence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CoreStore(Path(temp_dir) / "core.sqlite3")
            store.initialize()
            run_id = store.create_import_run("sha256:synthetic-undone-run")

            store.undo_import_run(run_id)
            source_id = store.add_source_record(
                run_id,
                source_locator="csv-row:2",
                retained_input="synthetic,late-row",
                parse_status="parsed",
            )
            identity_id = store.get_or_create_identity("txn:synthetic-late-row")
            occurrence_id = store.add_occurrence(
                run_id,
                source_record_id=source_id,
                identity_id=identity_id,
                amount_minor=-100,
                currency="CAD",
            )

            store.undo_import_run(run_id)

            self.assertEqual(store.get_import_run(run_id)["state"], "undone")
            self.assertEqual(
                store.get_occurrence(occurrence_id)["inclusion_state"],
                "excluded",
                "an undone run must not retain an included occurrence",
            )


if __name__ == "__main__":
    unittest.main()
