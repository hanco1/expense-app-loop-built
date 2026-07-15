from __future__ import annotations

from tests.backend.local_web_api_support import CSRF_TOKEN, LocalWebApiTestCase


class LocalWebApiDecisionTests(LocalWebApiTestCase):
    def test_category_and_tim_hortons_decisions_are_append_only(self) -> None:
        imported = self.import_fixture("csv")
        june = self.data(self.api.dispatch("GET", "/api/months/2026-06"))
        grocery = next(
            row for row in june["transactions"] if row["merchant"].startswith("LOBLAWS")
        )
        counts_before_invalid = self.store.entity_counts()
        invalid_category = self.post_json(
            f"/api/transactions/{grocery['identity_id']}/category",
            {"category": "Not A Canonical Category"},
        )
        self.assertEqual(invalid_category.status, 400)
        self.assertEqual(self.store.entity_counts(), counts_before_invalid)
        duplicate_key = self.api.dispatch(
            "POST",
            f"/api/transactions/{grocery['identity_id']}/category",
            headers={
                "Content-Type": "application/json",
                "X-Local-Expense-CSRF": CSRF_TOKEN,
            },
            body=b'{"category":"Dining","category":"Shopping"}',
        )
        self.assertEqual(duplicate_key.status, 400)
        self.assertEqual(self.store.entity_counts(), counts_before_invalid)
        first_category = self.post_json(
            f"/api/transactions/{grocery['identity_id']}/category",
            {"category": "Dining"},
        )
        second_category = self.post_json(
            f"/api/transactions/{grocery['identity_id']}/category",
            {"category": "Shopping"},
        )
        category_state = self.data(second_category)
        self.assertEqual(first_category.status, 200)
        self.assertEqual(category_state["effective_category"], "Shopping")
        self.assertEqual(len(category_state["history"]), 2)
        self.assertEqual(
            len({row["correction_id"] for row in category_state["history"]}),
            2,
        )

        candidates = self.data(self.api.dispatch("GET", "/api/duplicates"))
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["effective_decision"], "pending")
        self.assertTrue(candidate["left"]["included"])
        self.assertTrue(candidate["right"]["included"])
        self.assertEqual(candidate["left"]["amount_minor"], "-450")
        self.assertEqual(candidate["right"]["amount_minor"], "-450")

        same = self.post_json(
            f"/api/duplicates/{candidate['duplicate_link_id']}/decision",
            {
                "decision": "same_transaction",
                "kept_identity_id": candidate["left"]["identity_id"],
            },
        )
        same_state = self.data(same)
        self.assertEqual(len(same_state["history"]), 1)
        self.assertTrue(same_state["left"]["included"])
        self.assertFalse(same_state["right"]["included"])
        run_detail = self.data(
            self.api.dispatch(
                "GET",
                f"/api/import-runs/{imported['summary']['run_id']}",
            )
        )
        excluded_record = next(
            row
            for row in run_detail["records"]
            if row["identity_id"] == candidate["right"]["identity_id"]
        )
        self.assertEqual(excluded_record["duplicate_state"], "same_transaction")
        self.assertFalse(excluded_record["effective_included"])
        self.assertEqual(
            excluded_record["effective_inclusion_reason"],
            "human_duplicate_same_transaction",
        )

        distinct = self.post_json(
            f"/api/duplicates/{candidate['duplicate_link_id']}/decision",
            {"decision": "distinct"},
        )
        distinct_state = self.data(distinct)
        self.assertEqual(distinct_state["effective_decision"], "distinct")
        self.assertEqual(len(distinct_state["history"]), 2)
        self.assertTrue(distinct_state["left"]["included"])
        self.assertTrue(distinct_state["right"]["included"])

    def test_invalid_component_proposal_returns_409_without_append(self) -> None:
        identities = self.seed_duplicate_group()
        ab = self.duplicate_for(identities["A"], identities["B"])
        bc = self.duplicate_for(identities["B"], identities["C"])
        ac = self.duplicate_for(identities["A"], identities["C"])

        self.assertEqual(
            self.post_json(
                f"/api/duplicates/{ab['duplicate_link_id']}/decision",
                {
                    "decision": "same_transaction",
                    "kept_identity_id": identities["A"],
                },
            ).status,
            200,
        )
        self.assertEqual(
            self.post_json(
                f"/api/duplicates/{bc['duplicate_link_id']}/decision",
                {
                    "decision": "same_transaction",
                    "kept_identity_id": identities["B"],
                },
            ).status,
            200,
        )
        counts_before = self.store.entity_counts()
        rejected = self.post_json(
            f"/api/duplicates/{ac['duplicate_link_id']}/decision",
            {
                "decision": "same_transaction",
                "kept_identity_id": identities["C"],
            },
        )
        self.assertEqual(rejected.status, 409)
        self.assertEqual(
            rejected.json()["error"]["code"],
            "duplicate_graph_conflict",
        )
        self.assertEqual(self.store.entity_counts(), counts_before)
        after = self.duplicate_for(identities["A"], identities["C"])
        self.assertEqual(after["effective_decision"], "pending")
        self.assertEqual(after["history"], [])


if __name__ == "__main__":
    import unittest

    unittest.main()
