"""Navigation UI tests for https://shop.thekoraistudio.com/.

Verifies clicks on primary nav items navigate to the right pages, the brand
logo returns home, the Collections dropdown reveals its links, and the header
cart link points at the bag — while never entering a checkout or payment flow.
"""

import pytest

from pages.home_page import HomePage


@pytest.mark.parametrize("label,path,title,heading", [
    ("Shop", "/shop", "Shop — Korai Studio", "Everything"),
    ("Best Sellers", "/best-sellers", "Best Sellers — Korai Studio", "Best Sellers"),
    ("New Arrivals", "/new-arrivals", "New Arrivals — Korai Studio", "New Arrivals"),
])
def test_primary_nav_navigates_to_expected_page(home_page, label, path, title, heading):
    """Clicking a primary nav item lands on the right page with the right title."""
    home_page.click_nav(label)
    home_page.page.wait_for_url(f"**{path}")
    assert home_page.page.title() == title
    assert heading.casefold() in home_page.main_heading().inner_text().casefold()


def test_logo_navigates_back_home(home_page):
    """Clicking the logo returns the user to the homepage root."""
    home_page.click_nav("Shop")
    assert home_page.page.url.endswith("/shop")
    home_page.logo().click()
    home_page.page.wait_for_load_state("networkidle")
    assert home_page.page.url.rstrip("/").endswith("shop.thekoraistudio.com")


def test_collections_dropdown_reveals_links(home_page):
    """Hovering Collections shows its top-level sub-category links, all same-site."""
    home_page.open_dropdown()
    links = home_page.dropdown_group_links()
    assert links.count() >= 2
    for i in range(links.count()):
        link = links.nth(i)
        assert link.is_visible()
        href = link.get_attribute("href")
        assert href is not None and href.startswith("/")
        assert "checkout" not in href.lower()
        assert "payment" not in href.lower()


def test_collections_subgroup_expands_and_links_visited(home_page):
    """Expanding 'Launching Soon' reveals its links, all pointing to same-site pages."""
    home_page.open_dropdown()
    toggle = home_page.dropdown_subgroup_toggle()
    toggle.click()
    links = home_page.dropdown_subgroup_links()
    assert links.count() >= 1
    for i in range(links.count()):
        link = links.nth(i)
        assert link.is_visible()
        href = link.get_attribute("href")
        assert href is not None and href.startswith("/")
        assert "checkout" not in href.lower()
        assert "payment" not in href.lower()


def test_collections_dropdown_link_navigates_to_shop_subcategory(home_page):
    """A dropdown link such as 'Shirts' navigates to its shop category page."""
    home_page.open_dropdown()
    shirts = home_page.dropdown_links().filter(has_text="Shirts").first
    shirts.click()
    home_page.page.wait_for_load_state("networkidle")
    assert home_page.page.url.rstrip("/").endswith("/shop/shirts")


def test_cart_link_goes_to_bag_not_checkout(home_page):
    """The header Bag link opens the cart page, never the checkout/payment flow."""
    href = home_page.cart_link().get_attribute("href")
    assert href == "/cart"
    home_page.cart_link().click()
    home_page.page.wait_for_load_state("networkidle")
    assert home_page.page.url.rstrip("/").endswith("/cart")
    assert home_page.page.title() == "Your bag — Korai Studio"
    assert "checkout" not in home_page.page.url.lower()
    assert "payment" not in home_page.page.url.lower()
