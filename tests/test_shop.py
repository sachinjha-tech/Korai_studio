"""Shop page filter & sort UI tests for https://www.thekoraistudio.com/shop.

Step 4 of the run — executed while signed in as sachin. Verifies the shop page
renders the product grid and that the filter & sort panel (sort, colour,
design, price range) narrows the grid and updates the querystring as expected.
"""

import pytest
from playwright.sync_api import expect

from pages.shop_page import ShopPage


@pytest.fixture
def shop_page(page):
    shop = ShopPage(page)
    shop.goto()
    return shop


@pytest.mark.order(60)
def test_shop_page_loads_signed_in(shop_page):
    """The shop page loads with products and the sachin session visible."""
    assert shop_page.page.title() == "Shop — Korai Studio"
    assert shop_page.heading().inner_text() == "Everything"
    assert shop_page.product_cards().count() >= 1
    account = shop_page.page.locator("header .account-link").first
    expect(account).to_contain_text("sachin", ignore_case=True, timeout=15000)


@pytest.mark.order(61)
def test_shop_filter_panel_opens_and_lists_widgets(shop_page):
    """The filter panel exposes sort, colour, design and price controls."""
    shop_page.open_filters()
    assert shop_page.filters_panel().is_visible()

    sort_options = shop_page.sort_select().evaluate(
        "s => [...s.options].map(o => o.value)"
    )
    assert {"new", "price-low", "price-high"} <= set(sort_options)
    assert shop_page.colour_select().evaluate("s => [...s.options].length") >= 2
    assert shop_page.design_select().evaluate("s => [...s.options].length") >= 2
    assert shop_page.price_min_input().is_visible()
    assert shop_page.price_max_input().is_visible()
    assert shop_page.apply_button().is_visible()


@pytest.mark.order(62)
def test_sort_by_price_low_to_high(shop_page):
    """Sorting by lowest price reorders the grid ascending."""
    shop_page.set_sort("price-low")
    assert shop_page.query_param("sort") == "price-low"
    prices = shop_page.sale_prices()
    assert len(prices) >= 2
    assert prices == sorted(prices)


@pytest.mark.order(63)
def test_sort_by_price_high_to_low(shop_page):
    """Sorting by highest price reorders the grid descending."""
    shop_page.set_sort("price-high")
    assert shop_page.query_param("sort") == "price-high"
    prices = shop_page.sale_prices()
    assert len(prices) >= 2
    assert prices == sorted(prices, reverse=True)


@pytest.mark.order(64)
def test_filter_by_colour_narrows_grid(shop_page):
    """Filtering by a colour reduces the grid to matching products."""
    total = shop_page.product_cards().count()
    shop_page.set_colour("Black")
    assert shop_page.query_param("color") == "Black"
    count = shop_page.product_cards().count()
    assert 1 <= count < total


@pytest.mark.order(65)
def test_filter_by_design_narrows_grid(shop_page):
    """Filtering by a design reduces the grid to matching products."""
    total = shop_page.product_cards().count()
    shop_page.set_design("Checks")
    assert shop_page.query_param("design") == "Checks"
    count = shop_page.product_cards().count()
    assert 1 <= count < total


@pytest.mark.order(66)
def test_price_range_filter_narrows_grid(shop_page):
    """A price range keeps only products whose sale price falls inside it."""
    shop_page.apply_price(min_price="500", max_price="900")
    assert shop_page.query_param("price_min") == "500"
    assert shop_page.query_param("price_max") == "900"
    prices = shop_page.sale_prices()
    assert prices, "no products within the price range"
    assert all(500 <= p <= 900 for p in prices)


@pytest.mark.order(67)
def test_filters_reset_to_default(shop_page):
    """A fresh visit to the shop shows the full, unfiltered grid."""
    shop_page.goto()
    assert shop_page.query_param("sort") in (None, "new")
    for name in ("color", "design", "price_min", "price_max"):
        assert shop_page.query_param(name) in (None, "")
    assert shop_page.product_cards().count() >= 1