import asyncio
import logging
from decimal import Decimal

import pytest

from starter import recommend_price, sample_fetch_offers


def make_fetch(offers, status="success"):
    async def fetch():
        return {"status": status, "offers": offers}

    return fetch


def offer(price, days=1, seller="RIVAL"):
    return {"seller": seller, "price": Decimal(price), "delivery_days": days}


def run(fetch, current="1000.00", minimum="1.00", **kwargs):
    return asyncio.run(
        recommend_price(fetch, Decimal(current), Decimal(minimum), **kwargs)
    )


def test_sample_from_task():
    result = run(sample_fetch_offers, current="4900.00", minimum="4500.00")
    assert result["price"] == Decimal("4728.00")
    assert result["decision"] == "APPLY"
    assert result["reason"]


def test_timeout_returns_hold():
    async def slow_fetch():
        await asyncio.sleep(1)
        return {"status": "success", "offers": [offer("900.00")]}

    result = run(slow_fetch, current="1000.00", timeout_s=0.05)
    assert result["price"] == Decimal("1000.00")
    assert result["decision"] == "HOLD"


def test_source_exception_returns_hold_and_logs(caplog):
    async def broken_fetch():
        raise ConnectionError("source down")

    with caplog.at_level(logging.ERROR, logger="starter"):
        result = run(broken_fetch, current="1000.00")
    assert (result["price"], result["decision"]) == (Decimal("1000.00"), "HOLD")
    assert caplog.records[0].exc_info[0] is ConnectionError  # traceback сохранён


@pytest.mark.parametrize("status", ["partial", "error"])
def test_not_success_status_returns_hold(status):
    result = run(make_fetch([offer("900.00")], status=status), current="1000.00")
    assert (result["price"], result["decision"]) == (Decimal("1000.00"), "HOLD")


def test_no_eligible_offers_holds_even_below_min_price():
    offers = [
        offer("500.00", seller="MyShop"),
        offer("500.00", seller="MYSHOP"),
        offer("500.00", days=7),
        offer("500.00", days=None),
    ]
    result = run(make_fetch(offers), current="800.00", minimum="900.00")
    assert (result["price"], result["decision"]) == (Decimal("800.00"), "HOLD")


def test_min_price_floor():
    # 900 * 0.985 = 886.50 < min_price 950
    result = run(make_fetch([offer("900.00")]), current="1000.00", minimum="950.00")
    assert (result["price"], result["decision"]) == (Decimal("950.00"), "APPLY")


def test_rounds_down_to_kopeck():
    # 1000.01 * 0.985 = 985.00985 -> 985.00
    result = run(make_fetch([offer("1000.01")]), current="1000.00")
    assert result["price"] == Decimal("985.00")


def test_delivery_boundaries_and_cheapest_competitor():
    offers = [offer("1100.00", days=0), offer("1000.00", days=6), offer("10.00", days=7)]
    result = run(make_fetch(offers), current="1000.00")
    assert result["price"] == Decimal("985.00")  # 1000.00 * 0.985


@pytest.mark.parametrize(
    "competitor, expected_price, expected_decision",
    [
        ("710.66", "700.00", "APPLY"),  # ровно -30% от 1000.00
        ("710.65", "699.99", "REVIEW"),  # чуть больше -30%
        ("1319.80", "1300.00", "APPLY"),  # ровно +30%
        ("1319.81", "1300.01", "REVIEW"),  # чуть больше +30%
    ],
)
def test_30_percent_boundary(competitor, expected_price, expected_decision):
    result = run(make_fetch([offer(competitor)]), current="1000.00")
    assert result["price"] == Decimal(expected_price)
    assert result["decision"] == expected_decision
