from __future__ import annotations

import argparse
import ipaddress
import json
import socket
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from backend.local_web_api import DEFAULT_MAX_UPLOAD_BYTES, LocalWebApi
from contracts.local_web_api import LocalWebRequest, LocalWebResponse


LOOPBACK_HOST = "127.0.0.1"
DEFAULT_PORT = 8766
STATIC_DIR = Path(__file__).with_name("static")
STATIC_FILES: Mapping[str, tuple[str, str]] = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}
SECURITY_HEADERS: Mapping[str, str] = {
    "Cache-Control": "no-store",
    "Content-Security-Policy": (
        "default-src 'none'; base-uri 'none'; connect-src 'self'; "
        "font-src 'self'; form-action 'self'; frame-ancestors 'none'; "
        "img-src 'self'; object-src 'none'; script-src 'self'; "
        "style-src 'self'"
    ),
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": "camera=(), geolocation=(), microphone=()",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


class ListenerBindError(OSError):
    """Raised when the requested loopback endpoint cannot be bound exclusively."""


class LocalExpenseHTTPServer(ThreadingHTTPServer):
    """HTTP listener that is structurally pinned to IPv4 loopback."""

    allow_reuse_address = False
    allow_reuse_port = False
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        api: LocalWebApi,
        *,
        static_dir: Path = STATIC_DIR,
    ) -> None:
        host, port = server_address
        if host != LOOPBACK_HOST:
            raise ValueError("listener host must be exactly 127.0.0.1")
        if type(port) is not int or not 0 <= port <= 65535:
            raise ValueError("port must be an integer from 0 through 65535")
        if not isinstance(api, LocalWebApi):
            raise TypeError("api must be a LocalWebApi")
        resolved_static_dir = Path(static_dir).resolve()
        if not resolved_static_dir.is_dir():
            raise FileNotFoundError(
                f"static asset directory does not exist: {resolved_static_dir}"
            )
        self.api = api
        self.static_dir = resolved_static_dir
        self.max_request_bytes = api.max_upload_bytes
        try:
            super().__init__((host, port), LocalExpenseRequestHandler)
        except OSError as error:
            raise ListenerBindError(
                f"unable to bind exclusive listener on {host}:{port}: {error}"
            ) from error

    def server_bind(self) -> None:
        # Windows requires this option before bind to prevent another process
        # using SO_REUSEADDR from silently sharing the requested endpoint.
        exclusive_address_use = getattr(socket, "SO_EXCLUSIVEADDRUSE", None)
        if exclusive_address_use is not None:
            self.socket.setsockopt(socket.SOL_SOCKET, exclusive_address_use, 1)
        super().server_bind()


class LocalExpenseRequestHandler(BaseHTTPRequestHandler):
    """Serve fixed assets and forward API bytes without application logging."""

    server: LocalExpenseHTTPServer
    protocol_version = "HTTP/1.1"
    server_version = "LocalExpense"
    sys_version = ""

    def version_string(self) -> str:
        return self.server_version

    def __getattr__(self, name: str) -> object:
        # BaseHTTPRequestHandler otherwise sends its default HTML 501 before
        # our Host validation and security headers run. Route every parsed
        # public method through the same Host-first structured boundary.
        if name.startswith("do_"):
            return self._method_not_allowed
        raise AttributeError(name)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if not self._valid_host():
            self._write_error(
                HTTPStatus.MISDIRECTED_REQUEST,
                "invalid_host",
                "request Host must identify a loopback origin",
            )
            return
        if self.path.startswith("/api/"):
            self._forward_to_api(b"")
            return
        static = STATIC_FILES.get(self.path)
        if static is None:
            self._write_error(
                HTTPStatus.NOT_FOUND,
                "not_found",
                "requested resource was not found",
            )
            return
        filename, content_type = static
        asset_path = self.server.static_dir / filename
        try:
            body = asset_path.read_bytes()
        except OSError:
            self._write_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "static_asset_unavailable",
                "a local application asset is unavailable",
            )
            return
        self._write_response(HTTPStatus.OK, {"Content-Type": content_type}, body)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if not self._valid_host():
            self._write_error(
                HTTPStatus.MISDIRECTED_REQUEST,
                "invalid_host",
                "request Host must identify a loopback origin",
            )
            return
        if not self.path.startswith("/api/"):
            self._write_error(
                HTTPStatus.METHOD_NOT_ALLOWED,
                "method_not_allowed",
                "method is not allowed for this resource",
            )
            return
        body = self._read_request_body()
        if body is None:
            return
        self._forward_to_api(body)

    def do_HEAD(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._method_not_allowed()

    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._method_not_allowed()

    def do_PUT(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._method_not_allowed()

    def do_DELETE(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._method_not_allowed()

    def _method_not_allowed(self) -> None:
        if not self._valid_host():
            self._write_error(
                HTTPStatus.MISDIRECTED_REQUEST,
                "invalid_host",
                "request Host must identify a loopback origin",
            )
            return
        self._write_error(
            HTTPStatus.METHOD_NOT_ALLOWED,
            "method_not_allowed",
            "request method is not supported",
        )

    def _valid_host(self) -> bool:
        values = self.headers.get_all("Host", failobj=[])
        if len(values) != 1:
            return False
        authority = values[0]
        if (
            not authority
            or authority != authority.strip()
            or any(character.isspace() for character in authority)
            or any(character in authority for character in "/?#@,%")
        ):
            return False
        if authority.startswith("["):
            closing_bracket = authority.find("]")
            if closing_bracket < 0:
                return False
            suffix = authority[closing_bracket + 1 :]
            if suffix and (
                not suffix.startswith(":")
                or len(suffix) == 1
                or not suffix[1:].isdigit()
            ):
                return False
        elif authority.count(":") > 1:
            return False
        elif ":" in authority:
            _, port_text = authority.rsplit(":", 1)
            if not port_text or not port_text.isdigit():
                return False
        try:
            parsed = urlsplit(f"//{authority}")
            hostname = parsed.hostname
            port = parsed.port
        except ValueError:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        if not hostname:
            return False
        if port is not None and not 1 <= port <= 65535:
            return False
        if hostname.casefold() == "localhost":
            return True
        try:
            return ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            return False

    def _read_request_body(self) -> bytes | None:
        if self.headers.get("Transfer-Encoding") is not None:
            self._write_error(
                HTTPStatus.BAD_REQUEST,
                "invalid_http_body",
                "transfer-encoded request bodies are not supported",
            )
            return None
        lengths = self.headers.get_all("Content-Length", failobj=[])
        if len(lengths) != 1:
            self._write_error(
                HTTPStatus.BAD_REQUEST,
                "invalid_http_body",
                "one valid Content-Length header is required",
            )
            return None
        try:
            length = int(lengths[0], 10)
        except ValueError:
            length = -1
        if length < 0:
            self._write_error(
                HTTPStatus.BAD_REQUEST,
                "invalid_http_body",
                "Content-Length must be a non-negative integer",
            )
            return None
        if length > self.server.max_request_bytes:
            self.close_connection = True
            self._write_error(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "upload_too_large",
                "request body exceeds the configured local limit",
                {"max_upload_bytes": self.server.max_request_bytes},
            )
            return None
        body = self.rfile.read(length)
        if len(body) != length:
            self._write_error(
                HTTPStatus.BAD_REQUEST,
                "invalid_http_body",
                "request body ended before Content-Length bytes arrived",
            )
            return None
        return body

    def _forward_to_api(self, body: bytes) -> None:
        headers: dict[str, str] = {}
        for name in (
            "Content-Type",
            "X-Local-Expense-CSRF",
            "X-Statement-Filename",
        ):
            values = self.headers.get_all(name, failobj=[])
            if len(values) > 1:
                self._write_error(
                    HTTPStatus.BAD_REQUEST,
                    "invalid_http_headers",
                    "request contains duplicate application headers",
                )
                return
            if values:
                headers[name] = values[0]
        response = self.server.api.handle(
            LocalWebRequest(
                method=self.command,
                path=self.path,
                headers=headers,
                body=body,
            )
        )
        self._write_response(response.status, response.headers, response.body)

    def _write_error(
        self,
        status: int,
        code: str,
        message: str,
        details: Mapping[str, object] | None = None,
    ) -> None:
        body = json.dumps(
            {
                "error": {
                    "code": code,
                    "details": dict(details or {}),
                    "message": message,
                }
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        self._write_response(
            status,
            {"Content-Type": "application/json; charset=utf-8"},
            body,
        )

    def _write_response(
        self,
        status: int,
        headers: Mapping[str, str],
        body: bytes,
    ) -> None:
        self.send_response(int(status))
        merged = dict(SECURITY_HEADERS)
        merged.update(headers)
        for name, value in merged.items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            pass

    def log_message(self, format: str, *args: object) -> None:
        # Request paths, headers, bodies, transaction data, and tokens must not
        # enter application logs. Startup prints only the approved local facts.
        return


def create_server(
    database_path: str | Path,
    *,
    host: str = LOOPBACK_HOST,
    port: int = DEFAULT_PORT,
    max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
    csrf_token: str | None = None,
) -> LocalExpenseHTTPServer:
    """Build a loopback server; port 0 selects an ephemeral test port."""

    if host != LOOPBACK_HOST:
        raise ValueError("listener host must be exactly 127.0.0.1")
    api = LocalWebApi.from_database(
        database_path,
        max_upload_bytes=max_upload_bytes,
        csrf_token=csrf_token,
    )
    return LocalExpenseHTTPServer((host, port), api)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the local Canadian expense analysis web application.",
    )
    parser.add_argument(
        "--database",
        required=True,
        type=Path,
        help="local SQLite database file (its parent directory must exist)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"loopback TCP port; default {DEFAULT_PORT}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        server = create_server(args.database, port=args.port)
    except ListenerBindError as error:
        print(
            f"Unable to bind local expense app at {LOOPBACK_HOST}:{args.port}: {error}",
            file=sys.stderr,
            flush=True,
        )
        return 1
    address, bound_port = server.server_address
    print(f"Local expense app: http://{address}:{bound_port}", flush=True)
    print(f"Database: {Path(args.database).resolve()}", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("Stopping local expense app.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEFAULT_PORT",
    "ListenerBindError",
    "LOOPBACK_HOST",
    "LocalExpenseHTTPServer",
    "SECURITY_HEADERS",
    "create_server",
    "main",
]
