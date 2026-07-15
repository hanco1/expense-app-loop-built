from __future__ import annotations

import math

from tests.frontend.browser_support import BrowserAppTestCase, CSV_FIXTURE


PIE_SCALE = 1_000_000_000
VISIBLE_SAMPLE_COUNT = 720
EXPECTED_CATEGORY_MINOR = {
    "Housing": 185_000,
    "Shopping": 30_521,
    "Groceries": 25_727,
    "Bills & Utilities": 16_774,
    "Transportation": 8_047,
    "Health & Fitness": 6_554,
    "Dining": 2_100,
    "Entertainment": 1_799,
    "Fees": 1_095,
}
EXPECTED_CATEGORY_UNITS = {
    "Housing": 666_385_709,
    "Shopping": 109_939_232,
    "Groceries": 92_670_837,
    "Bills & Utilities": 60_421_371,
    "Transportation": 28_985_977,
    "Health & Fitness": 23_608_064,
    "Dining": 7_564_378,
    "Entertainment": 6_480_150,
    "Fees": 3_944_282,
}


def formatted_money(minor: int) -> str:
    return f"${minor // 100:,}.{minor % 100:02d}"


def formatted_percent(part: int, total: int) -> str:
    basis_points = (part * 10_000 + total // 2) // total
    return f"{basis_points // 100}.{basis_points % 100:02d}%"


class LocalWebAppPieGeometryReviewTests(BrowserAppTestCase):
    def test_approved_june_donut_is_visibly_contiguous_exact_and_operable(self) -> None:
        self.go_to("imports")
        self.import_files(CSV_FIXTURE)
        self.go_to("overview")

        snapshot = self.page.evaluate(
            """({sampleCount}) => {
              const svg = document.querySelector(".pie-svg");
              const segments = [...document.querySelectorAll(".pie-segment")];
              const legends = [...document.querySelectorAll("#chart-legend .legend-button")];
              const categoryRows = [...document.querySelectorAll("#category-table-body tr")];
              const transactions = [...document.querySelectorAll("#transaction-table-body tr")];
              if (!svg || segments.length === 0) {
                throw new Error("the rendered pie SVG and its segments are required");
              }

              const rect = svg.getBoundingClientRect();
              const centerX = rect.left + rect.width / 2;
              const centerY = rect.top + rect.height / 2;
              const hitCategories = (radius, steps) => {
                const result = [];
                for (let index = 0; index < steps; index += 1) {
                  const angle = 2 * Math.PI * index / steps;
                  const hits = document.elementsFromPoint(
                    centerX + radius * Math.cos(angle),
                    centerY + radius * Math.sin(angle),
                  ).filter((element) => element.matches?.(".pie-segment"));
                  result.push(hits.map((element) => element.dataset.category));
                }
                return result;
              };

              // Derive the ring radius from rendered SVG geometry, not from a
              // circle/path source attribute or a visual-coordinate constant.
              const referencePoint = segments[0].getPointAtLength(0);
              const screenPoint = referencePoint.matrixTransform(segments[0].getScreenCTM());
              const radius = Math.hypot(screenPoint.x - centerX, screenPoint.y - centerY);
              const samples = hitCategories(radius, sampleCount);
              const topmost = samples.map((categories) => categories[0] || null);
              const visibleCounts = {};
              for (const category of topmost) {
                if (category !== null) {
                  visibleCounts[category] = (visibleCounts[category] || 0) + 1;
                }
              }
              const runs = [];
              for (const category of topmost) {
                if (runs.length === 0 || runs[runs.length - 1].category !== category) {
                  runs.push({category, samples: 1});
                } else {
                  runs[runs.length - 1].samples += 1;
                }
              }
              if (
                runs.length > 1
                && runs[0].category === runs[runs.length - 1].category
              ) {
                runs[0].samples += runs.pop().samples;
              }

              const categoryMinor = Object.fromEntries(
                categoryRows.map((row) => [row.dataset.category, row.dataset.minor]),
              );
              const segmentMinor = Object.fromEntries(
                segments.map((segment) => [segment.dataset.category, segment.dataset.minor]),
              );
              const segmentUnits = Object.fromEntries(
                segments.map((segment) => [segment.dataset.category, segment.dataset.units]),
              );
              const spendingFromTransactions = transactions
                .filter((row) => row.dataset.spending === "true")
                .reduce((sum, row) => sum - BigInt(row.dataset.minor), 0n);
              const creditsFromTransactions = transactions
                .filter((row) => row.dataset.spending === "false" && BigInt(row.dataset.minor) > 0n)
                .reduce((sum, row) => sum + BigInt(row.dataset.minor), 0n);

              return {
                exact: {
                  month: document.querySelector("#month-select").value,
                  spending: document.querySelector("#spending-total").dataset.minor,
                  credits: document.querySelector("#credit-total").dataset.minor,
                  transactionCount: document.querySelector("#transaction-count").textContent,
                  reconciliation: document.querySelector("#reconciliation-status").textContent,
                  pieScale: window.ExpenseAppTesting.PIE_SCALE,
                  categoryMinor,
                  segmentMinor,
                  segmentUnits,
                  segmentCount: segments.length,
                  legendCount: legends.length,
                  spendingFromTransactions: spendingFromTransactions.toString(),
                  creditsFromTransactions: creditsFromTransactions.toString(),
                  unitSum: segments
                    .reduce((sum, segment) => sum + BigInt(segment.dataset.units), 0n)
                    .toString(),
                },
                visible: {
                  radius,
                  circumferencePixels: 2 * Math.PI * radius,
                  emptySamples: samples.filter((categories) => categories.length === 0).length,
                  overlapSamples: samples.filter((categories) => categories.length > 1).length,
                  visibleCounts,
                  runs,
                },
              };
            }""",
            {"sampleCount": VISIBLE_SAMPLE_COUNT},
        )

        exact = snapshot["exact"]
        visible = snapshot["visible"]
        expected_minor_text = {
            category: str(minor) for category, minor in EXPECTED_CATEGORY_MINOR.items()
        }
        expected_units_text = {
            category: str(units) for category, units in EXPECTED_CATEGORY_UNITS.items()
        }

        with self.subTest(case_id="PG-01-exact-accounting-guardrail"):
            self.assertEqual(exact["month"], "2026-06")
            self.assertEqual(exact["spending"], "277617")
            self.assertEqual(exact["credits"], "72999")
            self.assertEqual(exact["transactionCount"], "22")
            self.assertEqual(exact["reconciliation"], "Reconciled exactly")
            self.assertEqual(exact["pieScale"], str(PIE_SCALE))
            self.assertEqual(exact["categoryMinor"], expected_minor_text)
            self.assertEqual(exact["segmentMinor"], expected_minor_text)
            self.assertEqual(exact["segmentUnits"], expected_units_text)
            self.assertEqual(exact["segmentCount"], 9)
            self.assertEqual(exact["legendCount"], 9)
            self.assertEqual(exact["spendingFromTransactions"], "277617")
            self.assertEqual(exact["creditsFromTransactions"], "72999")
            self.assertEqual(exact["unitSum"], str(PIE_SCALE))

        with self.subTest(case_id="PG-02-visible-coverage-no-gap-or-overlap"):
            self.assertEqual(visible["emptySamples"], 0)
            self.assertLessEqual(
                visible["overlapSamples"],
                len(EXPECTED_CATEGORY_MINOR) * 2,
                "only a boundary hit may see both adjacent painted segments",
            )

        with self.subTest(case_id="PG-03-one-cyclic-run-per-category"):
            self.assertEqual(len(visible["runs"]), 9, visible["runs"])
            self.assertEqual(
                {run["category"] for run in visible["runs"]},
                set(EXPECTED_CATEGORY_MINOR),
            )
            self.assertTrue(all(run["category"] is not None for run in visible["runs"]))

        sample_tolerance = max(
            2,
            math.ceil(
                2 * VISIBLE_SAMPLE_COUNT / float(visible["circumferencePixels"])
            ),
        )
        visible_counts = visible["visibleCounts"]
        with self.subTest(case_id="PG-04-every-category-visible-and-proportional"):
            self.assertEqual(set(visible_counts), set(EXPECTED_CATEGORY_MINOR))
            for category, units in EXPECTED_CATEGORY_UNITS.items():
                expected_samples = round(units * VISIBLE_SAMPLE_COUNT / PIE_SCALE)
                self.assertGreater(visible_counts[category], 0, category)
                self.assertLessEqual(
                    abs(visible_counts[category] - expected_samples),
                    sample_tolerance,
                    category,
                )

        with self.subTest(case_id="PG-05-housing-dominates-visible-ring"):
            housing_samples = visible_counts.get("Housing", 0)
            expected_housing_samples = round(
                EXPECTED_CATEGORY_UNITS["Housing"] * VISIBLE_SAMPLE_COUNT / PIE_SCALE
            )
            self.assertGreater(housing_samples, VISIBLE_SAMPLE_COUNT // 2)
            self.assertLessEqual(
                abs(housing_samples - expected_housing_samples),
                sample_tolerance,
            )

        for category, minor in EXPECTED_CATEGORY_MINOR.items():
            with self.subTest(case_id=f"PG-06-operable-legend-match[{category}]"):
                segment = self.page.locator(
                    f'.pie-segment[data-category="{category}"]'
                )
                legend = self.page.locator(
                    f'#chart-legend .legend-button[data-category="{category}"]'
                )
                self.assertEqual(segment.count(), 1)
                self.assertEqual(legend.count(), 1)
                self.assertEqual(segment.get_attribute("tabindex"), "0")
                self.assertEqual(segment.get_attribute("role"), "button")
                expected_money = formatted_money(minor)
                expected_percentage = formatted_percent(minor, 277_617)
                self.assertIn(expected_money, segment.get_attribute("aria-label") or "")
                self.assertIn(expected_percentage, segment.get_attribute("aria-label") or "")
                self.assertIn(expected_money, legend.inner_text())
                self.assertIn(expected_percentage, legend.inner_text())

                segment.focus()
                self.assertEqual(
                    self.page.evaluate("() => document.activeElement?.dataset.category"),
                    category,
                )
                segment.press("Enter")
                self.assertTrue(segment.evaluate("element => element.classList.contains('is-selected')"))
                self.assertTrue(legend.evaluate("element => element.classList.contains('is-selected')"))
                segment.press("Enter")
                self.assertFalse(segment.evaluate("element => element.classList.contains('is-selected')"))
                self.assertFalse(legend.evaluate("element => element.classList.contains('is-selected')"))


if __name__ == "__main__":
    import unittest

    unittest.main()
