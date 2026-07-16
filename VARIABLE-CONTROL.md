# Variable control — how this A/B comparison was kept fair

This file exists so you don't have to take the comparison on faith. It records exactly what each of the two
builds received, what was held constant, and — honestly — the ways the two runs were *not* identical.
The **same file is committed to both repositories**, so it reads identically from either side.

Two builds of the same local-first Canadian expense-analysis web app:

- **Solo arm** → https://github.com/hanco1/expense-app-solo-session-built — one plain `codex exec` session.
- **Loop arm** → https://github.com/hanco1/expense-app-loop-built — the `codex-agent-loop-orchestrator`
  multi-agent loop.

Both used codex **`gpt-5.6-sol` at `xhigh`** reasoning effort. Full scored comparison:
https://github.com/hanco1/multi-loops-agents/blob/main/COMPARISON.md

## What was held constant

| Held constant | Detail |
|---|---|
| Requirements | The same objective, the same 8 hard invariants, the same "done-when" list, the same operating flow |
| Test fixtures | The same two synthetic TD-style statements: `td-mock-2026-06.csv` and `td-mock-2026-05.pdf` |
| Model + effort | `gpt-5.6-sol`, `xhigh`, for every session in both arms |
| Reviewer | The exact same 5-dimension rubric scored both codebases; every blocker/major finding was re-derived by an independent adversarial verifier before it counted |

## The exact inputs — read them yourself

- **Solo arm received** the single build brief, verbatim:
  [build prompt](https://github.com/hanco1/expense-app-solo-session-built/blob/main/docs/build-prompt.md),
  and again inside the real
  [session transcript](https://github.com/hanco1/expense-app-solo-session-built/blob/main/docs/session-transcript.md)
  — role-tagged `USER` / `ASSISTANT`, extracted verbatim from the actual `codex exec` session (the single user
  prompt, codex's turns, and a summary of every shell/file tool call).
- **Loop arm received** the same requirements as its objective + invariants, crystallized into
  [`docs/loop/goal.md`](https://github.com/hanco1/expense-app-loop-built/blob/main/docs/loop/goal.md) and
  [`docs/loop/constraints.md`](https://github.com/hanco1/expense-app-loop-built/blob/main/docs/loop/constraints.md).
  The loop's full "conversation" is not a single chat log — it is the complete inter-agent message ledger under
  [`docs/loop/messages/`](https://github.com/hanco1/expense-app-loop-built/tree/main/docs/loop/messages) plus
  the append-only
  [`docs/loop/loop-run-log.md`](https://github.com/hanco1/expense-app-loop-built/blob/main/docs/loop/loop-run-log.md).
  That ledger IS the loop arm's transcript.

You can diff the solo brief's "What it must do" / "Hard rules" against the loop's `goal.md`
`## Done When` / `## Invariants` and confirm they are the same requirements.

## Where the two runs were NOT identical (stated honestly)

A fair comparison names its own asymmetries. There are three, all documented, none hidden:

1. **The prompt text is not byte-identical — the requirements are.** The loop gathers requirements by
   *interviewing the human* (a short intake Q&A that produced `goal.md`'s invariants). A single non-interactive
   `codex exec` session cannot interview anyone, so the solo brief **folds those same intake answers in as
   plain text** (e.g. the "data must persist locally" decision). This was a deliberate control choice: it gives
   both arms the *same information* rather than penalizing the solo arm for not being able to ask questions.
   The consequence: the loop's own requirements-elicitation is a real advantage the solo brief neutralizes on
   purpose — so this comparison measures *execution method*, not *requirements gathering*.

2. **The loop got mid-run human QA; the solo arm got none.** During the loop run, a human caught a
   port-collision and a pie-chart rendering bug and sent them back for repair. The solo arm was judged exactly
   as first delivered, with zero follow-up. This favors the loop.

3. **n = 1.** One build each. Treat the scores as a case study, not a benchmark.

## Skill isolation (the load-bearing control)

The solo arm must not secretly benefit from the very skill it's being compared against. Before the counted
solo build, `codex exec` was probed under an isolated `CODEX_HOME`:

- With the default home, codex **could** see the `codex-agent-loop-orchestrator` skill (it reported the skill,
  its lanes, `requests.md`, the completion gate, etc.).
- Under the isolated home used for the solo build, codex reported **"codex-agent-loop-orchestrator: NO"** and
  **"lanes / docs/loop / requests.md / completion gate / loop dashboard: NO"**.

So the solo arm ran with the skill genuinely absent. Codex's own built-in capabilities (its bundled
"superpowers" playbooks) were **also** forbidden by the brief — the solo prompt explicitly bans invoking any
skill, playbook, subagent, or git worktree, so the solo arm is a single plain coding session. That keeps the
only difference between the arms the thing under test: the orchestration loop itself.

## Bottom line

Same requirements, same fixtures, same model, same reviewer and rubric. The solo prompt and the loop's
`goal.md` are reproduced in these repos so you can confirm the inputs match. The asymmetries that remain
(intake folding, mid-run QA, n=1) are named above and each is called out again in the comparison's verdict.
