# Iteration 4 Frozen Pie-Geometry Boundary

Request: `REQ-20260715-091230-frontend`  
Baseline implementation: `38479e5`  
Frozen command: `python -m unittest tests.acceptance.test_local_web_app_pie_geometry_review -v`

## Boundary

This acceptance owns only the observable June donut contract. It does not
prescribe circles, paths, dash arrays, a visual coordinate scale, or a frontend
repair. It imports the approved synthetic June CSV through the real loopback
server in existing Chromium and samples the browser's actually painted,
topmost `.pie-segment` strokes with `document.elementsFromPoint` around an
automatically located ring radius. Source SVG attributes alone cannot satisfy
the geometry cases.

The probe uses 720 angular samples. A two-rendered-pixel allowance covers
boundary antialiasing when comparing proportional arc lengths. At most two
multi-hit boundary samples per category are tolerated; no empty sample is
allowed. Runs are cyclic, so the first and last sample are merged when they
belong to the same category.

## Stable Cases

| Case ID | Observable assertion | Baseline expectation at `38479e5` |
| --- | --- | --- |
| `PG-01-exact-accounting-guardrail` | June is `277617` spending, `72999` credits, and 22 transactions; nine exact category amounts reconcile to included spending; credits stay outside spending; `PIE_SCALE`, every `data-units`, and their 1e9 sum remain exact. | green |
| `PG-02-visible-coverage-no-gap-or-overlap` | Every sampled point on the painted ring has one visible category, allowing only boundary antialiasing; no gap or overlap replacement is accepted. | red: repeated dash patterns overlap across most of the ring |
| `PG-03-one-cyclic-run-per-category` | The topmost painted ring has exactly nine cyclic runs and each category occurs in exactly one run. | red: repeated stripes create many runs |
| `PG-04-every-category-visible-and-proportional` | All nine categories are topmost-visible and each visible run matches its exact 1e9-unit share within two rendered pixels. | red: categories are replaced/fragmented by overlapping repeats |
| `PG-05-housing-dominates-visible-ring` | Housing (`185000/277617`, exact units `666385709`) is one visible run covering more than half the circumference and matching its exact share within tolerance. | red: Housing is fragmented and not dominant |
| `PG-06-operable-legend-match[category]` | Each of the nine non-zero categories has one focusable segment and one matched legend control; exact amount/percentage labels agree and Enter selection synchronizes both controls without changing accounting. | green for all nine category paths |

The frozen inventory is six case families. Expected current inventory is two
green guardrail families (`PG-01`, all `PG-06` category checks) and four red
visual-geometry families (`PG-02` through `PG-05`). No product code, fixture,
dependency, browser runtime, or prior frozen acceptance is in scope.

## Required Future Result

Frontend may change only bounded visual geometry. The same frozen command must
later pass every case without changing this file or its acceptance test. The
exact accounting data, accessible interaction, local/privacy boundary, and
approved fixture hashes remain standing guardrails. Product alone may convert
this frozen contract into the iteration-4 `FIX_REQUEST`; review does not
dispatch implementation.
