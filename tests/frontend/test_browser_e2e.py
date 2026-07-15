from __future__ import annotations

import hashlib
import unittest

from tests.frontend.browser_support import (
    BrowserAppTestCase,
    CSV_FIXTURE,
    PDF_FIXTURE,
)


class LocalExpenseBrowserEndToEndTests(BrowserAppTestCase):
    def test_full_fixture_review_decision_reimport_and_undo_flow(self) -> None:
        self.assertEqual(
            hashlib.sha256(CSV_FIXTURE.read_bytes()).hexdigest().upper(),
            "9F93F107DDD02AEE2FB0A0AE19EB962180C680D1FB06D4D90959C96ED8CD7BAA",
        )
        self.assertEqual(
            hashlib.sha256(PDF_FIXTURE.read_bytes()).hexdigest().upper(),
            "F4B6B524D7C6140EE3F3E24CE87C4A36F0B40619395B5DC17B03F1B99DBC11F8",
        )

        self.go_to("imports")
        self.import_files(CSV_FIXTURE, PDF_FIXTURE)
        queue_rows = self.page.locator("#import-queue .import-item")
        self.assertEqual(queue_rows.count(), 2)
        self.assertEqual(queue_rows.nth(0).locator("strong").inner_text(), CSV_FIXTURE.name)
        self.assertEqual(queue_rows.nth(1).locator("strong").inner_text(), PDF_FIXTURE.name)
        self.assertIn("22 parsed · 1 failed · 22 occurrences", queue_rows.nth(0).inner_text())
        self.assertIn("12 parsed · 0 failed · 12 occurrences", queue_rows.nth(1).inner_text())

        csv_row = self.page.locator(f'tr[data-source-name="{CSV_FIXTURE.name}"]').first
        pdf_row = self.page.locator(f'tr[data-source-name="{PDF_FIXTURE.name}"]').first
        self.assertIn("23 retained rows", csv_row.inner_text())
        self.assertIn("22", csv_row.inner_text())
        self.assertIn("1", csv_row.inner_text())
        self.assertIn("12 retained rows", pdf_row.inner_text())
        csv_row.locator("button", has_text="Inspect").click()
        failed = self.page.locator('#run-detail tr[data-error-code="missing_amount"]')
        failed.wait_for()
        self.assertIn("csv-row:21", failed.inner_text())
        self.assertIn("No normalized transaction", failed.inner_text())
        self.assertNotIn("BROKEN ROW NO AMOUNT", self.page.locator("#run-detail").inner_text())

        self.go_to("overview")
        self.assertEqual(self.page.locator("#month-select").input_value(), "2026-06")
        self.assert_month("$2,776.17", "$729.99", "22", "277617", "72999")
        reconciliation = self.page.evaluate(
            """() => {
              const spending = BigInt(document.querySelector("#spending-total").dataset.minor);
              const categories = [...document.querySelectorAll("#category-table-body tr")]
                .reduce((sum, row) => sum + BigInt(row.dataset.minor), 0n);
              const transactionSpending = [...document.querySelectorAll("#transaction-table-body tr[data-spending='true']")]
                .reduce((sum, row) => sum - BigInt(row.dataset.minor), 0n);
              const segments = [...document.querySelectorAll(".pie-segment")];
              const trackLength = document.querySelector(".pie-track").getTotalLength();
              const pieUnits = segments
                .reduce((sum, segment) => sum + BigInt(segment.dataset.units), 0n);
              const visualUnits = segments
                .reduce((sum, segment) => sum + BigInt(segment.dataset.visualUnits), 0n);
              return {
                spending: spending.toString(),
                categories: categories.toString(),
                transactionSpending: transactionSpending.toString(),
                pieUnits: pieUnits.toString(),
                scale: window.ExpenseAppTesting.PIE_SCALE,
                visualUnits: visualUnits.toString(),
                visualScale: window.ExpenseAppTesting.PIE_VISUAL_SCALE,
                minimumVisualDegrees: Math.min(
                  ...segments.map(segment => segment.getTotalLength() * 360 / trackLength),
                ),
                chartLabels: document.querySelectorAll("#chart-legend .legend-button").length,
                categoryRows: document.querySelectorAll("#category-table-body tr").length,
                boundedArcs: segments.every((segment) => {
                  const geometry = segment.getAttribute("d") || "";
                  const geometryValues = (geometry.match(/-?[0-9]+(?:\\.[0-9]+)?/g) || [])
                    .map(Number);
                  return segment.tagName === "path"
                    && !segment.hasAttribute("pathLength")
                    && !segment.hasAttribute("stroke-dasharray")
                    && !segment.hasAttribute("stroke-dashoffset")
                    && !geometry.includes(window.ExpenseAppTesting.PIE_SCALE)
                    && geometryValues.length > 0
                    && geometryValues.every(value => Number.isFinite(value) && Math.abs(value) <= 200);
                }),
              };
            }"""
        )
        self.assertEqual(reconciliation["categories"], reconciliation["spending"])
        self.assertEqual(reconciliation["transactionSpending"], reconciliation["spending"])
        self.assertEqual(reconciliation["pieUnits"], reconciliation["scale"])
        self.assertEqual(reconciliation["visualUnits"], reconciliation["visualScale"])
        self.assertGreaterEqual(reconciliation["minimumVisualDegrees"], 0.99)
        self.assertEqual(reconciliation["chartLabels"], reconciliation["categoryRows"])
        self.assertTrue(reconciliation["boundedArcs"])
        self.assertEqual(self.page.locator("#reconciliation-status").inner_text(), "Reconciled exactly")

        self.page.locator("#month-select").select_option("2026-05")
        self.assert_month("$503.40", "$600.00", "12", "50340", "60000")
        self.page.locator("#month-select").select_option("2026-06")

        loblaws = self.page.locator("#transaction-table-body tr", has_text="LOBLAWS").first
        loblaws.locator("select").select_option("Dining")
        loblaws.locator('button[data-action="category-correction"]').click()
        corrected = self.page.locator("#transaction-table-body tr", has_text="LOBLAWS").first
        corrected.locator("text=Human correction").wait_for()
        self.assertEqual(corrected.locator("select").input_value(), "Dining")
        self.assertIn("1 history entry", corrected.inner_text())

        self.go_to("duplicates")
        candidate = self.page.locator(".duplicate-card").first
        self.assertEqual(candidate.get_attribute("data-effective-decision"), "pending")
        self.assertEqual(candidate.locator(".duplicate-side", has_text="TIM HORTONS").count(), 2)
        self.assertEqual(candidate.locator('.duplicate-side[data-included="true"]').count(), 2)

        candidate.locator('button[data-action="duplicate-distinct"]').click()
        candidate = self.page.locator(".duplicate-card").first
        candidate.filter(has=self.page.locator('[data-state="distinct"]')).wait_for()
        self.assertEqual(candidate.get_attribute("data-effective-decision"), "distinct")
        self.assertIn("Decision history (1)", candidate.inner_text())

        candidate.locator('input[type="radio"]').first.check()
        candidate.locator('button[data-action="duplicate-same"]').click()
        candidate = self.page.locator(".duplicate-card").first
        candidate.filter(has=self.page.locator('[data-state="same_transaction"]')).wait_for()
        self.assertEqual(candidate.get_attribute("data-effective-decision"), "same_transaction")
        self.assertEqual(candidate.locator('.duplicate-side[data-included="false"]').count(), 1)
        self.assertIn("Decision history (2)", candidate.inner_text())

        self.go_to("overview")
        self.assert_month("$2,771.67", "$729.99", "21", "277167", "72999")
        self.page.reload(wait_until="networkidle")
        self.page.locator("#status-region").filter(has_text="Local session ready").wait_for()
        self.assertEqual(self.page.locator("#month-select").input_value(), "2026-06")
        self.assert_month("$2,771.67", "$729.99", "21", "277167", "72999")
        corrected = self.page.locator("#transaction-table-body tr", has_text="LOBLAWS").first
        self.assertEqual(corrected.locator("select").input_value(), "Dining")
        self.assertIn("1 history entry", corrected.inner_text())
        self.go_to("duplicates")
        candidate = self.page.locator(".duplicate-card").first
        self.assertEqual(candidate.get_attribute("data-effective-decision"), "same_transaction")
        self.assertIn("Decision history (2)", candidate.inner_text())

        self.go_to("imports")
        self.import_files(CSV_FIXTURE)
        csv_rows = self.page.locator(f'tr[data-source-name="{CSV_FIXTURE.name}"]')
        self.assertEqual(csv_rows.count(), 2)
        self.assertEqual(csv_rows.locator("text=Exact re-import").count(), 1)
        self.go_to("overview")
        self.assert_month("$2,771.67", "$729.99", "21", "277167", "72999")

        self.go_to("imports")
        self.page.on("dialog", lambda dialog: dialog.accept())
        undone_ids: list[str] = []
        for _ in range(2):
            active = self.page.locator(
                f'tr[data-source-name="{CSV_FIXTURE.name}"][data-state="active"]'
            ).first
            run_id = active.get_attribute("data-run-id")
            self.assertIsNotNone(run_id)
            undone_ids.append(run_id)
            active.locator('button[data-action="undo-run"]').click()
            self.page.locator(f'tr[data-run-id="{run_id}"][data-state="undone"]').wait_for(timeout=30_000)

        self.go_to("overview")
        self.assertEqual(self.page.locator("#month-select").input_value(), "2026-05")
        self.assert_month("$503.40", "$600.00", "12", "50340", "60000")

        self.go_to("imports")
        self.import_files(CSV_FIXTURE)
        self.assertEqual(
            self.page.locator(f'tr[data-source-name="{CSV_FIXTURE.name}"][data-state="undone"]').count(),
            2,
        )
        self.go_to("overview")
        self.assertEqual(self.page.locator("#month-select").input_value(), "2026-06")
        self.assert_month("$2,771.67", "$729.99", "21", "277167", "72999")
        restored = self.page.locator("#transaction-table-body tr", has_text="LOBLAWS").first
        self.assertEqual(restored.locator("select").input_value(), "Dining")
        self.assertIn("1 history entry", restored.inner_text())
        self.go_to("duplicates")
        restored_candidate = self.page.locator(".duplicate-card").first
        self.assertEqual(restored_candidate.get_attribute("data-effective-decision"), "same_transaction")
        self.assertIn("Decision history (2)", restored_candidate.inner_text())

    def assert_month(
        self,
        spending_display: str,
        credits_display: str,
        count: str,
        spending_minor: str,
        credits_minor: str,
    ) -> None:
        spending = self.page.locator("#spending-total")
        credits = self.page.locator("#credit-total")
        self.assertEqual(spending.inner_text(), spending_display)
        self.assertEqual(spending.get_attribute("data-minor"), spending_minor)
        self.assertEqual(credits.inner_text(), credits_display)
        self.assertEqual(credits.get_attribute("data-minor"), credits_minor)
        self.assertEqual(self.page.locator("#transaction-count").inner_text(), count)


if __name__ == "__main__":
    unittest.main()
