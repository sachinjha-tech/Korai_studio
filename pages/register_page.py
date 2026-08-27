"""Page Object Model for the Korai Studio registration (create account) page.

Encapsulates the selectors and behaviour for https://shop.thekoraistudio.com/
account/register so tests interact with the form through meaningful methods
rather than raw CSS/text selectors.
"""


class RegisterPage:
    URL_PATH = "/account/register"

    def __init__(self, page):
        self.page = page

    # -- navigation ---------------------------------------------------------

    def goto(self):
        """Navigate to the registration page, resolving against base_url."""
        self.page.goto(self.URL_PATH)

    # -- selectors ----------------------------------------------------------

    def form(self):
        """The registration <form> element."""
        return self.page.locator('form[action="/account/register"]')

    def title_field(self):
        """The 'Full name' text input."""
        return self.page.locator("#name")

    def email_field(self):
        """The 'Email' input."""
        return self.page.locator("#email")

    def password_field(self):
        """The 'Password' input."""
        return self.page.locator("#password")

    def confirm_field(self):
        """The 'Confirm password' input."""
        return self.page.locator("#confirm")

    def submit_button(self):
        """The 'Create account' submit button."""
        return self.form().locator('button[type="submit"]')

    def sign_in_link(self):
        """The 'Sign in' link for users who already have an account."""
        return self.form().locator('a[href*="/account/login"]')

    def heading(self):
        """The primary page heading."""
        return self.page.locator("main h1").first

    # -- actions ------------------------------------------------------------

    def fill_full_name(self, value):
        self.title_field().fill(value)

    def fill_email(self, value):
        self.email_field().fill(value)

    def fill_password(self, value):
        self.password_field().fill(value)

    def fill_confirm_password(self, value):
        self.confirm_field().fill(value)

    def fill_form(self, *, name, email, password, confirm=None):
        """Fill every field; confirm defaults to the same value as password."""
        self.fill_full_name(name)
        self.fill_email(email)
        self.fill_password(password)
        self.fill_confirm_password(confirm if confirm is not None else password)

    def submit(self):
        """Click 'Create account' and wait for the network to settle."""
        self.submit_button().click()
        self.page.wait_for_load_state("networkidle")

    # -- readiness ----------------------------------------------------------

    def is_loaded(self):
        """Wait until the heading and form are visible."""
        self.heading().wait_for(state="visible")
        self.form().wait_for(state="visible")
        return True
