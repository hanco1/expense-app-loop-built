# Agent Lanes

| lane | thread_id | role | write_scope | worklog | status | heartbeat | tier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| data-eng | 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | Own statement ingestion, normalization, deduplication, categorization, storage, aggregation, API contracts, OCR boundary, and core tests. | backend/**; contracts/**; scripts/**; tests/backend/**; docs/data/**; docs/loop/lanes/data-eng/** | docs/loop/lanes/data-eng/worklog.md | registered | 2026-07-14T06:30:55Z | highest |
| frontend | 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | Own local file-selection UX, import review, duplicate resolution, monthly dashboard, charts, manual corrections, and UI tests. | frontend/**; tests/frontend/**; docs/design/**; docs/loop/lanes/frontend/** | docs/loop/lanes/frontend/worklog.md | registered | - | highest |
| product | 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | Own goals, specs, acceptance criteria, milestones, privacy boundaries, and final product judgment. | docs/loop/**; docs/product/**; README.md; .gitignore | docs/loop/lanes/product/worklog.md | registered | 2026-07-14T06:40:51Z | highest |
| review | 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | Independently review acceptance, regressions, privacy, traceability, misuse paths, and human-QA readiness. | tests/acceptance/**; docs/review/**; docs/loop/lanes/review/** | docs/loop/lanes/review/worklog.md | registered | 2026-07-14T06:34:26Z | highest |
