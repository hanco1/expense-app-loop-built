from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from frontend.server import create_server


FIXTURE_DIR = Path(__file__).parents[1] / "backend" / "fixtures"
CSV_FIXTURE = FIXTURE_DIR / "td-mock-2026-06.csv"
PDF_FIXTURE = FIXTURE_DIR / "td-mock-2026-05.pdf"


class BrowserAppTestCase(unittest.TestCase):
    viewport = {"width": 1280, "height": 900}

    def setUp(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:  # pragma: no cover - explicit environment gate
            self.fail(f"Existing Python Playwright is required: {error}")

        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "expenses.sqlite"
        self.server = create_server(
            self.database_path,
            port=0,
            csrf_token="frontend-browser-test-token",
            max_upload_bytes=1_000_000,
        )
        self.server_thread = threading.Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.01},
            daemon=True,
        )
        self.server_thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"
        self.playwright = sync_playwright().start()
        try:
            self.browser = self.playwright.chromium.launch(headless=True)
        except Exception as error:  # pragma: no cover - explicit environment gate
            self.playwright.stop()
            self.server.shutdown()
            self.server_thread.join(timeout=5)
            self.server.server_close()
            self.temporary_directory.cleanup()
            self.fail(f"Existing Playwright browser runtime is required: {error}")
        self.page = self.browser.new_page(viewport=self.viewport)
        self.browser_errors: list[str] = []
        self.page.on("pageerror", lambda error: self.browser_errors.append(str(error)))
        self.page.goto(self.base_url, wait_until="networkidle")
        self.page.locator("#status-region").filter(has_text="Local session ready").wait_for()

    def tearDown(self) -> None:
        try:
            self.assertEqual(self.browser_errors, [])
        finally:
            self.browser.close()
            self.playwright.stop()
            self.server.shutdown()
            self.server_thread.join(timeout=5)
            self.server.server_close()
            self.temporary_directory.cleanup()

    def import_files(self, *paths: Path) -> None:
        current_successes = self.page.locator('#import-queue .import-item[data-state="success"]').count()
        self.page.locator("#statement-files").set_input_files([str(path) for path in paths])
        self.page.locator('#import-queue .import-item[data-state="success"]').nth(
            current_successes + len(paths) - 1
        ).wait_for(timeout=60_000)

    def go_to(self, view: str) -> None:
        self.page.locator(f'.nav-button[data-view="{view}"]').click()
        self.page.locator(f"#{view}-title").wait_for()
