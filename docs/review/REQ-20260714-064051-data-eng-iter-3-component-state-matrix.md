# Frozen same-transaction component-state matrix - iteration 3

Status: **FROZEN before implementation** against baseline commit `6b9378f`.

## Component contract

`COMP-1` is the single component-level invariant for this iteration:

- Effective `same_transaction` edges, and only those edges, form connected
  components. Pending and latest-`distinct` links do not connect components.
- Every committed same component has exactly one **structural keeper**: the
  single identity not excluded by any effective same edge. A proposed same or
  distinct redecision that would leave zero or multiple structural keepers is
  rejected before append. A distinct proposal is also rejected when its two
  endpoints remain same-connected through an alternate path.
- If the structural keeper is active, it is the sole included representative.
  Otherwise the sole representative is the active component identity with the
  lexicographically smallest stable `identity_id`. When structural-keeper
  support returns, that keeper resumes automatically.
- A component with active identities has exactly one included active
  representative. A component with no active identity has zero. This combines
  the lower bound required by C3/INV-1 with INV-5's no-double-counting upper
  bound.
- Projection is derived from current effective decisions and current active
  supports by one centralized rule. Fallback, undo, import, and re-import never
  append, rewrite, or delete human decision history. Accepted human decisions
  append exactly one row; rejected decisions append none.

## Assertion bundle applied to every executable path

Every `P*`, `C*`, `T*`, `M*`, and `X*` path in the consolidated acceptance
asserts all applicable parts of this bundle:

1. Exact active identity set and active run/source supports.
2. Exact included representative set and the `COMP-1` one-or-zero cardinality.
3. Deterministic fallback and restoration of the structural keeper.
4. Append-only decision history IDs and exact accepted/rejected history delta.
5. No decrease or mutation in retained identity, normalized fact, link, source,
   occurrence, or decision counts; each operation's expected additive delta is
   exact.
6. Exact month presence, transaction count, CAD spending total, Dining bucket,
   contributing identity IDs, inclusion reason, duplicate decision/link
   provenance, and structured source supports.
7. INV-1 through INV-6 consequences: no silent fact loss, no double counting,
   recoverable run state, human-history survival, exact reconciliation, and no
   cross-component effect.

All matrix transactions are repository-safe synthetic CAD 4.50 debits dated
2026-06-01. Different balance tokens create different source fingerprints while
leaving normalized facts equal; normalized-disconnected groups use different
merchant strings.

## Compatible executable paths

Abbreviations: `AB:A` means effective same edge A-B keeping A; `AB:D` means
latest distinct; `min(B,C)` means the active identity with lexicographically
smallest stable ID. Each row names the pre-state, one final state-changing
operation, and the required committed post-state.

| ID | Topology / compatible pre-state | Final operation | Required post-state |
| --- | --- | --- | --- |
| P01 | Pair; A active; B not imported; pending | Import new B/link | A,B active and included |
| P02 | Pending pair; A,B active | Undo A final support | Only B active/included |
| P03 | Pending pair; only B active | Undo B final support | None active; no month |
| P04 | Pending pair; all inactive | Exact re-import A | Only A active/included |
| P05 | Pending pair; A,B active | Append exact A support | A,B included; A has two supports |
| P06 | Pair; A,B active; pending | Append `AB:A` | Sole representative A |
| P07 | Pair `AB:A`; A,B active | Undo B final support | Only keeper A active/included |
| P08 | Pair `AB:A`; A,B active | Undo A final support | Sole fallback B |
| P09 | Pair `AB:A`; A inactive, B active | Restore exact A support | Human keeper A resumes |
| P10 | Pair `AB:A`; A has two supports | Undo one A support | A remains keeper with one support |
| P11 | Pair `AB:A`; A has one remaining of two supports | Undo final A support | Sole fallback B |
| P12 | Pair `AB:A`; A inactive, B active | Undo B final support | None active; no month |
| P13 | Pair `AB:A`; all inactive | Exact re-import B | Sole fallback B |
| P14 | Pair `AB:A`; all active | Append latest `AB:D` | Split pair; A,B included; history +1 |
| P15 | Pair latest `AB:D`; all active | Append latest `AB:A` | Sole representative A; history +1 |
| P16 | Pair `AB:A`; all active | Redecide `AB:B` | Sole representative B; history +1 |
| P17 | Pair `AB:A`; all active | Append exact B support | A remains sole representative |
| P18 | Pair `AB:A`; all active | Renamed exact re-import A | A remains keeper; support +1 |
| C01 | Chain pre-edge `AB:A`; A,B,C active | Append `BC:B` | Chain structural keeper A |
| C02 | Chain pre-edge `AB:B`; A,B,C active | Append `BC:B` | Chain structural keeper B |
| C03 | `AB:A`; A,B,C active | Propose `BC:C` | Reject multi-keeper chain; zero history delta |
| C04 | Chain `AB:A,BC:B`; only A,B active | Undo A final support | Sole fallback B |
| C05 | Chain `AB:A,BC:B`; all active | Undo A final support | Sole fallback `min(B,C)` |
| C06 | Chain keeper A with two supports | Undo one A support | A remains keeper |
| C07 | Chain keeper A with one remaining support | Undo final A support | Sole fallback `min(B,C)` |
| C08 | Chain; only C active | Undo C final support | None active; no month |
| C09 | Chain keeper A inactive; B,C active | Restore exact A support | Keeper A resumes |
| C10 | Chain keeper A; A,B,C active | Import matching D/new pending links | Representatives A and pending D |
| C11 | Chain keeper A plus pending D | Accept `AD:A` | D merges; sole representative A |
| C12 | Chain `AB:A,BC:B` | Append latest `BC:D` | Bridge split; representatives A,C |
| C13 | Split `AB:A`, latest `BC:D` | Reappend `BC:B` | Rejoined chain; sole A |
| C14 | Chain `AB:A,BC:B` | Redecide `AB:B` | Sole structural keeper B |
| C15 | Chain keeper A inactive; B,C active | Append exact B support | Same sole fallback `min(B,C)` |
| T01 | Triangle pre-edges `AB:A,AC:A` | Append `BC:B` | Triangle sole keeper A |
| T02 | Chain `AB:A,BC:B`; A-C closes triangle | Propose `AC:C` | Reject zero-keeper cycle; zero history delta |
| T03 | Triangle keeper A; all active | Undo A final support | Sole fallback `min(B,C)` |
| T04 | Triangle keeper A; all active | Propose latest `AB:D` | Reject non-bridge contradiction; zero history delta |
| T05 | Triangle keeper A; all active | Redecide `AB:B` | Sole structural keeper B |
| T06 | Triangle; only C active | Undo C final support | None active; no month |
| T07 | Triangle keeper A inactive; B,C active | Restore exact A support | Keeper A resumes |
| T08 | Triangle keeper A with one remaining support | Undo final A support | Sole fallback `min(B,C)` |
| M01 | Four identities; component `AB:A`, C,D separate | Append `CD:C` | Two components; representatives A,C |
| M02 | Components `AB:A` and `CD:C` | Append cross `AC:A` | Merged component; sole A |
| M03 | Components `AB:A` and `CD:C` | Propose cross `BD:B` | Reject two-keeper merge; zero history delta |
| M04 | Inactive `AB:A`; active `CD:C` | Append cross `AC:C` | Merged component; sole active C |
| M05 | Merged `AB:A,CD:C,AC:A` | Append latest `AC:D` | Bridge split; representatives A,C |
| M06 | Merged component keeper A | Redecide cross `AC:C` | Sole structural keeper C |
| M07 | `AB:A` with A inactive; active `CD:C` | Append cross `AC:C` | Merged component; sole C; A stays inactive |
| X01 | Two normalized-disconnected pending pairs; `AB:A` | Append `CD:C` | Representatives A,C; no cross links |
| X02 | Disconnected components `AB:A`, `CD:C` | Undo A final support | Fallback B plus unaffected C |
| X03 | Disconnected components `AB:A`, `CD:C` | Redecide `CD:D` | A unchanged; second representative D |
| X04 | Disconnected components `AB:A`, `CD:C` | Append exact B support | Representatives A,C unchanged |
| X05 | First component only B active; second all active | Undo B final support | First zero; second representative C |
| X06 | First component all inactive; second keeper C | Restore exact A support | Representatives A,C |
| X07 | Disconnected A singleton and `CD:C`; B not imported | Import matching B/link | Pending A,B plus unaffected C |

## Explicitly impossible or invalid cross-product classes

These classes account for requested axis combinations that cannot form a legal
pre-state or committed post-state. They are frozen exclusions, not omissions.

| ID | Impossible or invalid combination | Reason |
| --- | --- | --- |
| I01 | Pending/distinct edge as same-component topology | Only effective same edges connect components |
| I02 | Pair simultaneously chain/triangle | Topology cardinality is incompatible |
| I03 | Triangle split by one distinct edge | Every triangle edge has an alternate same path |
| I04 | Component merge through pending link | Pending does not assert same real transaction |
| I05 | Automatic link across unequal normalized facts | Link predicate requires equal date/merchant/amount/currency |
| I06 | Partial loss with one prior support | Partial requires at least two supports |
| I07 | Final support loss while that identity stays active | Final loss means active support count becomes zero |
| I08 | Keeper-active/inactive state for pending/latest-distinct | Those states designate no component keeper |
| I09 | Keeper change via distinct | Distinct must carry no kept identity |
| I10 | Rejected decision with appended history | Rejection occurs before persistence |
| I11 | Exact re-import creating a new identity | Exact fingerprint/locator reuses stable identity |
| I12 | Renamed exact re-import changing fingerprint | Filename is display metadata, not content |
| I13 | One operation both exact re-import and new-source identity | Source fingerprints are mutually exclusive |
| I14 | Undo creating support/link/decision | Undo only excludes run occurrences and changes run state |
| I15 | Support restore changing human history | Projection is derived; history is append-only |
| I16 | Operation on normalized-disconnected component merging another | No matching link exists across groups |
| I17 | All inactive with included representative | Included representative must be active |
| I18 | Active committed same component with zero or multiple reps | Violates combined C3 lower bound and INV-5 upper bound |
| I19 | Pair cycle-closing proposal | A cycle needs an alternate same path and at least three identities |
| I20 | Different-source identities sharing one occurrence support | Each occurrence references one stable identity |

## Frozen counts and baseline inventory

- Total frozen matrix entries: **75**.
- Compatible executable paths: **55**.
- Explicit impossible/invalid classes: **20**.
- Consolidated unittest count: **56** (55 executable paths plus one manifest
  completeness guard).
- Baseline `6b9378f` red path inventory: **13** — `P08`, `P11`, `P13`,
  `C03`, `C04`, `C05`, `C07`, `C15`, `T03`, `T04`, `T08`, `M03`, `X02`.
- Baseline green compatible guardrails: **42**; the manifest guard is also
  green.

Red operation families are complete and non-overlapping at the behavioral
level: keeper final-support loss/fallback, restoration of only a non-keeper,
support append while fallback is active, multi-keeper same/merge proposals, and
non-bridge distinct contradictions. The already-fixed zero-keeper triangle
cycle remains a green rejection guardrail.

The matrix, test cases, case IDs, fallback ordering, impossible classes, and
expected results must not change after the review freeze commit. Product may
translate this document verbatim into the single authoritative iteration-3
FIX_REQUEST; data-eng must make the unchanged acceptance green using one
centralized component projection/validation rule.
