from __future__ import annotations

import csv
import io
import unittest

from tests.backend.statement_support import StatementStoreTestCase


SQLITE_INTEGER_MAX = 9_223_372_036_854_775_807
THOUSAND_ZEROS = "0" * 1000
HUGE_EXPONENT = "9" * 80

VALID_AMOUNT_CASES = (
    ("V01-zero", "0", 0),
    ("V02-zero-leading", "00.00", 0),
    ("V03-zero-plus", "+0", 0),
    ("V04-zero-leading-point", ".00", 0),
    ("V05-zero-trailing-point", "0.", 0),
    ("V06-one-cent", "0.01", 1),
    ("V07-one-cent-leading-point", ".01", 1),
    ("V08-one-cent-plus", "+.01", 1),
    ("V09-integer", "1", 100),
    ("V10-integer-trailing-point", "1.", 100),
    ("V11-leading-zeros", "001.23", 123),
    ("V12-trailing-fractional-zeros", "1.2300", 123),
    ("V13-ordinary", "999.99", 99_999),
    ("V14-inclusive-maximum", "92233720368547758.07", SQLITE_INTEGER_MAX),
    ("V15-maximum-padding", "00092233720368547758.0700", SQLITE_INTEGER_MAX),
    ("V16-scientific-zero-exponent", "1e0", 100),
    ("V17-scientific-positive-exponent", "1E+2", 10_000),
    ("V18-scientific-cent", "+1e-2", 1),
    ("V19-scientific-coefficient", "123e-2", 123),
    ("V20-scientific-trailing-zeros", "12300e-4", 123),
    ("V21-scientific-leading-point", ".1e1", 100),
    ("V22-scientific-leading-point-cent", ".1e-1", 1),
    ("V23-scientific-trailing-point", "1.e2", 10_000),
    ("V24-scientific-leading-zeros", "001e-2", 1),
    (
        "V25-scientific-maximum-integer-coefficient",
        "9223372036854775807e-2",
        SQLITE_INTEGER_MAX,
    ),
    (
        "V26-scientific-maximum-decimal-coefficient",
        "9.223372036854775807e16",
        SQLITE_INTEGER_MAX,
    ),
    ("V27-zero-large-positive-exponent", "0e999999", 0),
    ("V28-zero-large-negative-exponent", "0e-999999999", 0),
    ("V29-zero-runtime-positive-exponent", "0e+" + HUGE_EXPONENT, 0),
    ("V30-zero-runtime-negative-exponent", "0e-" + HUGE_EXPONENT, 0),
    ("V31-long-leading-zeros", THOUSAND_ZEROS + "1.23", 123),
    ("V32-long-trailing-zeros", "1.23" + THOUSAND_ZEROS, 123),
    (
        "V33-long-maximum-trailing-zeros",
        "92233720368547758.07" + THOUSAND_ZEROS,
        SQLITE_INTEGER_MAX,
    ),
    ("V34-long-scientific-one", "1" + THOUSAND_ZEROS + "e-1000", 100),
    ("V35-long-scientific-cent", "1" + THOUSAND_ZEROS + "e-1002", 1),
    ("V36-long-scientific-amount", "123" + THOUSAND_ZEROS + "e-1002", 123),
)

INVALID_AMOUNT_CASES = (
    ("I01-nan", "NaN"),
    ("I02-nan-plus", "+NaN"),
    ("I03-nan-minus", "-NaN"),
    ("I04-nan-lower", "nan"),
    ("I05-nan-payload", "NaN123"),
    ("I06-snan", "sNaN"),
    ("I07-snan-plus", "+sNaN"),
    ("I08-snan-minus-payload", "-sNaN42"),
    ("I09-infinity", "Infinity"),
    ("I10-infinity-plus", "+Infinity"),
    ("I11-infinity-minus", "-Infinity"),
    ("I12-inf-short", "Inf"),
    ("I13-inf-short-plus", "+inf"),
    ("I14-inf-short-minus", "-INF"),
    ("I15-negative-zero", "-0"),
    ("I16-negative-zero-fixed", "-0.00"),
    ("I17-negative-zero-leading-point", "-.00"),
    ("I18-negative-zero-scientific", "-0e0"),
    ("I19-negative-zero-large-exponent", "-0E+999999"),
    ("I20-negative-integer", "-1"),
    ("I21-negative-cent", "-0.01"),
    ("I22-negative-scientific", "-1e2"),
    ("I23-fractional-cent", "0.001"),
    ("I24-fractional-cent-ordinary", "1.234"),
    ("I25-fractional-cent-long", "0.009999999999999999"),
    ("I26-maximum-fractional-tail", "92233720368547758.0701"),
    ("I27-long-fractional-tail", "1.23" + THOUSAND_ZEROS + "1"),
    ("I28-scientific-fractional-cent", "1e-3"),
    ("I29-scientific-fractional-coefficient", "123e-3"),
    ("I30-scientific-fractional-mantissa", "1.234e0"),
    ("I31-underflow", "1e-999999"),
    ("I32-underflow-runtime", "1e-999999999"),
    ("I33-underflow-mantissa", "9.99e-1000000"),
    ("I34-underflow-huge-exponent", "1e-" + HUGE_EXPONENT),
    ("I35-over-maximum-cent", "92233720368547758.08"),
    ("I36-over-maximum-integer", "92233720368547759"),
    ("I37-over-maximum-scientific-integer", "9223372036854775808e-2"),
    ("I38-over-maximum-scientific-decimal", "9.223372036854775808e16"),
    ("I39-over-maximum-power", "1e17"),
    ("I40-overflow", "1e999999"),
    ("I41-overflow-huge-exponent", "1e" + HUGE_EXPONENT),
    ("I42-long-over-range-integer", "1" + THOUSAND_ZEROS),
    (
        "I43-long-scientific-fractional-tail",
        "123" + THOUSAND_ZEROS + "1e-1003",
    ),
    ("I44-grouping-comma", "1,234.56"),
    ("I45-locale-decimal-comma", "1.234,56"),
    ("I46-decimal-comma", "1,23"),
    ("I47-currency-dollar", "$1.00"),
    ("I48-currency-canadian-dollar", "C$1.00"),
    ("I49-currency-code-prefix", "CAD 1.00"),
    ("I50-currency-code-suffix", "1.00 CAD"),
    ("I51-underscore", "1_000.00"),
    ("I52-grouping-space", "1 000.00"),
    ("I53-grouping-nbsp", "1\u00a0000.00"),
    ("I54-grouping-apostrophe", "1'000.00"),
    ("I55-parentheses", "(1.00)"),
    ("I56-trailing-sign", "1.00-"),
    ("I57-hex", "0x10"),
    ("I58-binary", "0b10"),
    ("I59-ratio", "1/2"),
    ("I60-percent", "100%"),
    ("I61-leading-space", " 1.00"),
    ("I62-trailing-space", "1.00 "),
    ("I63-leading-tab", "\t1.00"),
    ("I64-trailing-tab", "1.00\t"),
    ("I65-embedded-space", "1 .00"),
    ("I66-embedded-tab", "1\t.00"),
    ("I67-exponent-space", "1e 2"),
    ("I68-plus-space", "+ 1.00"),
    ("I69-leading-nbsp", "\u00a01.00"),
    ("I70-leading-zero-width-space", "\u200b1.00"),
    ("I71-leading-bom", "\ufeff1.00"),
    ("I72-trailing-nul", "1.00\x00"),
    ("I73-arabic-indic-digits", "١.٢٣"),
    ("I74-eastern-arabic-digits", "۱.۲۳"),
    ("I75-devanagari-digits", "१.२३"),
    ("I76-fullwidth-digits", "１.２３"),
    ("I77-fullwidth-punctuation", "１．２３"),
    ("I78-unicode-minus", "−1.00"),
    ("I79-fullwidth-plus", "＋1.00"),
    ("I80-mathematical-digits", "𝟙.𝟚𝟛"),
    ("I81-arabic-decimal-separator", "١٫٢٣"),
    ("I82-bare-point", "."),
    ("I83-bare-plus", "+"),
    ("I84-bare-minus", "-"),
    ("I85-double-point", "1..0"),
    ("I86-multiple-points", "1.2.3"),
    ("I87-exponent-missing-digits", "1e"),
    ("I88-exponent-plus-missing-digits", "1e+"),
    ("I89-exponent-minus-missing-digits", "1e-"),
    ("I90-exponent-missing-coefficient", "e2"),
    ("I91-exponent-point-coefficient", ".e2"),
    ("I92-double-exponent", "1ee2"),
    ("I93-decimal-exponent", "1e2.0"),
    ("I94-double-plus-exponent", "1e++2"),
    ("I95-double-minus-exponent", "1e--2"),
    ("I96-double-plus", "++1"),
    ("I97-plus-minus", "+-1"),
    ("I98-double-minus", "--1"),
    ("I99-exponent-plus-space", "1E+ 2"),
    ("I100-wrong-exponent-marker", "1d2"),
)

MISSING_AMOUNT_CASES = (
    ("A01-both-empty", "", ""),
    ("A02-debit-spaces", "   ", ""),
    ("A03-debit-tab", "\t", ""),
    ("A04-debit-nbsp", "\u00a0", ""),
    ("A05-credit-spaces", "", "   "),
    ("A06-credit-tab", "", "\t"),
    ("A07-credit-nbsp", "", "\u00a0"),
)

ABSENT_COUNTERPART_CASES = (
    ("A08-space-debit-credit-valid", "   ", "1.23", 123),
    ("A09-debit-valid-tab-credit", "1.23", "\t", -123),
)


def _amount_statement(case_id: str, debit: str, credit: str) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(["Date", "Description", "Debit", "Credit", "Balance"])
    writer.writerow(["06/01/2026", f"MATRIX {case_id}", debit, credit, "0.00"])
    return output.getvalue().encode("utf-8")


class StatementImportReviewTests(StatementStoreTestCase):
    def _import_amount_case(self, case_id: str, debit: str, credit: str):
        run_id = self.importer.import_bytes(
            _amount_statement(case_id, debit, credit),
            filename=f"amount-matrix-{case_id}.csv",
            source_type="csv",
        )
        return (
            self.store.get_import_run_summary(run_id),
            self.store.get_import_run_detail(run_id)[0],
        )

    def _assert_amount_failure(
        self,
        case_id: str,
        debit: str,
        credit: str,
        error_code: str,
    ) -> None:
        summary, detail = self._import_amount_case(case_id, debit, credit)
        self.assertEqual(summary["state"], "active")
        self.assertEqual(
            (
                summary["source_record_count"],
                summary["parsed_count"],
                summary["failed_count"],
                summary["occurrence_count"],
                detail["parse_status"],
                detail["error_code"],
                detail["normalized_transaction"],
                detail["inclusion_reason"],
            ),
            (1, 0, 1, 0, "failed", error_code, None, f"parse_failed:{error_code}"),
        )

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

    def test_amount_token_boundary_matrix(self) -> None:
        for case_id, raw_amount, expected_minor in VALID_AMOUNT_CASES:
            for path in ("debit", "credit"):
                with self.subTest(case_id=case_id, path=path):
                    debit = raw_amount if path == "debit" else ""
                    credit = raw_amount if path == "credit" else ""
                    summary, detail = self._import_amount_case(
                        f"{case_id}-{path}",
                        debit,
                        credit,
                    )
                    expected_signed_minor = (
                        -expected_minor if path == "debit" else expected_minor
                    )
                    transaction = detail["normalized_transaction"]
                    self.assertEqual(summary["state"], "active")
                    self.assertEqual(
                        (
                            summary["source_record_count"],
                            summary["parsed_count"],
                            summary["failed_count"],
                            summary["occurrence_count"],
                            detail["parse_status"],
                            detail["error_code"],
                            None if transaction is None else transaction["amount_minor"],
                            detail["inclusion_reason"],
                        ),
                        (1, 1, 0, 1, "parsed", None, expected_signed_minor, "active_support"),
                    )

        for case_id, raw_amount in INVALID_AMOUNT_CASES:
            for path in ("debit", "credit"):
                with self.subTest(case_id=case_id, path=path):
                    self._assert_amount_failure(
                        f"{case_id}-{path}",
                        raw_amount if path == "debit" else "",
                        raw_amount if path == "credit" else "",
                        "invalid_amount",
                    )

        for case_id, debit, credit in MISSING_AMOUNT_CASES:
            with self.subTest(case_id=case_id):
                self._assert_amount_failure(
                    case_id,
                    debit,
                    credit,
                    "missing_amount",
                )

        for case_id, debit, credit, expected_minor in ABSENT_COUNTERPART_CASES:
            with self.subTest(case_id=case_id):
                summary, detail = self._import_amount_case(case_id, debit, credit)
                transaction = detail["normalized_transaction"]
                self.assertEqual(
                    (
                        summary["source_record_count"],
                        summary["parsed_count"],
                        summary["failed_count"],
                        summary["occurrence_count"],
                        None if transaction is None else transaction["amount_minor"],
                        detail["inclusion_reason"],
                    ),
                    (1, 1, 0, 1, expected_minor, "active_support"),
                )

        with self.subTest(case_id="A10-both-present"):
            self._assert_amount_failure(
                "A10-both-present",
                "1.00",
                "2.00",
                "ambiguous_amount",
            )


if __name__ == "__main__":
    unittest.main()
