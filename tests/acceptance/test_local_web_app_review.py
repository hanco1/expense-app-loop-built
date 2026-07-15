from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from frontend.server import SECURITY_HEADERS, create_server
from tests.frontend.browser_support import BrowserAppTestCase, CSV_FIXTURE


class PublicHttpBoundaryReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.server = create_server(
            Path(self.temporary_directory.name) / "review.sqlite",
            port=0,
            csrf_token="review-http-token",
        )
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.01},
            daemon=True,
        )
        self.thread.start()
        self.host, self.port = self.server.server_address

    def tearDown(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        self.temporary_directory.cleanup()

    def request(
        self,
        method: str,
        *,
        host_header: str | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        connection = http.client.HTTPConnection(self.host, self.port, timeout=5)
        headers = {"Host": host_header} if host_header is not None else {}
        try:
            connection.request(method, "/api/session", headers=headers)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def assert_security_headers(self, headers: dict[str, str]) -> None:
        for name, value in SECURITY_HEADERS.items():
            self.assertEqual(headers.get(name), value, name)
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_every_public_method_obeys_host_rejection_and_security_headers(self) -> None:
        for method in ("PATCH", "TRACE", "CONNECT", "PROPFIND"):
            with self.subTest(method=method, host="non-loopback"):
                status, headers, body = self.request(
                    method,
                    host_header="expense.example.test",
                )
                self.assertEqual(status, 421)
                self.assertEqual(json.loads(body)["error"]["code"], "invalid_host")
                self.assert_security_headers(headers)

            with self.subTest(method=method, host="loopback"):
                status, headers, body = self.request(method)
                self.assertEqual(status, 405)
                self.assertEqual(json.loads(body)["error"]["code"], "method_not_allowed")
                self.assert_security_headers(headers)


class CommittedMutationRefreshReviewTests(BrowserAppTestCase):
    def arm_refresh_failure(
        self,
        mutation_path_fragment: str,
    ) -> tuple[dict[str, object], object]:
        state: dict[str, object] = {
            "committed": False,
            "aborted": 0,
        }

        def observe(response: object) -> None:
            request = response.request
            if (
                request.method == "POST"
                and mutation_path_fragment in response.url
                and 200 <= response.status < 300
            ):
                state["committed"] = True

        def fail_refresh(route: object) -> None:
            if state["committed"] and state["aborted"] == 0:
                state["aborted"] = 1
                route.abort()
            else:
                route.continue_()

        self.page.on("response", observe)
        self.page.route("**/api/import-runs", fail_refresh)
        return state, fail_refresh

    def wait_for_refresh_failure(self, state: dict[str, object]) -> None:
        for _ in range(50):
            if state["aborted"] == 1:
                break
            self.page.wait_for_timeout(100)
        self.assertTrue(state["committed"], "mutation never returned a success response")
        self.assertEqual(state["aborted"], 1, "post-commit canonical refresh was not interrupted")
        self.page.wait_for_timeout(300)

    def restore_refresh(self, route_handler: object) -> None:
        self.page.unroute("**/api/import-runs", route_handler)

    def reload_ready(self) -> None:
        self.page.reload(wait_until="networkidle")
        self.page.locator("#status-region").filter(has_text="Local session ready").wait_for()

    def test_successful_import_is_not_relabeled_failed_when_refresh_is_unavailable(self) -> None:
        self.go_to("imports")
        state, route_handler = self.arm_refresh_failure("/api/import")
        with self.page.expect_response(
            lambda response: response.request.method == "POST"
            and response.url.endswith("/api/import")
        ) as response_info:
            self.page.locator("#statement-files").set_input_files(str(CSV_FIXTURE))
        self.assertEqual(response_info.value.status, 201)
        self.wait_for_refresh_failure(state)
        item = self.page.locator("#import-queue .import-item").first
        reported_state = item.get_attribute("data-state")
        reported_status = self.page.locator("#status-region").inner_text()

        self.restore_refresh(route_handler)
        self.reload_ready()
        self.go_to("imports")
        self.assertEqual(
            self.page.locator(
                f'#run-history-body tr[data-source-name="{CSV_FIXTURE.name}"][data-state="active"]'
            ).count(),
            1,
            "the server committed the run even though the UI reported the follow-up failure",
        )
        self.assertNotEqual(reported_state, "error")
        self.assertIn("imported", reported_status.casefold())

    def test_successful_category_write_keeps_its_commit_acknowledgement_on_refresh_failure(self) -> None:
        self.import_files(CSV_FIXTURE)
        self.go_to("overview")
        loblaws = self.page.locator("#transaction-table-body tr", has_text="LOBLAWS").first
        loblaws.locator("select").select_option("Dining")
        state, route_handler = self.arm_refresh_failure("/category")
        with self.page.expect_response(
            lambda response: response.request.method == "POST"
            and response.url.endswith("/category")
        ) as response_info:
            loblaws.locator('button[data-action="category-correction"]').click()
        self.assertEqual(response_info.value.status, 200)
        self.wait_for_refresh_failure(state)
        reported_status = self.page.locator("#status-region").inner_text()

        self.restore_refresh(route_handler)
        self.reload_ready()
        restored = self.page.locator("#transaction-table-body tr", has_text="LOBLAWS").first
        self.assertEqual(restored.locator("select").input_value(), "Dining")
        self.assertIn("1 history entry", restored.inner_text())
        self.assertIn("changed to Dining", reported_status)

    def test_successful_duplicate_write_is_not_reported_unsaved_on_refresh_failure(self) -> None:
        self.import_files(CSV_FIXTURE)
        self.go_to("duplicates")
        candidate = self.page.locator(".duplicate-card").first
        state, route_handler = self.arm_refresh_failure("/decision")
        with self.page.expect_response(
            lambda response: response.request.method == "POST"
            and response.url.endswith("/decision")
        ) as response_info:
            candidate.locator('button[data-action="duplicate-distinct"]').click()
        self.assertEqual(response_info.value.status, 200)
        self.wait_for_refresh_failure(state)
        reported_status = self.page.locator("#status-region").inner_text()

        self.restore_refresh(route_handler)
        self.reload_ready()
        self.go_to("duplicates")
        restored = self.page.locator(".duplicate-card").first
        self.assertEqual(restored.get_attribute("data-effective-decision"), "distinct")
        self.assertIn("Decision history (1)", restored.inner_text())
        self.assertIn("saved as distinct", reported_status)
        self.assertNotIn("not saved", reported_status.casefold())

    def test_successful_undo_keeps_its_commit_acknowledgement_on_refresh_failure(self) -> None:
        self.import_files(CSV_FIXTURE)
        self.go_to("imports")
        active = self.page.locator(
            f'#run-history-body tr[data-source-name="{CSV_FIXTURE.name}"][data-state="active"]'
        ).first
        run_id = active.get_attribute("data-run-id")
        self.assertIsNotNone(run_id)
        state, route_handler = self.arm_refresh_failure("/undo")
        self.page.once("dialog", lambda dialog: dialog.accept())
        with self.page.expect_response(
            lambda response: response.request.method == "POST"
            and response.url.endswith("/undo")
        ) as response_info:
            active.locator('button[data-action="undo-run"]').click()
        self.assertEqual(response_info.value.status, 200)
        self.wait_for_refresh_failure(state)
        reported_status = self.page.locator("#status-region").inner_text()

        self.restore_refresh(route_handler)
        self.reload_ready()
        self.go_to("imports")
        self.assertEqual(
            self.page.locator(f'#run-history-body tr[data-run-id="{run_id}"]').get_attribute(
                "data-state"
            ),
            "undone",
        )
        self.assertIn("now undone", reported_status)


class FailureFamilyGuardrailReviewTests(BrowserAppTestCase):
    def test_validation_size_parser_and_unexpected_errors_render_as_safe_distinct_text(self) -> None:
        self.go_to("imports")
        outcomes = {
            "validation.csv": (400, "validation_failed", "validation rejected"),
            "oversized.csv": (413, "upload_too_large", "size rejected"),
            "parser.pdf": (422, "import_failed", "parser rejected"),
            "unexpected.csv": (500, "unexpected_failure", "<img src=x onerror=alert(1)>"),
        }

        def reject(route: object) -> None:
            filename = route.request.headers.get("x-statement-filename", "")
            status, code, message = outcomes[filename]
            route.fulfill(
                status=status,
                content_type="application/json",
                body=json.dumps(
                    {
                        "error": {
                            "code": code,
                            "details": {},
                            "message": message,
                        }
                    }
                ),
            )

        self.page.route("**/api/import", reject)
        for index, (filename, (_, code, message)) in enumerate(outcomes.items(), start=1):
            mime_type = "application/pdf" if filename.endswith(".pdf") else "text/csv"
            self.page.locator("#statement-files").set_input_files(
                {
                    "name": filename,
                    "mimeType": mime_type,
                    "buffer": b"synthetic review bytes",
                }
            )
            item = self.page.locator("#import-queue .import-item").nth(index - 1)
            item.locator(".import-state").filter(has_text=code).wait_for()
            self.assertEqual(item.get_attribute("data-state"), "error")
            self.assertIn(message, item.inner_text())

        self.assertEqual(self.page.locator("#import-queue img").count(), 0)


if __name__ == "__main__":
    unittest.main()
