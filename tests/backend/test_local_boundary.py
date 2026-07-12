from __future__ import annotations

import io
import logging
import socket
import tempfile
from pathlib import Path
from unittest import mock

from backend.persistence import CoreStore
from tests.backend.support import StoreTestCase


class LocalBoundaryTests(StoreTestCase):
    def test_core_persistence_never_opens_a_network_socket(self) -> None:
        isolated_database = Path(self.temp_dir.name) / "offline.sqlite3"
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network used")):
            store = CoreStore(isolated_database)
            store.initialize()
            run_id = store.create_import_run("sha256:offline")
            store.add_source_record(
                run_id,
                source_locator="csv-row:2",
                retained_input="synthetic,offline",
                parse_status="failed",
                error_code="SYNTHETIC_FAILURE",
            )

    def test_retained_source_content_is_not_written_to_logs(self) -> None:
        secret_synthetic_content = "SYNTHETIC_PRIVATE_ROW_8675309"
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        self.addCleanup(root_logger.removeHandler, handler)

        run_id = self.store.create_import_run("sha256:private-synthetic")
        self.store.add_source_record(
            run_id,
            source_locator="csv-row:7",
            retained_input=secret_synthetic_content,
            parse_status="failed",
            error_code="INVALID_SYNTHETIC_ROW",
        )
        self.store.get_source_record(
            self.store.list_source_records(run_id)[0]["source_record_id"]
        )

        handler.flush()
        self.assertNotIn(secret_synthetic_content, stream.getvalue())

    def test_only_the_provided_database_path_is_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as local_dir:
            local_path = Path(local_dir) / "provided.sqlite3"
            store = CoreStore(local_path)
            store.initialize()
            store.create_import_run("sha256:local-only")
            self.assertEqual(
                {path.resolve() for path in Path(local_dir).iterdir()},
                {local_path.resolve()},
            )


if __name__ == "__main__":
    import unittest

    unittest.main()
