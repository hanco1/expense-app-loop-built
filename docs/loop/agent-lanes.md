# Agent Lanes

| lane | thread_id | role | write_scope | worklog | status | heartbeat | tier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| data-eng | UNVERIFIED | Own statement ingestion, normalization, deduplication, categorization, storage, aggregation, API contracts, OCR boundary, and core tests. | backend/**; contracts/**; scripts/**; tests/backend/**; docs/data/**; docs/loop/lanes/data-eng/** | docs/loop/lanes/data-eng/worklog.md | needs-thread | - | highest |
| frontend | UNVERIFIED | Own local file-selection UX, import review, duplicate resolution, monthly dashboard, charts, manual corrections, and UI tests. | frontend/**; tests/frontend/**; docs/design/**; docs/loop/lanes/frontend/** | docs/loop/lanes/frontend/worklog.md | needs-thread | - | highest |
| product | UNVERIFIED | Own goals, specs, acceptance criteria, milestones, privacy boundaries, and final product judgment. | docs/loop/**; docs/product/**; README.md; .gitignore | docs/loop/lanes/product/worklog.md | needs-thread | - | highest |
| review | UNVERIFIED | Independently review acceptance, regressions, privacy, traceability, misuse paths, and human-QA readiness. | tests/acceptance/**; docs/review/**; docs/loop/lanes/review/** | docs/loop/lanes/review/worklog.md | needs-thread | - | highest |
