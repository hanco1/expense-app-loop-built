from __future__ import annotations

import inspect
import io
import logging
import socket
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from backend.statement_import import StatementImportService
from contracts.statement_import import StatementParser
from tests.backend.statement_support import CSV_FIXTURE, PDF_FIXTURE, StatementStoreTestCase


class StatementImportLocalBoundaryTests(StatementStoreTestCase):
    def test_boundary_requires_bytes_filename_and_explicit_supported_type(self) -> None:
        parameters = inspect.signature(StatementImportService.import_bytes).parameters
        self.assertIn("content", parameters)
        self.assertIn("filename", parameters)
        self.assertIn("source_type", parameters)
        self.assertNotIn("path", parameters)

        for invalid_content in (str(CSV_FIXTURE), CSV_FIXTURE, bytearray(b"data")):
            with self.subTest(content_type=type(invalid_content).__name__):
                with self.assertRaises(TypeError):
                    self.importer.import_bytes(
                        invalid_content,
                        filename="display.csv",
                        source_type="csv",
                    )
        with self.assertRaises(ValueError):
            self.importer.import_bytes(
                CSV_FIXTURE.read_bytes(),
                filename="display.csv",
                source_type="ocr",
            )

        descriptors = self.importer.parser_descriptors()
        self.assertEqual(set(descriptors), {"csv", "pdf"})
        self.assertTrue(all(descriptor["mode"] == "text" for descriptor in descriptors.values()))
        self.assertTrue(
            all(isinstance(parser, StatementParser) for parser in self.importer.parsers.values())
        )

    def test_import_has_no_network_subprocess_or_raw_content_logging(self) -> None:
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        self.addCleanup(root_logger.removeHandler, handler)

        with (
            mock.patch.object(socket, "socket", side_effect=AssertionError("network used")),
            mock.patch.object(subprocess, "run", side_effect=AssertionError("subprocess used")),
        ):
            self.importer.import_bytes(
                PDF_FIXTURE.read_bytes(),
                filename="local-display.pdf",
                source_type="pdf",
            )

        handler.flush()
        self.assertNotIn("TD CANADA TRUST - MOCK STATEMENT", stream.getvalue())
        self.assertNotIn("E-TRANSFER RECEIVED J. WU", stream.getvalue())

    def test_text_pdf_dependency_is_project_scoped(self) -> None:
        dependency_file = Path("backend/requirements.txt")
        self.assertTrue(dependency_file.is_file())
        dependencies = dependency_file.read_text(encoding="utf-8").splitlines()
        self.assertIn("pypdf==6.12.2", dependencies)
        self.assertFalse(any("ocr" in dependency.lower() for dependency in dependencies))


if __name__ == "__main__":
    unittest.main()
