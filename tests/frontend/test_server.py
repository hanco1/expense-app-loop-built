from __future__ import annotations

import contextlib
import hashlib
import http.client
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path

from frontend.server import LOOPBACK_HOST, SECURITY_HEADERS, create_server


FIXTURE_DIR = Path(__file__).parents[1] / "backend" / "fixtures"
CSV_FIXTURE = FIXTURE_DIR / "td-mock-2026-06.csv"


class LoopbackServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "expenses.sqlite"
        self.server = create_server(
            self.database_path,
            port=0,
            csrf_token="frontend-server-test-token",
            max_upload_bytes=1_000_000,
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
        self.assertFalse(self.thread.is_alive(), "loopback listener did not stop cleanly")
        self.server.server_close()
        self.temporary_directory.cleanup()

    def request(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        connection = http.client.HTTPConnection(self.host, self.port, timeout=10)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            response_body = response.read()
            return response.status, dict(response.getheaders()), response_body
        finally:
            connection.close()

    def test_listener_assets_api_and_headers_stay_on_one_loopback_origin(self) -> None:
        self.assertEqual(self.host, LOOPBACK_HOST)
        with self.assertRaisesRegex(ValueError, "exactly 127.0.0.1"):
            create_server(self.database_path, host="0.0.0.0", port=0)

        status, headers, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Monthly Expense Review", body)
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        for name, value in SECURITY_HEADERS.items():
            self.assertEqual(headers[name], value)
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertNotIn(b"http://", body)
        self.assertNotIn(b"https://", body)

        for path, content_type in (
            ("/app.css", "text/css; charset=utf-8"),
            ("/app.js", "text/javascript; charset=utf-8"),
        ):
            asset_status, asset_headers, asset_body = self.request("GET", path)
            self.assertEqual(asset_status, 200)
            self.assertEqual(asset_headers["Content-Type"], content_type)
            self.assertTrue(asset_body)
            self.assertEqual(asset_headers["Content-Security-Policy"], SECURITY_HEADERS["Content-Security-Policy"])

        api_status, api_headers, api_body = self.request("GET", "/api/session")
        self.assertEqual(api_status, 200)
        session = json.loads(api_body)["data"]
        self.assertTrue(session["local_only"])
        self.assertEqual(session["csrf_token"], "frontend-server-test-token")
        self.assertEqual(api_headers["Content-Security-Policy"], SECURITY_HEADERS["Content-Security-Policy"])
        self.assertNotIn("Access-Control-Allow-Origin", api_headers)

    def test_invalid_non_loopback_host_is_rejected_before_static_or_api_dispatch(self) -> None:
        for path in ("/", "/api/session"):
            status, _, body = self.request(
                "GET",
                path,
                headers={"Host": "expense.example.test"},
            )
            self.assertEqual(status, 421)
            self.assertEqual(json.loads(body)["error"]["code"], "invalid_host")

        status, _, body = self.request(
            "GET",
            "/api/session",
            headers={"Host": "127.0.0.1.example.test"},
        )
        self.assertEqual(status, 421)
        self.assertEqual(json.loads(body)["error"]["code"], "invalid_host")

        status, _, body = self.request(
            "GET",
            "/api/session",
            headers={"Host": "127.0.0.1:"},
        )
        self.assertEqual(status, 421)
        self.assertEqual(json.loads(body)["error"]["code"], "invalid_host")

        status, _, body = self.request(
            "GET",
            "/api/session",
            headers={"Host": "127.0.0.1:not-a-port"},
        )
        self.assertEqual(status, 421)
        self.assertEqual(json.loads(body)["error"]["code"], "invalid_host")

    def test_csrf_and_exact_statement_bytes_cross_the_real_adapter_without_logs(self) -> None:
        fixture_bytes = CSV_FIXTURE.read_bytes()
        expected_hash = "9F93F107DDD02AEE2FB0A0AE19EB962180C680D1FB06D4D90959C96ED8CD7BAA"
        self.assertEqual(hashlib.sha256(fixture_bytes).hexdigest().upper(), expected_hash)
        headers = {
            "Content-Type": "text/csv",
            "X-Statement-Filename": CSV_FIXTURE.name,
        }

        denied_status, _, denied_body = self.request(
            "POST",
            "/api/import",
            body=fixture_bytes,
            headers=headers,
        )
        self.assertEqual(denied_status, 403)
        self.assertEqual(json.loads(denied_body)["error"]["code"], "csrf_failed")

        private_marker = b"BROKEN ROW NO AMOUNT"
        self.assertIn(private_marker, fixture_bytes)
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()
        with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(captured_stderr):
            imported_status, _, imported_body = self.request(
                "POST",
                "/api/import",
                body=fixture_bytes,
                headers={
                    **headers,
                    "X-Local-Expense-CSRF": "frontend-server-test-token",
                },
            )
        self.assertEqual(imported_status, 201)
        imported = json.loads(imported_body)["data"]
        self.assertEqual(
            {
                key: imported["summary"][key]
                for key in (
                    "source_record_count",
                    "parsed_count",
                    "failed_count",
                    "occurrence_count",
                )
            },
            {
                "source_record_count": 23,
                "parsed_count": 22,
                "failed_count": 1,
                "occurrence_count": 22,
            },
        )
        failed = [row for row in imported["records"] if row["parse_status"] == "failed"]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["error_code"], "missing_amount")
        self.assertNotIn(private_marker.decode("ascii"), captured_stdout.getvalue())
        self.assertNotIn(private_marker.decode("ascii"), captured_stderr.getvalue())
        self.assertNotIn("frontend-server-test-token", captured_stdout.getvalue())
        self.assertNotIn("frontend-server-test-token", captured_stderr.getvalue())

    def test_transport_rejects_oversized_and_unsupported_methods_without_cors(self) -> None:
        status, headers, body = self.request(
            "POST",
            "/api/import",
            body=b"x" * 1_000_001,
            headers={
                "Content-Type": "text/csv",
                "X-Statement-Filename": "oversized.csv",
                "X-Local-Expense-CSRF": "frontend-server-test-token",
            },
        )
        self.assertEqual(status, 413)
        self.assertEqual(json.loads(body)["error"]["code"], "upload_too_large")
        self.assertNotIn("Access-Control-Allow-Origin", headers)

        status, headers, body = self.request("OPTIONS", "/api/session")
        self.assertEqual(status, 405)
        self.assertEqual(json.loads(body)["error"]["code"], "method_not_allowed")
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_run_history_survives_a_new_listener_process_facade(self) -> None:
        fixture_bytes = CSV_FIXTURE.read_bytes()
        status, _, body = self.request(
            "POST",
            "/api/import",
            body=fixture_bytes,
            headers={
                "Content-Type": "text/csv",
                "X-Statement-Filename": CSV_FIXTURE.name,
                "X-Local-Expense-CSRF": "frontend-server-test-token",
            },
        )
        self.assertEqual(status, 201)
        run_id = json.loads(body)["data"]["summary"]["run_id"]

        recreated = create_server(
            self.database_path,
            port=0,
            csrf_token="recreated-frontend-server-token",
            max_upload_bytes=1_000_000,
        )
        recreated_thread = threading.Thread(
            target=recreated.serve_forever,
            kwargs={"poll_interval": 0.01},
            daemon=True,
        )
        recreated_thread.start()
        recreated_host, recreated_port = recreated.server_address
        connection = http.client.HTTPConnection(recreated_host, recreated_port, timeout=10)
        try:
            connection.request("GET", "/api/import-runs")
            response = connection.getresponse()
            payload = json.loads(response.read())
        finally:
            connection.close()
            recreated.shutdown()
            recreated_thread.join(timeout=5)
            recreated.server_close()
        self.assertFalse(recreated_thread.is_alive())
        self.assertEqual(response.status, 200)
        self.assertEqual([summary["run_id"] for summary in payload["data"]], [run_id])


if __name__ == "__main__":
    unittest.main()
