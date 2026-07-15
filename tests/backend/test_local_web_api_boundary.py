from __future__ import annotations

import ast
import logging
import socket
import subprocess
from pathlib import Path
from unittest.mock import patch

from tests.backend.local_web_api_support import LocalWebApiTestCase


class LocalWebApiBoundaryTests(LocalWebApiTestCase):
    def test_facade_has_no_listener_network_ocr_subprocess_or_telemetry_surface(self) -> None:
        source_path = Path(__file__).parents[2] / "backend" / "local_web_api.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertTrue(
            {
                "socket",
                "http",
                "urllib",
                "requests",
                "subprocess",
                "pytesseract",
                "telemetry",
            }.isdisjoint(imports)
        )
        self.assertNotIn("Access-Control-Allow-Origin", source)
        self.assertNotIn("retained_input", source)
        self.assertNotIn("logging", imports)

    def test_fixture_crossing_uses_only_local_process_and_provided_database(self) -> None:
        with (
            patch.object(socket, "socket", side_effect=AssertionError("network")),
            patch.object(subprocess, "run", side_effect=AssertionError("subprocess")),
            patch.object(subprocess, "Popen", side_effect=AssertionError("subprocess")),
            patch.object(logging.Logger, "_log") as log_call,
        ):
            self.import_fixture("csv")
            self.import_fixture("pdf")
            self.data(self.api.dispatch("GET", "/api/months/2026-06"))
        log_call.assert_not_called()
        files = [
            path
            for path in Path(self._temporary_directory.name).iterdir()
            if path.is_file()
        ]
        self.assertEqual(files, [self.database_path])
        requirements = (
            Path(__file__).parents[2] / "backend" / "requirements.txt"
        ).read_text(encoding="utf-8")
        self.assertEqual(requirements.strip(), "pypdf==6.12.2")


if __name__ == "__main__":
    import unittest

    unittest.main()
