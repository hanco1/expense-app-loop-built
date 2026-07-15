from __future__ import annotations

import json
import math
from dataclasses import dataclass
from fractions import Fraction
from urllib.parse import urlparse

from contracts.analysis import CANONICAL_CATEGORIES
from tests.frontend.browser_support import BrowserAppTestCase


PIE_SCALE = 1_000_000_000
SAMPLES_PER_DEGREE = 10
VISIBLE_SAMPLE_COUNT = 360 * SAMPLES_PER_DEGREE
MINIMUM_VISIBLE_DEGREES = Fraction(1, 1)
LARGE_MINOR = 900_719_925_474_099_300
CREDITS = (("credit-income", "Income", 500), ("credit-refund", "Refunds & Credits", 300))


@dataclass(frozen=True)
class ArcCase:
    case_id: str
    category_amounts: tuple[tuple[str, int], ...]
    zero_categories: tuple[str, ...]


CASES = (
    ArcCase(
        case_id="MA-01-one-unit-near-full",
        category_amounts=(("Housing", 1), ("Groceries", LARGE_MINOR)),
        zero_categories=tuple(
            category for category in CANONICAL_CATEGORIES if category not in {"Housing", "Groceries"}
        ),
    ),
    ArcCase(
        case_id="MA-02-canonical-count-simultaneous-floors",
        category_amounts=tuple(
            (category, 1 if index < len(CANONICAL_CATEGORIES) - 1 else LARGE_MINOR)
            for index, category in enumerate(CANONICAL_CATEGORIES)
        ),
        zero_categories=(),
    ),
)


def formatted_money(minor: int) -> str:
    return f"${minor // 100:,}.{minor % 100:02d}"


def formatted_percent(part: int, total: int) -> str:
    basis_points = (part * 10_000 + total // 2) // total
    return f"{basis_points // 100}.{basis_points % 100:02d}%"


def exact_units(category_amounts: tuple[tuple[str, int], ...]) -> dict[str, int]:
    total = sum(amount for _, amount in category_amounts)
    allocated = [max(amount * PIE_SCALE // total, 1) for _, amount in category_amounts]
    largest_index = max(range(len(allocated)), key=allocated.__getitem__)
    difference = PIE_SCALE - sum(allocated)
    allocated[largest_index] += difference
    if allocated[largest_index] < 1 or sum(allocated) != PIE_SCALE:
        raise AssertionError("exact pie units must remain positive and reconcile")
    return {
        category: units
        for (category, _), units in zip(category_amounts, allocated, strict=True)
    }


def expected_visual_degrees(
    category_amounts: tuple[tuple[str, int], ...],
) -> dict[str, Fraction]:
    total = sum(amount for _, amount in category_amounts)
    floored = {
        category
        for category, amount in category_amounts
        if Fraction(amount * 360, total) < MINIMUM_VISIBLE_DEGREES
    }
    remaining = Fraction(360 - len(floored), 1)
    non_floored_total = sum(
        amount for category, amount in category_amounts if category not in floored
    )
    return {
        category: (
            MINIMUM_VISIBLE_DEGREES
            if category in floored
            else remaining * amount / non_floored_total
        )
        for category, amount in category_amounts
    }


def transaction(
    identity: str,
    category: str,
    amount_minor: int,
    *,
    is_spending: bool,
) -> dict[str, object]:
    return {
        "identity_id": identity,
        "transaction_date": "2026-07-01",
        "merchant": identity,
        "amount_minor": str(-amount_minor if is_spending else amount_minor),
        "currency": "CAD",
        "effective_category": category,
        "category_source": "automatic",
        "correction_ids": [],
        "included": True,
        "inclusion_reason": "included",
        "is_spending": is_spending,
        "active_supports": [],
    }


def summary_for(case: ArcCase) -> dict[str, object]:
    spending_total = sum(amount for _, amount in case.category_amounts)
    credit_total = sum(amount for _, _, amount in CREDITS)
    spending_rows = [
        transaction(f"spending-{index}", category, amount, is_spending=True)
        for index, (category, amount) in enumerate(case.category_amounts)
    ]
    credit_rows = [
        transaction(identity, category, amount, is_spending=False)
        for identity, category, amount in CREDITS
    ]
    return {
        "month": "2026-07",
        "currency": "CAD",
        "spending_total_minor": str(spending_total),
        "credit_total_minor": str(credit_total),
        "transaction_count": len(spending_rows) + len(credit_rows),
        "spending_transaction_count": len(spending_rows),
        "credit_transaction_count": len(credit_rows),
        "category_breakdown": [
            {
                "category": category,
                "spending_minor": str(amount),
                "transaction_count": 1,
            }
            for category, amount in case.category_amounts
        ],
        "transactions": spending_rows + credit_rows,
    }


def cyclic_order_matches(actual: list[str], expected: list[str]) -> bool:
    if len(actual) != len(expected):
        return False
    return any(actual == expected[index:] + expected[:index] for index in range(len(expected)))


class LocalWebAppMinimumArcReviewTests(BrowserAppTestCase):
    def render_case(self, case: ArcCase) -> dict[str, object]:
        summary = summary_for(case)

        def route_months(route) -> None:
            path = urlparse(route.request.url).path
            payload = ["2026-07"] if path == "/api/months" else summary
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"data": payload}),
            )

        self.page.unroute("**/api/months**")
        self.page.route("**/api/months**", route_months)
        self.page.reload(wait_until="networkidle")
        self.page.locator("#reconciliation-status").filter(
            has_text="Reconciled exactly"
        ).wait_for()

        return self.page.evaluate(
            """({sampleCount}) => {
              const svg = document.querySelector(".pie-svg");
              const track = document.querySelector(".pie-track");
              const segments = [...document.querySelectorAll(".pie-segment")];
              const legends = [...document.querySelectorAll("#chart-legend .legend-button")];
              const categoryRows = [...document.querySelectorAll("#category-table-body tr")];
              const transactions = [...document.querySelectorAll("#transaction-table-body tr")];
              if (!svg || !track || segments.length === 0) {
                throw new Error("the rendered pie track and segments are required");
              }

              const trackLength = track.getTotalLength();
              const pathLengths = Object.fromEntries(
                segments.map((segment) => [segment.dataset.category, segment.getTotalLength()]),
              );
              const pathDegrees = Object.fromEntries(
                segments.map((segment) => [
                  segment.dataset.category,
                  trackLength > 0 ? segment.getTotalLength() * 360 / trackLength : 0,
                ]),
              );
              const rect = svg.getBoundingClientRect();
              const centerX = rect.left + rect.width / 2;
              const centerY = rect.top + rect.height / 2;
              const reference = track.getPointAtLength(0).matrixTransform(track.getScreenCTM());
              const radius = Math.hypot(reference.x - centerX, reference.y - centerY);
              const samples = [];
              for (let index = 0; index < sampleCount; index += 1) {
                const angle = 2 * Math.PI * index / sampleCount;
                samples.push(
                  document.elementsFromPoint(
                    centerX + radius * Math.cos(angle),
                    centerY + radius * Math.sin(angle),
                  ).filter((element) => element.matches?.(".pie-segment"))
                    .map((element) => element.dataset.category),
                );
              }
              const topmost = samples.map((categories) => categories[0] || null);
              const visibleCounts = {};
              for (const category of topmost) {
                if (category !== null) {
                  visibleCounts[category] = (visibleCounts[category] || 0) + 1;
                }
              }
              const runs = [];
              for (const category of topmost) {
                if (runs.length === 0 || runs[runs.length - 1] !== category) {
                  runs.push(category);
                }
              }
              if (runs.length > 1 && runs[0] === runs[runs.length - 1]) {
                runs.pop();
              }

              const endpointGaps = segments.map((segment, index) => {
                const next = segments[(index + 1) % segments.length];
                const end = segment.getPointAtLength(segment.getTotalLength())
                  .matrixTransform(segment.getScreenCTM());
                const start = next.getPointAtLength(0).matrixTransform(next.getScreenCTM());
                return Math.hypot(end.x - start.x, end.y - start.y);
              });
              const tableText = Object.fromEntries(
                categoryRows.map((row) => [row.dataset.category, row.innerText]),
              );
              const legendText = Object.fromEntries(
                legends.map((legend) => [legend.dataset.category, legend.innerText]),
              );
              return {
                exact: {
                  pieScale: window.ExpenseAppTesting.PIE_SCALE,
                  spending: document.querySelector("#spending-total").dataset.minor,
                  credits: document.querySelector("#credit-total").dataset.minor,
                  transactionCount: document.querySelector("#transaction-count").textContent,
                  reconciliation: document.querySelector("#reconciliation-status").textContent,
                  categoryMinor: Object.fromEntries(
                    categoryRows.map((row) => [row.dataset.category, row.dataset.minor]),
                  ),
                  segmentMinor: Object.fromEntries(
                    segments.map((segment) => [segment.dataset.category, segment.dataset.minor]),
                  ),
                  segmentUnits: Object.fromEntries(
                    segments.map((segment) => [segment.dataset.category, segment.dataset.units]),
                  ),
                  unitSum: segments.reduce(
                    (sum, segment) => sum + BigInt(segment.dataset.units), 0n,
                  ).toString(),
                  spendingFromTransactions: transactions
                    .filter((row) => row.dataset.spending === "true")
                    .reduce((sum, row) => sum - BigInt(row.dataset.minor), 0n)
                    .toString(),
                  creditsFromTransactions: transactions
                    .filter((row) => row.dataset.spending === "false" && BigInt(row.dataset.minor) > 0n)
                    .reduce((sum, row) => sum + BigInt(row.dataset.minor), 0n)
                    .toString(),
                  creditRows: transactions.filter((row) => row.dataset.spending === "false").length,
                  tableText,
                  legendText,
                  segmentAria: Object.fromEntries(
                    segments.map((segment) => [segment.dataset.category, segment.getAttribute("aria-label")]),
                  ),
                },
                visible: {
                  trackLength,
                  pathLengths,
                  pathDegrees,
                  pathDegreeSum: Object.values(pathDegrees).reduce((sum, value) => sum + value, 0),
                  emptySamples: samples.filter((categories) => categories.length === 0).length,
                  overlapSamples: samples.filter((categories) => categories.length > 1).length,
                  visibleCounts,
                  runs,
                  maxEndpointGap: Math.max(...endpointGaps),
                },
              };
            }""",
            {"sampleCount": VISIBLE_SAMPLE_COUNT},
        )

    def test_exact_numbers_remain_separate_from_minimum_visible_arcs(self) -> None:
        for case in CASES:
            with self.subTest(case_id=case.case_id):
                snapshot = self.render_case(case)
                exact = snapshot["exact"]
                visible = snapshot["visible"]
                amounts = dict(case.category_amounts)
                spending_total = sum(amounts.values())
                credit_total = sum(amount for _, _, amount in CREDITS)
                expected_units = exact_units(case.category_amounts)
                expected_degrees = expected_visual_degrees(case.category_amounts)
                expected_text = {category: str(amount) for category, amount in amounts.items()}

                self.assertEqual(exact["pieScale"], str(PIE_SCALE))
                self.assertEqual(exact["spending"], str(spending_total))
                self.assertEqual(exact["credits"], str(credit_total))
                self.assertEqual(
                    exact["transactionCount"], str(len(case.category_amounts) + len(CREDITS))
                )
                self.assertEqual(exact["reconciliation"], "Reconciled exactly")
                self.assertEqual(exact["categoryMinor"], expected_text)
                self.assertEqual(exact["segmentMinor"], expected_text)
                self.assertEqual(
                    exact["segmentUnits"],
                    {category: str(units) for category, units in expected_units.items()},
                )
                self.assertEqual(exact["unitSum"], str(PIE_SCALE))
                self.assertEqual(exact["spendingFromTransactions"], str(spending_total))
                self.assertEqual(exact["creditsFromTransactions"], str(credit_total))
                self.assertEqual(exact["creditRows"], len(CREDITS))
                for category in case.zero_categories:
                    self.assertNotIn(category, exact["segmentMinor"])
                    self.assertNotIn(category, exact["tableText"])
                    self.assertNotIn(category, exact["legendText"])
                for category, amount in case.category_amounts:
                    expected_money = formatted_money(amount)
                    expected_percentage = formatted_percent(amount, spending_total)
                    self.assertIn(expected_money, exact["tableText"][category])
                    self.assertIn(expected_percentage, exact["tableText"][category])
                    self.assertIn(expected_money, exact["legendText"][category])
                    self.assertIn(expected_percentage, exact["legendText"][category])
                    self.assertIn(expected_money, exact["segmentAria"][category])
                    self.assertIn(expected_percentage, exact["segmentAria"][category])

                problems: list[str] = []
                if visible["emptySamples"] != 0:
                    problems.append(f"empty_samples={visible['emptySamples']}")
                if visible["overlapSamples"] > len(amounts) * 2:
                    problems.append(f"overlap_samples={visible['overlapSamples']}")
                if visible["maxEndpointGap"] > 0.25:
                    problems.append(f"max_endpoint_gap={visible['maxEndpointGap']:.6f}px")
                if abs(visible["pathDegreeSum"] - 360) > 0.05:
                    problems.append(f"path_degree_sum={visible['pathDegreeSum']:.6f}")

                run_categories = [category for category in visible["runs"] if category is not None]
                if None in visible["runs"] or not cyclic_order_matches(
                    run_categories, list(amounts)
                ):
                    problems.append(f"cyclic_runs={visible['runs']}")

                for category, expected in expected_degrees.items():
                    expected_float = float(expected)
                    actual_degrees = visible["pathDegrees"].get(category, 0)
                    actual_samples = visible["visibleCounts"].get(category, 0)
                    expected_samples = round(expected_float * SAMPLES_PER_DEGREE)
                    if actual_degrees < 0.99:
                        problems.append(
                            f"{category}: below_floor={actual_degrees:.6f}deg"
                        )
                    if abs(actual_degrees - expected_float) > 0.05:
                        problems.append(
                            f"{category}: path={actual_degrees:.6f}deg expected={expected_float:.6f}deg"
                        )
                    if actual_samples == 0 or abs(actual_samples - expected_samples) > 2:
                        problems.append(
                            f"{category}: visible={actual_samples} expected={expected_samples} samples"
                        )

                self.assertEqual(problems, [], "; ".join(problems))


if __name__ == "__main__":
    import unittest

    unittest.main()
