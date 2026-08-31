"""Page Object Model for the Korai Studio checkout page.

Encapsulates the selectors and behaviour for https://www.thekoraistudio.com/
checkout so tests can verify the address + payment form is reachable and
configured without ever actually placing an order.
"""


class CheckoutPage:
    URL_PATH = "/checkout"

    def __init__(self, page):
        self.page = page

    # -- navigation ---------------------------------------------------------

    def goto(self):
        """Navigate to the checkout page and wait for it to settle."""
        self.page.goto(self.URL_PATH)
        self.page.wait_for_load_state("networkidle")

    # -- selectors ----------------------------------------------------------

    def checkout_form(self):
        """The order form (POSTs the shipping + payment details)."""
        return self.page.locator('form[action="/checkout"]').first

    def place_order_button(self):
        """The 'Place order' submit button that finalises the sale."""
        return self.checkout_form().locator(
            'button[data-place-order-btn], button.place-order-btn'
        ).first

    def full_name_field(self):
        return self.checkout_form().locator("#name")

    def phone_field(self):
        return self.checkout_form().locator("#phone")

    def email_field(self):
        return self.checkout_form().locator("#email")

    def address1_field(self):
        return self.checkout_form().locator("#address1")

    def address2_field(self):
        return self.checkout_form().locator("#address2")

    def pincode_field(self):
        return self.checkout_form().locator("#pincode")

    def city_field(self):
        return self.checkout_form().locator("#city")

    def state_select(self):
        return self.checkout_form().locator("select#state")

    def payment_method(self, value="online"):
        """A payment-method radio (defaults to the 'online' option)."""
        return self.checkout_form().locator(
            f'input[name="payment_method"][value="{value}"]'
        )

    def order_summary(self):
        """The 'YOUR ORDER' line items section."""
        return self.page.locator("main").locator("text=YOUR ORDER")

    def breadcrumb(self):
        """The step indicator text (e.g. 'CART / CHECKOUT / ORDER CONFIRMED')."""
        return self.page.locator("main").first

    # -- helpers ------------------------------------------------------------

    def header_steps(self) -> str:
        """The visible step names in order (CART, CHECKOUT, ORDER CONFIRMED)."""
        text = self.breadcrumb().inner_text()
        steps = [s.strip() for s in text.split("ORDER CONFIRMED")[0].split()]
        return " ".join(steps)

    def place_order_label(self) -> str:
        """The 'PLACE ORDER · ₹…' label, or empty if absent."""
        btn = self.place_order_button()
        if btn.count():
            return btn.inner_text().strip()
        return ""

    # -- readiness ----------------------------------------------------------

    def is_loaded(self) -> bool:
        """True once the order form and the Place Order button are visible."""
        checked = self.checkout_form().count() > 0
        bought = self.place_order_button().count() > 0
        return checked and bought
