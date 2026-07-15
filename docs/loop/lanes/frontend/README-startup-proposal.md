# Proposed Root README Startup Text

Product owns `README.md`. The following exact section is proposed for insertion:

````markdown
## Start the local web app

Create a local data directory, then run the loopback-only server from the repository root:

```powershell
New-Item -ItemType Directory -Force local-data
python -m frontend.server --database .\local-data\expenses.sqlite
```

Open `http://127.0.0.1:8765`. The database is created at the explicit path you provide, and the server listens only on `127.0.0.1`. Stop it with Ctrl+C.

The MVP accepts TD-style CSV and text-based PDF statements. Scanned PDFs and OCR are not supported yet. Financial data stays in the local process and database.

Run the deterministic frontend and real-browser checks with:

```powershell
python -m unittest discover -s tests/frontend -p "test_*.py" -v
python -m unittest tests.frontend.test_browser_e2e -v
```
````
