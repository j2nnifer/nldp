from datetime import date
import pytest
from nldate import parse


@pytest.mark.parametrize(
    "input_str, ref, expected",
    [
        ("December 1st, 2025", None, date(2025, 12, 1)),
        ("5 days before December 1st, 2025", None, date(2025, 11, 26)),
        ("yesterday", date(2024, 1, 1), date(2023, 12, 31)),
        ("tomorrow", date(2024, 1, 1), date(2024, 1, 2)),
        ("2 weeks from now", date(2024, 1, 1), date(2024, 1, 15)),
        ("1 year and 2 months after yesterday", date(2024, 3, 1), date(2025, 5, 1)),
        ("next Tuesday", date(2024, 5, 20), date(2024, 5, 21)),
        ("3 days ago", date(2024, 5, 20), date(2024, 5, 17)),
        ("in 10 days", date(2024, 1, 1), date(2024, 1, 11)),
        ("Jan 1st 2026", None, date(2026, 1, 1)),
    ],
)
def test_parse_logic(input_str, ref, expected):
    assert parse(input_str, today=ref) == expected
