"""Search UI tests for Korai Studio.

Exercise the site-wide search (GET /search?q=...): navigating to it, running
searches with found/empty/no-result queries, and validating the result cards.
"""

import re
from urllib.parse import urlparse

import pytest
from playwright.sync_api import expect

SEARCH_PATH = "/search"
SEARCH_INPUT = 'input[name="q"]'
RESULT_CARDS = "a.card"

FOUND_QUERY = "shirt"
NO_RESULT_QUERY = "zzzznothing"


def search_for(page, query):
    """Run a search by going straight to the search results URL."""
    page.goto(f"{SEARCH_PATH}?q={query}")
    page.wait_for_load_state("networkidle")


def search_and_submit(page, query):
    """Fill the search box and press Enter."""
    page.goto(SEARCH_PATH)
    page.wait_for_load_state("networkidle")
    page.locator(SEARCH_INPUT).fill(query)
    with page.expect_navigation(wait_until="load", timeout=30000):
        page.locator(SEARCH_INPUT).press("Enter")
    page.wait_for_load_state("networkidle")


@pytest.mark.order(84)
@pytest.mark.case("positive", "Search box filters results and lands on /search")
def test_search_page_loads_and_submits(page):
    """Typing a query and pressing Enter produces a /search?q= results page."""
    search_and_submit(page, FOUND_QUERY)

    assert "/search" in page.url
    assert "q=" in page.url
    expect(page.locator("main h1").first).to_be_visible()
    assert page.locator(RESULT_CARDS).count() > 0


@pytest.mark.order(85)
@pytest.mark.case("positive", "Found results show matching product cards")
def test_search_found_results_show_cards(page):
    """A matching query returns product cards with real product links."""
    search_for(page, FOUND_QUERY)

    cards = page.locator(RESULT_CARDS)
    assert cards.count() > 0, "expected matching products in the results"
    result_text = page.locator("main").inner_text()
    assert re.search(r"\d+ results?", result_text), "expected a results count"

    href = urlparse(cards.first.get_attribute("href")).path
    assert href.startswith("/product/"), f"unexpected result link: {href}"
    assert page.locator(SEARCH_INPUT).input_value() == FOUND_QUERY


@pytest.mark.order(86)
@pytest.mark.case("negative", "No results produces a friendly message")
def test_search_no_results_shows_message(page):
    """An unmatched query shows a 'Nothing matched' message, not an error."""
    search_for(page, NO_RESULT_QUERY)

    text = page.locator("main").inner_text()
    assert "Nothing matched" in text, "expected a friendly no-results message"


@pytest.mark.order(87)
@pytest.mark.case("edge", "Empty query does not crash and keeps the search box")
def test_search_empty_query_stays_clean(page):
    """An empty query leaves the search page functional without results."""
    search_for(page, "")

    expect(page.locator(SEARCH_INPUT)).to_be_visible()
    body = page.locator("main").inner_text()
    assert "error" not in body.lower(), "empty search should not raise an error"


@pytest.mark.order(88)
@pytest.mark.case("edge", "A very long query is clamped to the input max length")
def test_search_long_query_respects_maxlength(page):
    """Over-long input clamps to the input's maxlength (80)."""
    page.goto(SEARCH_PATH)
    page.wait_for_load_state("networkidle")
    page.locator(SEARCH_INPUT).fill("k" * 200)
    value = page.locator(SEARCH_INPUT).input_value()
    assert len(value) <= 80, f"expected max length 80, got {len(value)}"


@pytest.mark.order(89)
@pytest.mark.case("positive", "Search results link to valid product pages")
def test_search_result_links_open_products(page):
    """Every result card points at a working product detail URL."""
    search_for(page, FOUND_QUERY)

    cards = page.locator(RESULT_CARDS)
    for i in range(min(cards.count(), 3)):
        href = cards.nth(i).get_attribute("href")
        assert href.startswith("/product/"), f"bad product link: {href}"


@pytest.mark.order(90)
@pytest.mark.case("negative", "Search card name matches the product page title")
def test_search_card_name_matches_product(page):
    """Opening the first result shows the same product name on its page."""
    search_for(page, FOUND_QUERY)

    card_name = page.locator(RESULT_CARDS).first.locator(".card-name").inner_text().strip()
    page.locator(RESULT_CARDS).first.click()
    page.wait_for_load_state("networkidle")

    product_heading = page.locator("main h1").first
    expect(product_heading).to_have_text(card_name, timeout=15000)
