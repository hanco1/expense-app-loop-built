# Local browser application

From the repository root, start the app with an explicit local database path:

```powershell
python -m frontend.server --database .\local-data\expenses.sqlite
```

Create the database parent directory first (for example, `New-Item -ItemType Directory -Force local-data`). The listener is fixed to `127.0.0.1`; the stable default URL is `http://127.0.0.1:8766`. Open the exact URL printed after startup. Use `--port 0` only when a caller needs an ephemeral port; the printed URL then includes the allocated port. Stop the process with Ctrl+C.

The listener is exclusive. If the requested port is occupied, startup exits non-zero with a bind error before printing a success URL; it does not silently share the port or choose another one.

Supported inputs are TD-style CSV and text-based PDF statements. Scanned PDFs and OCR are not supported yet. The app serves its assets and API from one local origin and makes no remote requests.

Verification from the repository root:

```powershell
python -m unittest discover -s tests/frontend -p "test_*.py" -v
python -m unittest tests.frontend.test_browser_e2e -v
python -m unittest discover -s tests/backend -p "test_*.py" -v
```

The browser command uses the existing Python Playwright installation and already-present Chromium runtime; it does not install either one.
