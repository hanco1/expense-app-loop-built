from __future__ import annotations

from tests.backend.support import StoreTestCase


class MoneyTests(StoreTestCase):
    def test_integer_minor_units_and_currency_round_trip_exactly(self) -> None:
        run_id = self.store.create_import_run("sha256:money")
        _, _, occurrence_id = self.add_parsed_occurrence(
            run_id,
            locator="csv-row:2",
            identity_fingerprint="txn:money",
            amount_minor=-1234567890123,
            currency="CAD",
        )
        occurrence = self.store.get_occurrence(occurrence_id)
        self.assertEqual(occurrence["amount_minor"], -1234567890123)
        self.assertIs(type(occurrence["amount_minor"]), int)
        self.assertEqual(occurrence["currency"], "CAD")

    def test_binary_float_and_boolean_amounts_are_rejected(self) -> None:
        run_id = self.store.create_import_run("sha256:float")
        source_id = self.store.add_source_record(
            run_id,
            source_locator="csv-row:2",
            retained_input="synthetic,float",
            parse_status="parsed",
        )
        identity_id = self.store.get_or_create_identity("txn:float")
        for invalid_amount in (12.34, True):
            with self.subTest(amount=invalid_amount):
                with self.assertRaises(TypeError):
                    self.store.add_occurrence(
                        run_id,
                        source_record_id=source_id,
                        identity_id=identity_id,
                        amount_minor=invalid_amount,
                        currency="CAD",
                    )

    def test_currency_is_required_and_must_be_uppercase_iso_shape(self) -> None:
        run_id = self.store.create_import_run("sha256:currency")
        source_id = self.store.add_source_record(
            run_id,
            source_locator="csv-row:2",
            retained_input="synthetic,currency",
            parse_status="parsed",
        )
        identity_id = self.store.get_or_create_identity("txn:currency")
        for invalid_currency in (None, "", "cad", "CA", "CADX"):
            with self.subTest(currency=invalid_currency):
                with self.assertRaises(ValueError):
                    self.store.add_occurrence(
                        run_id,
                        source_record_id=source_id,
                        identity_id=identity_id,
                        amount_minor=-100,
                        currency=invalid_currency,
                    )


if __name__ == "__main__":
    import unittest

    unittest.main()
