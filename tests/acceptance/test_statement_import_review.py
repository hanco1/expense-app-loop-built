from __future__ import annotations

import unittest

from tests.backend.statement_support import StatementStoreTestCase


class StatementImportReviewTests(StatementStoreTestCase):
    def test_approved_fixtures_match_every_expected_transaction_field(self) -> None:
        csv_run = self.import_csv()
        csv_actual = [
            (
                record["source_locator"],
                transaction["transaction_date"],
                transaction["merchant"],
                transaction["amount_minor"],
            )
            for record in self.store.get_import_run_detail(csv_run)
            if (transaction := record["normalized_transaction"]) is not None
        ]
        self.assertEqual(
            csv_actual,
            [
                ("csv-row:2", "2026-06-01", "RENT E-TRANSFER TO LANDLORD", -185000),
                ("csv-row:3", "2026-06-01", "TIM HORTONS #2214 TORONTO ON", -450),
                ("csv-row:4", "2026-06-01", "TIM HORTONS #2214 TORONTO ON", -450),
                ("csv-row:5", "2026-06-02", "LOBLAWS 1049 TORONTO ON", -8732),
                ("csv-row:6", "2026-06-03", "PRESTO FARE TORONTO ON", -335),
                ("csv-row:7", "2026-06-03", "SQ *COFFEE CO TORONTO ON", -675),
                ("csv-row:8", "2026-06-05", "SHOPPERS DRUG MART #0871", -2318),
                ("csv-row:9", "2026-06-06", "PETRO-CANADA 7734 TORONTO", -5840),
                ("csv-row:10", "2026-06-08", "AMAZON.CA *ORDER 702-441", -12999),
                ("csv-row:11", "2026-06-09", "BELL CANADA MOBILITY", -7514),
                ("csv-row:12", "2026-06-10", "AMAZON.CA REFUND 702-441", 12999),
                ("csv-row:13", "2026-06-12", "SOBEYS #4412 TORONTO ON", -6405),
                ("csv-row:14", "2026-06-13", "NETFLIX.COM 866-716-0414", -1799),
                ("csv-row:15", "2026-06-15", "E-TRANSFER RECEIVED J. WU", 60000),
                ("csv-row:16", "2026-06-16", "HYDRO ONE ELECTRICITY", -9260),
                ("csv-row:17", "2026-06-18", "LCBO/RAO #0523 TORONTO", -3145),
                ("csv-row:18", "2026-06-20", "UBER *TRIP TORONTO ON", -1872),
                ("csv-row:19", "2026-06-21", "LOBLAWS 1049 TORONTO ON", -10590),
                ("csv-row:20", "2026-06-23", "GOODLIFE FITNESS MEMBER", -4236),
                ("csv-row:22", "2026-06-27", "TIM HORTONS #0098 TORONTO", -525),
                ("csv-row:23", "2026-06-29", "WALMART SUPERCENTER 3115", -14377),
                ("csv-row:24", "2026-06-30", "MONTHLY PLAN FEE", -1095),
            ],
        )

        pdf_run = self.import_pdf()
        pdf_actual = [
            (
                record["source_locator"],
                transaction["transaction_date"],
                transaction["merchant"],
                transaction["amount_minor"],
            )
            for record in self.store.get_import_run_detail(pdf_run)
            if (transaction := record["normalized_transaction"]) is not None
        ]
        self.assertEqual(
            pdf_actual,
            [
                ("pdf-page:1:record:1", "2026-05-02", "LOBLAWS 1049 TORONTO ON", -9218),
                ("pdf-page:1:record:2", "2026-05-03", "TIM HORTONS #2214 TORONTO ON", -450),
                ("pdf-page:1:record:3", "2026-05-05", "PRESTO FARE TORONTO ON", -335),
                ("pdf-page:1:record:4", "2026-05-08", "AMAZON.CA *ORDER 698-002", -5423),
                ("pdf-page:1:record:5", "2026-05-10", "BELL CANADA MOBILITY", -7514),
                ("pdf-page:1:record:6", "2026-05-12", "E-TRANSFER RECEIVED J. WU", 60000),
                ("pdf-page:1:record:7", "2026-05-15", "SOBEYS #4412 TORONTO ON", -7160),
                ("pdf-page:1:record:8", "2026-05-18", "NETFLIX.COM 866-716-0414", -1799),
                ("pdf-page:1:record:9", "2026-05-20", "PETRO-CANADA 7734 TORONTO", -6102),
                ("pdf-page:1:record:10", "2026-05-24", "SHOPPERS DRUG MART #0871", -1984),
                ("pdf-page:1:record:11", "2026-05-28", "HYDRO ONE ELECTRICITY", -9260),
                ("pdf-page:1:record:12", "2026-05-31", "MONTHLY PLAN FEE", -1095),
            ],
        )

    def test_failed_import_cannot_leave_partial_active_support(self) -> None:
        content = (
            b"Date,Description,Debit,Credit,Balance\r\n"
            b"06/01/2026,FIRST GOOD ROW,1.00,,99.00\r\n"
            b"06/02/2026,OVERSIZED ROW,999999999999999999999999999999.00,,0.00\r\n"
        )

        try:
            run_id = self.importer.import_bytes(
                content,
                filename="supported-shape.csv",
                source_type="csv",
            )
        except Exception:
            self.assertEqual(
                self.store.entity_counts(),
                {
                    "import_runs": 0,
                    "source_records": 0,
                    "transaction_identities": 0,
                    "imported_occurrences": 0,
                    "manual_corrections": 0,
                    "normalized_transactions": 0,
                    "duplicate_links": 0,
                },
                "a rejected import must not leave an active partial run",
            )
            self.assertEqual(self.store.list_effective_transactions(), [])
            return

        summary = self.store.get_import_run_summary(run_id)
        self.assertEqual(
            (
                summary["source_record_count"],
                summary["parsed_count"],
                summary["failed_count"],
                summary["occurrence_count"],
            ),
            (2, 1, 1, 1),
        )
        failure = self.store.get_import_run_detail(run_id)[1]
        self.assertEqual(failure["parse_status"], "failed")
        self.assertEqual(failure["error_code"], "invalid_amount")
        self.assertIsNone(failure["normalized_transaction"])
        self.assertEqual(failure["inclusion_reason"], "parse_failed:invalid_amount")

    def test_decimal_exceptions_are_retained_as_invalid_amount_rows(self) -> None:
        for raw_amount in ("NaN", "1e999999"):
            with self.subTest(raw_amount=raw_amount):
                content = (
                    "Date,Description,Debit,Credit,Balance\r\n"
                    f"06/01/2026,DECIMAL EDGE,{raw_amount},,0.00\r\n"
                ).encode("utf-8")
                run_id = self.importer.import_bytes(
                    content,
                    filename=f"decimal-edge-{raw_amount}.csv",
                    source_type="csv",
                )

                summary = self.store.get_import_run_summary(run_id)
                self.assertEqual(summary["state"], "active")
                self.assertEqual(
                    (
                        summary["source_record_count"],
                        summary["parsed_count"],
                        summary["failed_count"],
                        summary["occurrence_count"],
                    ),
                    (1, 0, 1, 0),
                )
                failure = self.store.get_import_run_detail(run_id)[0]
                self.assertEqual(failure["parse_status"], "failed")
                self.assertEqual(failure["error_code"], "invalid_amount")
                self.assertIsNone(failure["normalized_transaction"])
                self.assertEqual(
                    failure["inclusion_reason"],
                    "parse_failed:invalid_amount",
                )


if __name__ == "__main__":
    unittest.main()
