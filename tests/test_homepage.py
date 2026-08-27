"""Homepage UI tests for https://shop.thekoraistudio.com/.

Covers page load, branding/logo, announcement bar, hero carousel and primary
navigation — without navigating into checkout or payment flows.
"""

from pages.home_page import HomePage

import pytest


@pytest.mark.order(30)
def test_homepage_loads_and_logo_visible(home_page):
    """The homepage loads successfully and the Korai Studio logo is shown."""
    assert home_page.page.title() == "Korai Studio"
    assert home_page.is_loaded()
    assert home_page.logo().is_visible()
    assert home_page.logo().get_attribute("alt") == "Korai Studio"


@pytest.mark.order(31)
def test_logo_is_a_link_back_to_home(home_page):
    """The logo is wrapped in a link back to the homepage root."""
    logo_link = home_page.page.locator("a.wordmark")
    assert logo_link.is_visible()
    assert logo_link.get_attribute("href") == "/"


@pytest.mark.order(32)
def test_announcement_bar_is_visible(home_page):
    """A promo/announcement strip is rendered at the top of the page."""
    bar = home_page.announce_bar()
    assert bar.is_visible()
    assert bar.inner_text().strip() != ""


@pytest.mark.order(33)
def test_hero_carousel_is_rendered(home_page):
    """The homepage hero carousel and its navigation dots are present."""
    assert home_page.page.locator("[data-carousel]").is_visible()
    assert home_page.page.locator("[data-carousel-slide]").count() >= 1
    assert home_page.page.locator("[data-carousel-dot]").count() >= 1


@pytest.mark.order(34)
def test_product_section_shows_items(home_page):
    """The homepage displays product cards in the featured section."""
    cards = home_page.page.locator(".slider-item a.card")
    assert cards.count() >= 1
    for i in range(cards.count()):
        card = cards.nth(i)
        name = card.locator(".card-name")
        assert name.is_visible()
        assert name.inner_text().strip() != ""
        # Cards should link to same-site product pages, not checkout.
        href = card.get_attribute("href")
        assert href is not None and href.startswith("/product/")


@pytest.mark.order(35)
def test_main_navigation_items_visible_and_clickable(home_page):
    """Each primary nav link is visible, enabled and points at a same-site URL."""
    for label, path in HomePage.NAV_ITEMS:
        link = home_page.nav_link(label)
        assert link.is_visible(), f"{label!r} not visible"
        assert link.is_enabled(), f"{label!r} not enabled"
        href = link.get_attribute("href")
        assert href == path, f"{label!r} href={href!r}, expected {path!r}"
