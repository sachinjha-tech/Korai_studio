"""Homepage UI tests for https://www.thekoraistudio.com/.

Step 3 of the run — executed while signed in as sachin. Covers page load,
branding/logo, announcement bar, hero carousel, primary navigation, the
signed-in header state, full-page scroll, and validation of every link on the
homepage — without navigating into checkout or payment flows.
"""

from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect

from pages.home_page import HomePage

ROOT = "https://www.thekoraistudio.com"


@pytest.mark.order(50)
def test_homepage_loads_and_logo_visible(home_page):
    """The homepage loads successfully and the Korai Studio logo is shown."""
    assert home_page.page.title() == "Korai Studio"
    assert home_page.is_loaded()
    assert home_page.logo().is_visible()
    assert home_page.logo().get_attribute("alt") == "Korai Studio"


@pytest.mark.order(51)
def test_logo_is_a_link_back_to_home(home_page):
    """The logo is wrapped in a link back to the homepage root."""
    logo_link = home_page.page.locator("a.wordmark")
    assert logo_link.is_visible()
    assert logo_link.get_attribute("href") == "/"


@pytest.mark.order(52)
def test_announcement_bar_is_visible(home_page):
    """A promo/announcement strip is rendered at the top of the page."""
    bar = home_page.announce_bar()
    assert bar.is_visible()
    assert bar.inner_text().strip() != ""


@pytest.mark.order(53)
def test_hero_carousel_is_rendered(home_page):
    """The homepage hero carousel and its navigation dots are present."""
    assert home_page.page.locator("[data-carousel]").is_visible()
    assert home_page.page.locator("[data-carousel-slide]").count() >= 1
    assert home_page.page.locator("[data-carousel-dot]").count() >= 1


@pytest.mark.order(54)
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


@pytest.mark.order(55)
def test_main_navigation_items_visible_and_clickable(home_page):
    """Each primary nav link is visible, enabled and points at a same-site URL."""
    for label, path in HomePage.NAV_ITEMS:
        link = home_page.nav_link(label)
        assert link.is_visible(), f"{label!r} not visible"
        assert link.is_enabled(), f"{label!r} not enabled"
        href = link.get_attribute("href")
        assert href == path, f"{label!r} href={href!r}, expected {path!r}"


@pytest.mark.order(56)
def test_logged_in_as_sachin_on_homepage(home_page):
    """The header reflects the signed-in sachin session and wishlist link."""
    account = home_page.page.locator("header .account-link").first
    # The header is rendered client-side after load, so use web-first
    # assertions that retry until it reflects the signed-in session.
    expect(account).to_have_attribute("href", "/account", timeout=15000)
    expect(account).to_contain_text("sachin", ignore_case=True, timeout=15000)
    wishlist = home_page.page.locator("header a[href*='wishlist']").first
    expect(wishlist).to_have_attribute("href", "/wishlist")


@pytest.mark.order(57)
def test_homepage_scrolls_down_and_back_up(home_page):
    """Scrolling through the homepage reaches the footer; scrolling back to top."""
    home_page.scroll_to_bottom()
    assert home_page.footer().is_visible()
    assert home_page.page.locator("a.card").count() >= 1
    home_page.scroll_to_top()
    assert home_page.page.evaluate("() => window.scrollY") == 0
    assert home_page.logo().is_visible()


@pytest.mark.order(58)
def test_all_homepage_links_are_valid(home_page):
    """Every anchor on the homepage has a valid href and internal links resolve."""
    links = [a.get_attribute("href") for a in home_page.all_links().all()]
    links = [h for h in links if h and h.strip()]
    assert links, "no anchor links found on the homepage"

    checked = set()
    for raw in links:
        href = raw.strip()
        assert not href.lower().startswith("javascript:"), f"unsafe link {href!r}"

        if href.startswith("#"):
            continue  # in-page anchor
        if href.startswith("//"):
            continue  # protocol-relative external link

        parsed = urlsplit(href)
        if parsed.scheme in ("mailto", "tel"):
            continue
        if parsed.scheme in ("http", "https"):
            assert parsed.netloc, f"malformed absolute link {href!r}"
            continue  # external: authority is enough, we don't fetch it
        assert parsed.scheme == "", f"unsupported scheme in link {href!r}"
        assert href.startswith("/"), f"internal link must be root-relative: {href!r}"

        if href in checked:
            continue
        checked.add(href)
        response = home_page.page.request.get(ROOT + href, timeout=15000)
        assert response.status < 400, f"dead link {href!r} -> HTTP {response.status}"
