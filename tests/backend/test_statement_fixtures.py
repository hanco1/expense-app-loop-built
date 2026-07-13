from __future__ import annotations

import hashlib
import unittest
from pathlib import Path


FIXTURE_DIR = Path(__file__).parent / "fixtures"
CSV_FIXTURE = FIXTURE_DIR / "td-mock-2026-06.csv"
PDF_FIXTURE = FIXTURE_DIR / "td-mock-2026-05.pdf"


class StatementFixtureTests(unittest.TestCase):
    def test_authorized_fixtures_have_pinned_hashes(self) -> None:
        expected = {
            CSV_FIXTURE: "9F93F107DDD02AEE2FB0A0AE19EB962180C680D1FB06D4D90959C96ED8CD7BAA",
            PDF_FIXTURE: "F4B6B524D7C6140EE3F3E24CE87C4A36F0B40619395B5DC17B03F1B99DBC11F8",
        }
        for fixture, expected_hash in expected.items():
            with self.subTest(fixture=fixture.name):
                self.assertTrue(fixture.is_file())
                self.assertEqual(
                    hashlib.sha256(fixture.read_bytes()).hexdigest().upper(),
                    expected_hash,
                )


if __name__ == "__main__":
    unittest.main()
