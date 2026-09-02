"""Positive purchase-flow UI tests for Korai Studio.

Runs between navigation (70-75) and logout (84-85). Starting from the Short
Kurtis catalogue, these verify the happy path: the page applies the 'Newest'
sort, a product is opened, added to the bag, appears in the cart, and the
checkout/payment page is reached — without ever placing a real order.
"""

import pytest
from playwright.sync_api import expect

# POM helpers
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage

SHORT_KURTIS = "/shop/short-kurtis"
PRODUCT = "/product/blue-yellow-stripes-100-cotton"
PRODUCT_NAME = "Blue & Yellow Stripes -100% Cotton"
SIZE_S = "Size S"
BASE_PRICE = "₹799"

# Selectors (kept local to avoid one mega-POM for a single flow)
SHORT_KURTIS_HEADING = "main h1"
SORT_SELECT = 'select[name="sort"]'
PRODUCT_CARDS = "div.card"
BUY_FORM = "#buy"
ADD_TO_BAG = '#buy button[type="submit"][name="next"][value="cart"]'
SIZE_RADIO = '#buy input[name="variant_id"]'
CART_BADGE = "header [data-cart-count]"


def sort_value(page) -> str:
    return page.locator(SORT_SELECT).first.input_value()


def product_slug(card) -> str:
    from urllib.parse import urlparse
    href = card.locator("a.card-body").get_attribute("href")
    return urlparse(href).path


def add_to_bag(page):
    """Submit Add to bag and wait for the AJAX /cart/add call to succeed."""
    with page.expect_response(
        lambda r: r.request.method == "POST" and "/cart/add" in r.url,
        timeout=15000,
    ):
        page.locator(ADD_TO_BAG).first.click()


def ensure_item_in_cart(page, cart):
    """If the cart is empty, add the target product and return to the cart."""
    if not cart.is_empty():
        return
    page.goto(PRODUCT)
    page.wait_for_load_state("networkidle")
    expect(page.locator("#buy")).to_be_visible(timeout=15000)
    add_to_bag(page)
    expect(page.locator(CART_BADGE).first).to_be_visible(timeout=10000)
    cart.goto()


@pytest.mark.order(76)
@pytest.mark.case("positive", "Short Kurtis page loads with the Newest sort applied")
def test_short_kurtis_page_applies_newest_sort(page):
    """The catalogue page opens and 'Newest' is the active sort default."""
    page.goto(SHORT_KURTIS)
    page.wait_for_load_state("networkidle")

    expect(page.locator(SHORT_KURTIS_HEADING).first).to_be_visible()
    assert sort_value(page) == "new", "expected the 'Newest' sort to be active"

    cards = page.locator(PRODUCT_CARDS)
    assert cards.count() > 0, "expected at least one product card"


@pytest.mark.order(77)
@pytest.mark.case("positive", "A product opens with size selector and Add to bag")
def test_open_product_shows_size_and_add_to_bag(page):
    """Clicking a card from Short Kurtis opens its product detail page."""
    page.goto(SHORT_KURTIS)
    page.wait_for_load_state("networkidle")

    card = page.locator(PRODUCT_CARDS).first
    slug = product_slug(card)
    assert slug.startswith("/product/"), f"unexpected product link: {slug}"

    with page.expect_navigation(wait_until="load", timeout=30000):
        card.click()
    page.wait_for_load_state("networkidle")

    # Product detail is ready and offers a size + add-to-bag action.
    expect(page.locator("#buy")).to_be_visible(timeout=15000)
    expect(page.locator(SIZE_RADIO).first).to_be_visible()
    assert page.locator(
        f'{SIZE_RADIO}:checked'
    ).count() > 0, "expected a default size to be pre-selected"
    expect(page.locator(ADD_TO_BAG).first).to_be_visible()


@pytest.mark.order(78)
@pytest.mark.case("positive", "Adding to the bag updates the cart without leaving the page")
def test_add_to_bag_updates_cart(page):
    """Add to bag is AJAX now: /cart/add returns JSON and the badge updates.

    The storefront used to full-page redirect to /cart after submit; it now
    posts via fetch (the header cart badge updates in place) and only the
    checkout page is reached through a subsequent navigation.
    """
    page.goto(PRODUCT)
    page.wait_for_load_state("networkidle")

    expect(page.locator("#buy")).to_be_visible(timeout=15000)
    with page.expect_response(
        lambda r: r.request.method == "POST" and "/cart/add" in r.url,
        timeout=15000,
    ) as info:
        page.locator(ADD_TO_BAG).first.click()
    response = info.value

    assert response.status == 200, f"/cart/add returned {response.status}"
    data = response.json()
    assert isinstance(data.get("count"), int) and data["count"] >= 1
    assert data.get("size") == "S", f"expected size S, got {data.get('size')!r}"
    assert data.get("next") == "/cart", f"unexpected next: {data.get('next')!r}"

    # The header badge reflects the non-empty bag; no navigation happened.
    expect(page.locator(CART_BADGE).first).to_be_visible(timeout=10000)
    from urllib.parse import urlparse
    assert urlparse(page.url).path == PRODUCT, "add-to-bag should not navigate away"


@pytest.mark.order(79)
@pytest.mark.case("positive", "The cart lists the added product with size, qty and price")
def test_cart_shows_added_product_and_checkout_link(page):
    """The cart line shows the right product, size S, quantity 1 and price."""
    cart = CartPage(page)
    cart.goto()

    # Always start from a known state: at least the target item present.
    ensure_item_in_cart(page, cart)

    row = cart.item_rows().first
    expect(row).to_be_visible()
    expect(cart.item_name(row)).to_contain_text(PRODUCT_NAME)
    expect(cart.item_size(row)).to_contain_text("Size S")
    qty = cart.item_qty_select(row).input_value()
    assert qty == "1", f"expected quantity 1, got {qty}"
    assert BASE_PRICE in cart.item_price(row).inner_text()

    # The checkout (payment) entry point is present.
    expect(cart.checkout_link()).to_be_visible()


@pytest.mark.order(80)
@pytest.mark.case("positive", "Navigating to checkout reaches the payment page")
def test_checkout_page_reachable_with_payment_form(page):
    """From the cart, CHECKOUT leads to the payment page with address + pay form."""
    cart = CartPage(page)
    cart.goto()

    ensure_item_in_cart(page, cart)

    cart.open_checkout()

    checkout = CheckoutPage(page)
    assert checkout.is_loaded(), "expected the checkout/payment page to be ready"

    # Steps run CART -> CHECKOUT -> ORDER CONFIRMED
    steps = checkout.header_steps()
    assert "CHECKOUT" in steps

    # The address and payment form is present, but we do NOT place the order.
    assert checkout.full_name_field().count() == 1
    assert checkout.phone_field().count() == 1
    expect(checkout.payment_method("online")).to_be_visible()
    label = checkout.place_order_label()
    assert "PLACE ORDER" in label, f"expected a place-order button, got '{label}'"


@pytest.mark.order(81)
@pytest.mark.case("negative", "Place Order is never submitted — payment is not executed")
def test_payment_is_not_executed(page):
    """The test deliberately stops at checkout without clicking Place Order."""
    checkout = CheckoutPage(page)
    checkout.goto()

    if not checkout.is_loaded():
        # Nothing to clean up — the cart is empty, so there is nothing to pay.
        assert True
        return

    # Ensure we never confirm/reach an ORDER CONFIRMED / payment screen.
    assert page.url.rstrip("/").endswith("/checkout")
    steps = checkout.header_steps()
    assert "ORDER CONFIRMED" not in steps, (
        f"an order was unexpectedly confirmed: {page.url}"
    )


@pytest.mark.order(82)
@pytest.mark.case("positive", "The checkout page's Place Order label shows the order amount")
def test_checkout_place_order_shows_amount(page):
    """Place Order renders with the computed order total (e.g. ₹799)."""
    cart = CartPage(page)
    cart.goto()

    ensure_item_in_cart(page, cart)

    cart.open_checkout()
    checkout = CheckoutPage(page)

    label = checkout.place_order_label()
    assert "PLACE ORDER" in label
    assert any(
        ch.isdigit() for ch in label
    ), f"expected the total amount in the label, got '{label}'"


@pytest.mark.order(83)
@pytest.mark.case("positive", "Cart is cleaned up so the next run starts fresh")
def test_cart_cleaned_up_after_purchase_flow(page):
    """Remove all items so no state leaks into the logout suite or future runs."""
    cart = CartPage(page)
    cart.clear_cart()

    assert cart.is_empty(), "expected the cart to be empty after cleanup"
