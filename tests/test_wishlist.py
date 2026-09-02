"""Wishlist (Saved) UI tests for Korai Studio.

Runs while the session is signed in (from step 2). These verify the empty
Saved page, adding an item to the wishlist from a product page, reflecting it
on the Saved page, and removing it again.
"""

import pytest
from playwright.sync_api import expect

WISHLIST_PATH = "/wishlist"
PRODUCT = "/product/blue-yellow-stripes-100-cotton"
PRODUCT_SLUG = "blue-yellow-stripes-100-cotton"
PRODUCT_NAME = "Blue & Yellow Stripes -100% Cotton"

WISHLIST_TOGGLE = (
    f'[data-wishlist-toggle="{PRODUCT_SLUG}"][aria-pressed="false"]'
)


def clean_wishlist(page):
    """Remove every saved item (toggle any pressed hearts off)."""
    page.goto(WISHLIST_PATH)
    page.wait_for_load_state("networkidle")
    while page.locator('[data-wishlist-toggle][aria-pressed="true"]').count():
        page.locator('[data-wishlist-toggle][aria-pressed="true"]').first.click()
        page.wait_for_timeout(600)
    page.goto(WISHLIST_PATH)
    page.wait_for_load_state("networkidle")


def add_to_wishlist(page):
    """Save the target product to the wishlist from its product page."""
    page.goto(PRODUCT)
    page.wait_for_load_state("networkidle")
    page.locator(
        f'button[data-wishlist-toggle="{PRODUCT_SLUG}"]'
    ).first.click()
    page.wait_for_timeout(1200)


@pytest.mark.order(91)
@pytest.mark.case("positive", "The Saved page loads with a helpful empty state")
def test_wishlist_empty_state(page):
    """An empty wishlist shows the 'Nothing saved yet' message."""
    clean_wishlist(page)

    expect(page.locator("main h1").first).to_contain_text("Saved")
    text = page.locator("main").inner_text()
    assert "Nothing saved yet" in text, "expected the empty-wishlist message"
    expect(page.locator('a[href="/shop"]:has-text("Browse the shop")').first).to_be_visible()


@pytest.mark.order(92)
@pytest.mark.case("positive", "Save for later adds an item to the wishlist")
def test_save_product_to_wishlist(page):
    """Toggling the heart on the product page saves the item."""
    clean_wishlist(page)
    add_to_wishlist(page)

    page.goto(WISHLIST_PATH)
    page.wait_for_load_state("networkidle")

    cards = page.locator("div.card")
    assert cards.count() >= 1, "expected a saved product on the wishlist page"
    assert page.locator('[data-wishlist-toggle][aria-pressed="true"]').count() >= 1


@pytest.mark.order(93)
@pytest.mark.case("positive", "The saved item is the correct product")
def test_wishlist_shows_correct_product(page):
    """The wishlist lists the exact product that was saved."""
    clean_wishlist(page)
    add_to_wishlist(page)
    page.goto(WISHLIST_PATH)
    page.wait_for_load_state("networkidle")

    first_card = page.locator("div.card").first
    href = first_card.locator("a.card-body").get_attribute("href")
    assert href == PRODUCT, f"expected {PRODUCT}, got {href}"
    expect(page.locator("div.card").first.locator(".card-name")).to_contain_text(
        PRODUCT_NAME
    )


@pytest.mark.order(94)
@pytest.mark.case("positive", "A saved item is reflected on the Saved page heart")
def test_wishlist_heart_state_reflected(page):
    """The heart on the Saved page shows the item as saved (pressed)."""
    clean_wishlist(page)
    add_to_wishlist(page)
    page.goto(WISHLIST_PATH)
    page.wait_for_load_state("networkidle")

    heart = page.locator(
        f'[data-wishlist-toggle="{PRODUCT_SLUG}"]'
    ).first
    assert heart.get_attribute("aria-pressed") == "true"


@pytest.mark.order(95)
@pytest.mark.case("negative", "Removing the item empties the wishlist again")
def test_remove_from_wishlist(page):
    """Un-save the item and confirm the wishlist returns to its empty state."""
    clean_wishlist(page)
    add_to_wishlist(page)
    page.goto(WISHLIST_PATH)
    page.wait_for_load_state("networkidle")

    heart = page.locator(
        f'[data-wishlist-toggle="{PRODUCT_SLUG}"]'
    ).first
    heart.click()
    page.wait_for_timeout(800)
    page.goto(WISHLIST_PATH)
    page.wait_for_load_state("networkidle")

    assert page.locator('[data-wishlist-toggle][aria-pressed="true"]').count() == 0
    assert "Nothing saved yet" in page.locator("main").inner_text()
