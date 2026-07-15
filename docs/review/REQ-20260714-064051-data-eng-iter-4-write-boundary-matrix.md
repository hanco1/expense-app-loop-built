# Frozen public duplicate-decision write-boundary matrix - iteration 4

Status: **FROZEN before implementation** against baseline commit `53e57f6`.

This matrix closes the complete currently reachable public writer class. It is
separate from, and does not modify, the frozen iteration-3 component-state
matrix or its acceptance file.

## Public writer inventory

Repository export, import, contract, and symbol searches find two underlying
decision-writing callables exposed through six supported import paths. All six
are executable cells even when two paths resolve to the same class object; this
prevents an incidental module alias from remaining an untested bypass.

| Writer ID | Supported import path | Callable class | Baseline guard state |
| --- | --- | --- | --- |
| `SP` | `backend.AnalysisService.set_duplicate_decision` | service | guarded |
| `SM` | `backend.analysis.AnalysisService.set_duplicate_decision` | service | guarded; same callable as `SP` |
| `CP` | `backend.CoreStore.add_duplicate_decision` | persistence | unguarded |
| `CM` | `backend.persistence.CoreStore.add_duplicate_decision` | persistence | unguarded; same callable as `CP` |
| `CA` | `backend.analysis.CoreStore.add_duplicate_decision` | imported persistence alias | unguarded; same callable as `CP` |
| `CT` | `backend.statement_import.CoreStore.add_duplicate_decision` | imported persistence alias | unguarded; same callable as `CP` |

`contracts.analysis` contains immutable result dataclasses only and declares no
writer protocol or function. `StatementImportService` declares no duplicate
decision method. There is no supported HTTP, CLI, UI, plugin, or telemetry
writer in this backend-only slice.

## Proposal classes

| Proposal ID | Pre-state and final operation | Required result |
| --- | --- | --- |
| `ZK` | Valid chain `AB:A, BC:B`; propose triangle close `AC:C` | Reject zero structural keepers before append |
| `MC` | Valid `AB:A`; propose `BC:C` | Reject two structural keepers in one chain |
| `MM` | Valid components `AB:A` and `CD:C`; propose merge `BD:B` | Reject two structural keepers after merge |
| `AD` | Valid triangle `AB:A, AC:A, BC:B`; propose `AB:distinct` | Reject endpoints still same-connected by alternate path |
| `VS` | Pending pair `AB`; propose `AB:A` | Accept exactly one same history row and keeper A |
| `BD` | Valid chain `AB:A, BC:B`; propose bridge `BC:distinct` | Accept exactly one row and split into two valid components |
| `KR` | Valid chain `AB:A, BC:B`; redecide `AB:B` | Accept exactly one row and change structural keeper to B |
| `LR` | Pair history `AB:A`, then `AB:distinct`; propose latest `AB:A` | Accept exactly one row and restore latest same state |

The first four are invalid proposal families and the final four are valid
guardrails. Proposal validity is graph-structural and must not depend on current
support.

## Support states

| Support ID | Target-component state | Compatibility rule |
| --- | --- | --- |
| `A` | All target identities active | Compatible with every proposal |
| `P` | The first target identity has final support removed; all remaining target identities stay active | Compatible with every proposal and exercises deterministic fallback |
| `I` | Every target identity has final support removed | Compatible with every proposal; an active disconnected anchor keeps monthly analysis readable |

Each case contains one active normalized-disconnected anchor. Consequently,
even an inactive target component must leave `get_month_summary("2026-06")`
available before and after a rejected proposal.

## Assertion bundle applied to every executable case

Every case performs these checks where applicable:

1. Pre-proposal support loss changes no decision ID or entity count and leaves
   the valid graph readable.
2. A rejected proposal raises before append; entity counts, all decision IDs,
   effective candidate state, monthly summary, normalized facts, active
   supports, and structured occurrence provenance remain byte-for-byte equal.
3. An accepted proposal appends exactly one history row to only the target
   link, preserves every prior decision ID, and changes no retained fact or
   support.
4. Every same component has exactly one structural keeper. Each active
   component includes the active keeper or lexicographically smallest active
   stable identity fallback; an inactive component includes zero. Spending,
   Dining contributors, inclusion reasons, candidate flags, and source support
   provenance reconcile exactly.
5. After either rejection or acceptance, a renamed exact re-import of the first
   target identity reuses its stable identity, appends only run/source/occurrence
   support facts, rewrites no human history, and reprojects deterministically.
6. No test invokes network, subprocess, telemetry, OCR, UI, or a system
   dependency, and all data is wholly synthetic.

## Executable case IDs

Ordering is writer, then proposal, then support. The manifest guard parses this
section and fails if any documented ID and generated test ID diverge.

<!-- EXECUTABLE_CASE_IDS_START -->

| Writer | Stable executable IDs |
| --- | --- |
| SP | `SP-ZK-A`, `SP-ZK-P`, `SP-ZK-I`, `SP-MC-A`, `SP-MC-P`, `SP-MC-I`, `SP-MM-A`, `SP-MM-P`, `SP-MM-I`, `SP-AD-A`, `SP-AD-P`, `SP-AD-I`, `SP-VS-A`, `SP-VS-P`, `SP-VS-I`, `SP-BD-A`, `SP-BD-P`, `SP-BD-I`, `SP-KR-A`, `SP-KR-P`, `SP-KR-I`, `SP-LR-A`, `SP-LR-P`, `SP-LR-I` |
| SM | `SM-ZK-A`, `SM-ZK-P`, `SM-ZK-I`, `SM-MC-A`, `SM-MC-P`, `SM-MC-I`, `SM-MM-A`, `SM-MM-P`, `SM-MM-I`, `SM-AD-A`, `SM-AD-P`, `SM-AD-I`, `SM-VS-A`, `SM-VS-P`, `SM-VS-I`, `SM-BD-A`, `SM-BD-P`, `SM-BD-I`, `SM-KR-A`, `SM-KR-P`, `SM-KR-I`, `SM-LR-A`, `SM-LR-P`, `SM-LR-I` |
| CP | `CP-ZK-A`, `CP-ZK-P`, `CP-ZK-I`, `CP-MC-A`, `CP-MC-P`, `CP-MC-I`, `CP-MM-A`, `CP-MM-P`, `CP-MM-I`, `CP-AD-A`, `CP-AD-P`, `CP-AD-I`, `CP-VS-A`, `CP-VS-P`, `CP-VS-I`, `CP-BD-A`, `CP-BD-P`, `CP-BD-I`, `CP-KR-A`, `CP-KR-P`, `CP-KR-I`, `CP-LR-A`, `CP-LR-P`, `CP-LR-I` |
| CM | `CM-ZK-A`, `CM-ZK-P`, `CM-ZK-I`, `CM-MC-A`, `CM-MC-P`, `CM-MC-I`, `CM-MM-A`, `CM-MM-P`, `CM-MM-I`, `CM-AD-A`, `CM-AD-P`, `CM-AD-I`, `CM-VS-A`, `CM-VS-P`, `CM-VS-I`, `CM-BD-A`, `CM-BD-P`, `CM-BD-I`, `CM-KR-A`, `CM-KR-P`, `CM-KR-I`, `CM-LR-A`, `CM-LR-P`, `CM-LR-I` |
| CA | `CA-ZK-A`, `CA-ZK-P`, `CA-ZK-I`, `CA-MC-A`, `CA-MC-P`, `CA-MC-I`, `CA-MM-A`, `CA-MM-P`, `CA-MM-I`, `CA-AD-A`, `CA-AD-P`, `CA-AD-I`, `CA-VS-A`, `CA-VS-P`, `CA-VS-I`, `CA-BD-A`, `CA-BD-P`, `CA-BD-I`, `CA-KR-A`, `CA-KR-P`, `CA-KR-I`, `CA-LR-A`, `CA-LR-P`, `CA-LR-I` |
| CT | `CT-ZK-A`, `CT-ZK-P`, `CT-ZK-I`, `CT-MC-A`, `CT-MC-P`, `CT-MC-I`, `CT-MM-A`, `CT-MM-P`, `CT-MM-I`, `CT-AD-A`, `CT-AD-P`, `CT-AD-I`, `CT-VS-A`, `CT-VS-P`, `CT-VS-I`, `CT-BD-A`, `CT-BD-P`, `CT-BD-I`, `CT-KR-A`, `CT-KR-P`, `CT-KR-I`, `CT-LR-A`, `CT-LR-P`, `CT-LR-I` |

<!-- EXECUTABLE_CASE_IDS_END -->

## Explicitly unreachable or non-distinct writer classes

These are frozen exclusions rather than silent omissions.

<!-- UNREACHABLE_CASE_IDS_START -->

| ID | Candidate path | Reason |
| --- | --- | --- |
| `U01` | `AnalysisService.store.add_duplicate_decision` | Public attribute access resolves to the same `CoreStore` callable already executed through `CP`, `CM`, `CA`, and `CT`; it is not a seventh writer implementation |
| `U02` | The service's internal `self.store.add_duplicate_decision` call | This is the post-validation internal leg of `SP`/`SM`, not an independently callable decision API |
| `U03` | `CoreStore._connection()` plus raw SQL | Underscore-private persistence machinery is unsupported and not a public writer |
| `U04` | Direct `sqlite3` access to the database path | Bypasses the backend API entirely and is not an exported application contract |
| `U05` | `contracts.analysis` | Contains immutable values/results only; no decision-writing callable or protocol exists |
| `U06` | `StatementImportService`, HTTP, CLI, UI, plugin, or telemetry route | No duplicate-decision writer exists on these surfaces in this slice |

<!-- UNREACHABLE_CASE_IDS_END -->

## Frozen counts and baseline inventory

- Total inventory entries: **150**.
- Executable paths: **144**.
- Explicitly unreachable classes: **6**.
- Consolidated unittest count: **145** (144 cases plus one manifest guard).
- Expected baseline-red inventory at `53e57f6`: **48** cases — every
  `CP|CM|CA|CT` x `ZK|MC|MM|AD` x `A|P|I` combination.
- Expected baseline-green compatible guardrails: **96** cases — every `SP|SM`
  case plus every `CP|CM|CA|CT` x `VS|BD|KR|LR` x `A|P|I` combination. The
  manifest guard is also expected green.

The expected red classes are one underlying unvalidated persistence writer
reachable through four public import paths. The implementation contract is
class-wide: all supported public aliases must reject invalid proposals
atomically through one centralized rule while retaining all valid-write and
support/history guardrails. No case ID, expected result, or frozen artifact may
change after the freeze commit.
