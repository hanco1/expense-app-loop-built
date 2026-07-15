# Handoff

Continuation state for the next session or lane. Keep this current enough that
the next actor can continue from repo files plus the latest message alone.

## Current State

- The SQLite core foundation is accepted. The human has confirmed the browser operating flow and authorized two wholly synthetic TD-style fixtures for committed end-to-end tests.
- Data-eng fixed the named Decimal exceptional-value row loss at commit `e94a09a`; all eight declared iteration-3 commands and the completion gate are green.
- Independent review found that `1e-999999999` silently becomes an active zero-cent transaction. The human authorized iteration 4 with a temporary cap of 7 and required one whitelist-based class-wide correction.
- Data-eng implemented the frozen class-wide whitelist at `06ac048`; product and independent review reproduced backend 31/31 and the full unchanged 282-path acceptance matrix with all nine recorded gates green. Review returned PASS with no scope, privacy, traceability, or misuse finding.
- Product accepted the ingestion slice and restored the standing `max_fix_cycles: 3` in the same checkpoint.
- Product specified the next core slice in `docs/product/analysis-core.md`: deterministic categories, append-only category/duplicate decisions, exact monthly fixture oracles, and typed local contracts.
- Data-eng implemented the analysis core at `8aa5b6f`; all nine recorded commands are exit 0, backend discovery is 45/45, and product independently reproduced the exact May/June, correction, and duplicate checks.
- Independent review found a C3 blocker in iteration 1: three pairwise kept choices could form a cycle and exclude every active identity.
- Data-eng fixed the blocker at `6b9378f` by validating the proposed latest-wins connected component before appending a `same_transaction` decision. The cycle-closing proposal now raises `ValueError` with no history row, accepted decisions survive undo/re-import, and one representative remains included.
- The unchanged review acceptance, all original focused gates, backend discovery 46/46, and the completion gate are green with ten flat iteration-2 evidence records.
- Independent iteration-2 review added the missing selective-support transition: after a valid same-transaction decision, undoing only the designated keeper's run leaves the non-kept identity active in storage but excluded from analysis. The expanded acceptance is red at `tests/acceptance/test_analysis_core_review.py:119`.
- The live raw fix-cycle count is 3 at `max_fix_cycles: 3`; review returned the request to product as BLOCKED instead of dispatching iteration 3. The recommended human decision is a temporary cap of 5 for one bounded final round, restored to 3 after acceptance.
- The human approved iteration 3 with temporary `max_fix_cycles: 5`, required one component-level invariant across every state-changing path, and required review to freeze the complete `component state x operation` matrix before data-eng starts.
- Review froze the complete contract at `6fdc57d`: 55 executable compatible paths plus 20 explicitly impossible/invalid classes. The one post-freeze baseline run produced 13 red paths, 42 green compatible guardrails, and a green manifest guard without dispatching implementation.
- Data-eng implemented the class-wide invariant at `53e57f6`: one latest-same component projection now validates structural keepers, rejects alternate-path distinct contradictions, and selects the active keeper or deterministic fallback without rewriting human history.
- The unchanged frozen acceptance passes 56/56, backend discovery passes 50/50, both frozen hashes are unchanged, all ten iteration-3 evidence records are exit 0, and the completion gate is green. Independent review is now active.
- Independent review found a write-boundary blocker: publicly exported `CoreStore.add_duplicate_decision()` bypasses the projection and commits a zero-keeper history row. The separate boundary probe is red, and raw fix-cycle usage is 5/5.
- The human approved iteration 4 with temporary `max_fix_cycles: 7`. Product strengthened the contract so every exposed decision writer must enforce the same validator atomically, and routed review-first freezing of the complete public-writer/proposal matrix before implementation.
- Review froze the complete iteration-4 boundary contract at `7a99866`: six public import paths, eight proposal classes, and three support states produce 144 executable cases plus six explicit unreachable classes. Baseline 53e57f6 is red in 48 CoreStore-alias invalid-proposal paths and green in 96 compatible paths plus the manifest guard; original matrix remains 56/56.
- Data-eng implemented the centralized underlying write boundary at `9268a5e`. `CoreStore.add_duplicate_decision()` validates the overlaid latest-same graph inside one immediate transaction before allocating a decision ID or appending history; all public import aliases inherit the same rule while valid decisions still append exactly once.
- The unchanged write-boundary matrix passes 145/145, the unchanged component-state matrix passes 56/56, backend discovery passes 52/52, all four frozen hashes match, and all eleven iteration-4 evidence records are exit 0.
- Independent review passed at `329fa51` and delivered at `1e0d0f4`; product accepted implementation `9268a5e` and restored the standing `max_fix_cycles: 3` in the same checkpoint.
- Product specified the next dependency in `docs/product/local-web-api.md`: a local JSON-ready application facade, persistent run listing, exact string money, CSRF protection, and approved-fixture end-to-end checks before the browser UI starts.

## Next Action

- [~] Data-eng implements `REQ-20260715-082547-data-eng` and routes the nine-gate result to independent review.

## Active Request

- request_id: REQ-20260715-082547-data-eng
- owner_lane: data-eng
- iteration: 1

## Blockers

- None. No system dependency is authorized or expected.

## Pending Inbox Deliveries

- None.

## Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` done and verified
- `[!]` blocked

## Done When

- [x] Both approved fixtures import with field-level correctness, bad rows remain visible, exact re-imports do not double-count, legitimate lookalikes remain separate, and each run is inspectable and independently undoable without losing manual corrections.
- [x] May and June fixture summaries match the exact oracle, category buckets reconcile to spending, credits remain outside spending, and human category/duplicate decisions persist through undo and re-import.

## Memory Protocol

The decision memory (`memory/decisions.jsonl`) is an append-only cache, never a
source of truth. Follow this protocol so it survives compaction and never lies:

1. Before deciding, grep `memory/decisions.jsonl` for this request_id and
   follow the `supersedes` chain to the newest live decision.
2. Before trusting any recorded `gate_status`, re-run
   `completion_gate.py --request-id <id>` and `multi_agent_loop_doctor.py`.
   The recorded token is only a hint; the live gate is the authority.
3. If the doctor reports a `stale_decision`, discard that cached decision and
   re-read the live source docs before acting on it.
4. At checkpoint close, append EXACTLY one line via `record_decision.py`. Never
   edit or delete an old line. To change a prior decision, append a new line
   whose `supersedes` names the old `decision_id`.

## Auto-Chain Permission

auto_chain_next_session: false
