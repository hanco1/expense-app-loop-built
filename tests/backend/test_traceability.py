from __future__ import annotations

from tests.backend.support import StoreTestCase


class TraceabilityTests(StoreTestCase):
    def test_occurrence_provenance_has_required_structured_fields(self) -> None:
        run_id = self.store.create_import_run("sha256:traceable-source")
        source_id, identity_id, occurrence_id = self.add_parsed_occurrence(
            run_id,
            locator="pdf-page:2:record:5",
            identity_fingerprint="txn:traceable",
        )

        provenance = self.store.get_occurrence_provenance(occurrence_id)

        self.assertEqual(
            provenance,
            {
                "occurrence_id": occurrence_id,
                "run_id": run_id,
                "source_fingerprint": "sha256:traceable-source",
                "source_record_id": source_id,
                "source_locator": "pdf-page:2:record:5",
                "transaction_identity_id": identity_id,
                "transaction_fingerprint": "txn:traceable",
                "inclusion_state": "included",
                "exclusion_reason": None,
            },
        )
        self.assertNotIn("retained_input", provenance)


if __name__ == "__main__":
    import unittest

    unittest.main()
