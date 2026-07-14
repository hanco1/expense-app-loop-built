from __future__ import annotations

from backend.analysis import AnalysisService
from contracts.analysis import AnalysisTransaction, MonthSummary
from tests.backend.statement_support import StatementStoreTestCase


EXPECTED_CATEGORY_BY_MERCHANT = {
    "LOBLAWS 1049 TORONTO ON": "Groceries",
    "TIM HORTONS #2214 TORONTO ON": "Dining",
    "PRESTO FARE TORONTO ON": "Transportation",
    "AMAZON.CA *ORDER 698-002": "Shopping",
    "BELL CANADA MOBILITY": "Bills & Utilities",
    "E-TRANSFER RECEIVED J. WU": "Income",
    "SOBEYS #4412 TORONTO ON": "Groceries",
    "NETFLIX.COM 866-716-0414": "Entertainment",
    "PETRO-CANADA 7734 TORONTO": "Transportation",
    "SHOPPERS DRUG MART #0871": "Health & Fitness",
    "HYDRO ONE ELECTRICITY": "Bills & Utilities",
    "MONTHLY PLAN FEE": "Fees",
    "RENT E-TRANSFER TO LANDLORD": "Housing",
    "SQ *COFFEE CO TORONTO ON": "Dining",
    "AMAZON.CA *ORDER 702-441": "Shopping",
    "AMAZON.CA REFUND 702-441": "Refunds & Credits",
    "LCBO/RAO #0523 TORONTO": "Shopping",
    "UBER *TRIP TORONTO ON": "Transportation",
    "GOODLIFE FITNESS MEMBER": "Health & Fitness",
    "TIM HORTONS #0098 TORONTO": "Dining",
    "WALMART SUPERCENTER 3115": "Shopping",
}

EXPECTED_MONTHLY_CATEGORIES = {
    "2026-05": {
        "Bills & Utilities": 16_774,
        "Groceries": 16_378,
        "Transportation": 6_437,
        "Shopping": 5_423,
        "Health & Fitness": 1_984,
        "Entertainment": 1_799,
        "Fees": 1_095,
        "Dining": 450,
    },
    "2026-06": {
        "Housing": 185_000,
        "Shopping": 30_521,
        "Groceries": 25_727,
        "Bills & Utilities": 16_774,
        "Transportation": 8_047,
        "Health & Fitness": 6_554,
        "Dining": 2_100,
        "Entertainment": 1_799,
        "Fees": 1_095,
    },
}


class AnalysisStoreTestCase(StatementStoreTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.analysis = AnalysisService(self.store)

    def import_both(self) -> tuple[str, str]:
        return self.import_pdf(), self.import_csv()

    def transaction(
        self,
        summary: MonthSummary,
        *,
        merchant: str,
        amount_minor: int | None = None,
    ) -> AnalysisTransaction:
        matches = [
            transaction
            for transaction in summary.transactions
            if transaction.merchant == merchant
            and (
                amount_minor is None
                or transaction.amount_minor == amount_minor
            )
        ]
        self.assertEqual(len(matches), 1)
        return matches[0]

    @staticmethod
    def category_map(summary: MonthSummary) -> dict[str, int]:
        return {
            bucket.category: bucket.spending_minor
            for bucket in summary.category_breakdown
        }
