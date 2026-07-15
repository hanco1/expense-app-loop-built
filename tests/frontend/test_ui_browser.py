from __future__ import annotations

import base64
import json
import unittest

from tests.frontend.browser_support import BrowserAppTestCase, CSV_FIXTURE


class BrowserUiTests(BrowserAppTestCase):
    def test_empty_keyboard_narrow_and_offline_states_are_accessible(self) -> None:
        self.assertTrue(self.page.locator("#overview-empty").is_visible())
        self.assertEqual(self.page.locator('input[type="text"]').count(), 0)
        self.assertEqual(
            self.page.locator("#statement-files").get_attribute("accept"),
            ".csv,.pdf,text/csv,application/pdf",
        )
        self.assertEqual(
            self.page.evaluate(
                "() => performance.getEntriesByName(`${location.origin}/api/session`).length"
            ),
            1,
        )
        self.assertNotIn("frontend-browser-test-token", self.page.content())

        import_button = self.page.locator('.nav-button[data-view="imports"]')
        import_button.focus()
        import_button.press("Enter")
        self.assertEqual(self.page.locator(":focus").get_attribute("id"), "imports-title")
        self.assertTrue(self.page.locator("#drop-zone").is_visible())

        exact = self.page.evaluate(
            """() => ({
              large: window.ExpenseAppTesting.formatMoney("900719925474099301", "CAD"),
              negative: window.ExpenseAppTesting.formatMoney("-450", "CAD"),
              tiny: window.ExpenseAppTesting.allocatePieUnits([
                {category: "Tiny", spending_minor: "1"},
                {category: "Large", spending_minor: "900719925474099300"}
              ], "900719925474099301").map(item => item.units.toString()),
              scale: window.ExpenseAppTesting.PIE_SCALE
            })"""
        )
        self.assertEqual(exact["large"], "$9,007,199,254,740,993.01")
        self.assertEqual(exact["negative"], "−$4.50")
        self.assertGreater(int(exact["tiny"][0]), 0)
        self.assertEqual(sum(int(value) for value in exact["tiny"]), int(exact["scale"]))

        self.page.set_viewport_size({"width": 390, "height": 844})
        dimensions = self.page.evaluate(
            "() => ({documentWidth: document.documentElement.scrollWidth, viewportWidth: window.innerWidth})"
        )
        self.assertLessEqual(dimensions["documentWidth"], dimensions["viewportWidth"])

        offline_page = self.browser.new_page(viewport=self.viewport)
        offline_page.route("**/api/session", lambda route: route.abort())
        offline_page.goto(self.base_url)
        offline_page.locator("#error-banner").filter(has_text="local server is unavailable").wait_for()
        self.assertTrue(offline_page.locator("#overview-empty").is_visible())
        offline_page.close()

    def test_drop_import_conflict_and_double_submit_prevention(self) -> None:
        self.go_to("imports")
        encoded = base64.b64encode(CSV_FIXTURE.read_bytes()).decode("ascii")
        self.page.evaluate(
            """({encoded, name}) => {
              const binary = atob(encoded);
              const bytes = new Uint8Array(binary.length);
              for (let index = 0; index < binary.length; index += 1) {
                bytes[index] = binary.charCodeAt(index);
              }
              const transfer = new DataTransfer();
              transfer.items.add(new File([bytes], name, {type: "text/csv"}));
              const dropZone = document.querySelector("#drop-zone");
              dropZone.dispatchEvent(new DragEvent("dragenter", {bubbles: true, cancelable: true, dataTransfer: transfer}));
              dropZone.dispatchEvent(new DragEvent("drop", {bubbles: true, cancelable: true, dataTransfer: transfer}));
            }""",
            {"encoded": encoded, "name": CSV_FIXTURE.name},
        )
        self.page.locator('#import-queue .import-item[data-state="success"]').wait_for(timeout=60_000)
        queue_text = self.page.locator("#import-queue").inner_text()
        self.assertIn("22 parsed · 1 failed · 22 occurrences", queue_text)
        self.assertTrue(self.page.locator('#run-detail tr[data-error-code="missing_amount"]').is_visible())

        self.go_to("duplicates")
        candidate = self.page.locator(".duplicate-card").first
        self.assertEqual(candidate.get_attribute("data-effective-decision"), "pending")
        candidate.locator('input[type="radio"]').first.check()
        requests: list[str] = []

        def reject(route) -> None:
            requests.append(route.request.url)
            route.fulfill(
                status=409,
                content_type="application/json",
                body=json.dumps(
                    {
                        "error": {
                            "code": "duplicate_graph_conflict",
                            "message": "duplicate decision conflicts with the component invariant",
                            "details": {"duplicate_link_id": candidate.get_attribute("data-duplicate-link-id")},
                        }
                    }
                ),
            )

        self.page.route("**/api/duplicates/*/decision", reject)
        same_button = candidate.locator('button[data-action="duplicate-same"]')
        same_button.evaluate("button => { button.click(); button.click(); }")
        candidate.locator(".candidate-error").filter(has_text="duplicate_graph_conflict").wait_for()
        self.assertEqual(len(requests), 1)
        self.assertEqual(candidate.get_attribute("data-effective-decision"), "pending")
        self.assertIn("Decision history (0)", candidate.inner_text())
        self.assertTrue(candidate.locator('.duplicate-side[data-included="true"]').count() == 2)

        self.go_to("imports")
        self.page.unroute("**/api/duplicates/*/decision", reject)
        stale_requests: list[str] = []

        def stale_undo(route) -> None:
            stale_requests.append(route.request.url)
            route.fulfill(
                status=409,
                content_type="application/json",
                body=json.dumps(
                    {
                        "error": {
                            "code": "run_state_conflict",
                            "message": "only an active import run can be undone",
                            "details": {"state": "undone"},
                        }
                    }
                ),
            )

        self.page.route("**/api/import-runs/*/undo", stale_undo)
        self.page.once("dialog", lambda dialog: dialog.accept())
        active_run = self.page.locator('#run-history-body tr[data-state="active"]').first
        run_id = active_run.get_attribute("data-run-id")
        active_run.locator('button[data-action="undo-run"]').click()
        self.page.locator("#error-banner").filter(has_text="run_state_conflict").wait_for()
        self.assertEqual(len(stale_requests), 1)
        self.assertEqual(
            self.page.locator(f'#run-history-body tr[data-run-id="{run_id}"]').get_attribute("data-state"),
            "active",
        )


if __name__ == "__main__":
    unittest.main()
