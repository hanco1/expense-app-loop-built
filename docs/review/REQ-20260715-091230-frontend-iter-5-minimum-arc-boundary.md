# Iteration 5 Minimum-Visible-Arc Boundary

Request: `REQ-20260715-091230-frontend`  
Baseline implementation: `4b88b11`  
Frozen command: `python -m unittest tests.acceptance.test_local_web_app_minimum_arc_review -v`  
Frozen test SHA-256: `9FABFD79773E1419363E73508D2FB2125B5E6D1F087661C18AE559762984C88D`

## Two Frozen Scenario Families

| Case | Exact spending allocation | Required visual allocation |
| --- | --- | --- |
| `MA-01-one-unit-near-full` | `Housing=1`, `Groceries=999999999` data units | `Housing=1°`, `Groceries=359°` |
| `MA-02-canonical-count-simultaneous-floors` | All 12 canonical categories are non-zero; 11 receive one data unit and `Uncategorized=999999989` | eleven 1° arcs and `Uncategorized=349°` |

Both cases also carry two included positive credit rows. Credits remain visible
in the transaction/credit totals but never add a pie slice or spending amount.
In `MA-01`, the ten canonical zero-spending categories are absent from the
chart, legend, and category table.

## Observable Contract

- Numerical truth is checked before geometry: exact minor units, independent
  exact percentage text, category/transaction reconciliation, unchanged
  `data-units`, and an exact `PIE_SCALE=1000000000` sum.
- Chromium measures each rendered segment with `getTotalLength()` relative to
  the rendered track, not from a source angle or path attribute. Each non-zero
  category must be at least 1° and match the water-filled expected angle within
  0.05°.
- A 3,600-point centerline hit test (0.1° resolution) requires full coverage,
  at most boundary-tolerant multi-hits, one cyclic visible run per category,
  expected run order, and visible counts within two samples of the expected
  visual angle. Adjacent rendered endpoints must remain continuous.

## Frozen Baseline Against `4b88b11`

The command exits 1 with one test and two failing subtests.

- `MA-01`: 3,600 empty samples; path-degree sum 0°; no visible category run;
  both paths measure 0° instead of 1°/359° and receive 0/10 and 0/3590 hits.
- `MA-02`: 2,117 empty samples; path-degree sum 360.633197°; visible runs are
  only gap plus `Uncategorized`; all eleven sub-floor categories have zero
  visible hits, while `Uncategorized` measures 360.633191° instead of 349° and
  receives 1,483 rather than 3,490 hits.
- Green guardrails in both cases: exact displayed/accounting amounts and
  percentages, category and transaction reconciliation, unchanged exact data
  units and 1e9 sum, zero-category absence, and credit exclusion.

The module and this boundary document are frozen before implementation. Review
does not dispatch frontend work or change prior frozen artifacts, implementation,
root lifecycle state, dependencies, privacy behavior, or runtime ports.
