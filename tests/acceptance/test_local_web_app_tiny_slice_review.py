from __future__ import annotations

import json
from urllib.parse import urlparse

from tests.frontend.browser_support import BrowserAppTestCase


PIE_SCALE = 1_000_000_000
VISIBLE_SAMPLE_COUNT = 720
TINY_MINOR = 1
LARGE_MINOR = 900_719_925_474_099_300
TOTAL_MINOR = TINY_MINOR + LARGE_MINOR


def transaction(identity: str, category: str, amount_minor: int) -> dict[str, object]:
    return {
        "identity_id": identity,
        "transaction_date": "2026-07-01",
        "merchant": category,
        "amount_minor": str(-amount_minor),
        "currency": "CAD",
        "effective_category": category,
        "category_source": "automatic",
        "correction_ids": [],
        "included": True,
        "inclusion_reason": "included",
        "is_spending": True,
        "active_supports": [],
    }


class LocalWebAppTinySliceReviewTests(BrowserAppTestCase):
    def test_supported_one_unit_slice_remains_visibly_represented(self) -> None:
        summary = {
            "month": "2026-07",
            "currency": "CAD",
            "spending_total_minor": str(TOTAL_MINOR),
            "credit_total_minor": "0",
            "transaction_count": 2,
            "credit_transaction_count": 0,
            "category_breakdown": [
                {
                    "category": "Tiny",
                    "spending_minor": str(TINY_MINOR),
                    "transaction_count": 1,
                },
                {
                    "category": "Large",
                    "spending_minor": str(LARGE_MINOR),
                    "transaction_count": 1,
                },
            ],
            "transactions": [
                transaction("identity-tiny", "Tiny", TINY_MINOR),
                transaction("identity-large", "Large", LARGE_MINOR),
            ],
        }

        def route_months(route) -> None:
            path = urlparse(route.request.url).path
            payload = ["2026-07"] if path == "/api/months" else summary
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"data": payload}),
            )

        self.page.route("**/api/months**", route_months)
        self.page.reload(wait_until="networkidle")
        self.page.locator("#reconciliation-status").filter(
            has_text="Reconciled exactly"
        ).wait_for()

        snapshot = self.page.evaluate(
            """({sampleCount}) => {
              const svg = document.querySelector(".pie-svg");
              const segments = [...document.querySelectorAll(".pie-segment")];
              const tiny = segments.find((segment) => segment.dataset.category === "Tiny");
              if (!svg || !tiny || segments.length !== 2) {
                throw new Error("the two-category rendered chart is required");
              }
              const rect = svg.getBoundingClientRect();
              const centerX = rect.left + rect.width / 2;
              const centerY = rect.top + rect.height / 2;
              const radius = rect.width * 70 / 200;
              const visible = [];
              for (let index = 0; index < sampleCount; index += 1) {
                const angle = 2 * Math.PI * index / sampleCount;
                const category = document.elementsFromPoint(
                  centerX + radius * Math.cos(angle),
                  centerY + radius * Math.sin(angle),
                ).find((element) => element.matches?.(".pie-segment"))?.dataset.category;
                visible.push(category || null);
              }
              tiny.focus();
              tiny.dispatchEvent(new KeyboardEvent("keydown", {key: "Enter", bubbles: true}));
              return {
                units: Object.fromEntries(
                  segments.map((segment) => [segment.dataset.category, segment.dataset.units]),
                ),
                lengths: Object.fromEntries(
                  segments.map((segment) => [segment.dataset.category, segment.getTotalLength()]),
                ),
                visibleCounts: Object.fromEntries(
                  ["Tiny", "Large"].map((category) => [
                    category,
                    visible.filter((value) => value === category).length,
                  ]),
                ),
                tinySelected: tiny.classList.contains("is-selected"),
                legendSelected: document.querySelector(
                  '#chart-legend .legend-button[data-category="Tiny"]',
                )?.classList.contains("is-selected") || false,
              };
            }""",
            {"sampleCount": VISIBLE_SAMPLE_COUNT},
        )

        self.assertEqual(snapshot["units"]["Tiny"], "1")
        self.assertEqual(
            int(snapshot["units"]["Tiny"]) + int(snapshot["units"]["Large"]),
            PIE_SCALE,
        )
        self.assertGreater(
            min(snapshot["lengths"].values()),
            0,
            f"non-zero exact slices collapsed in rendered SVG: {snapshot}",
        )
        self.assertGreater(snapshot["visibleCounts"]["Tiny"], 0, snapshot)
        self.assertGreater(
            snapshot["visibleCounts"]["Large"],
            VISIBLE_SAMPLE_COUNT // 2,
            snapshot,
        )
        self.assertTrue(snapshot["tinySelected"])
        self.assertTrue(snapshot["legendSelected"])


if __name__ == "__main__":
    import unittest

    unittest.main()
