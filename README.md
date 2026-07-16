> Part of a controlled A/B comparison: this is the **multi-agent loop** arm (built with the codex-agent-loop-orchestrator skill; the full `docs/loop/` decision ledger is included). See the [solo arm](https://github.com/hanco1/expense-app-solo-session-built) and the [full comparison](https://github.com/hanco1/multi-loops-agents/blob/main/COMPARISON.md).

## Start the local web app

Create a local data directory, then run the loopback-only server from the repository root:

```powershell
New-Item -ItemType Directory -Force local-data
python -m frontend.server --database .\local-data\expenses.sqlite
```

Open the exact URL printed after startup (by default, `http://127.0.0.1:8766`). The database is created at the explicit path you provide, and the server listens only on `127.0.0.1`. If the requested port is occupied, startup exits non-zero without printing a success URL or silently choosing another port. `--port 0` remains available for an ephemeral port, and the printed URL contains the actual allocated port. Stop the process with Ctrl+C.

The MVP accepts TD-style CSV and text-based PDF statements. Scanned PDFs and OCR are not supported yet. Financial data stays in the local process and database.

Run the deterministic frontend and real-browser checks with:

```powershell
python -m unittest discover -s tests/frontend -p "test_*.py" -v
python -m unittest tests.frontend.test_browser_e2e -v
```
