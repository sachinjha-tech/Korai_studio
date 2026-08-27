"""Page Object Model for the Korai Studio login (sign in) page.

Encapsulates the selectors and behaviour for https://shop.thekoraistudio.com/
account/login so tests interact with the form through meaningful methods rather
than raw CSS/text selectors.
"""


class LoginPage:
    URL_PATH = "/account/login"

    def __init__(self, page):
        self.page = page

    # -- navigation ---------------------------------------------------------

    def goto(self):
        """Navigate to the login page, resolving against base_url."""
        self.page.goto(self.URL_PATH)

    # -- selectors ----------------------------------------------------------

    def form(self):
        """The sign-in <form> element."""
        return self.page.locator('form[action="/account/login"]')

    def email_field(self):
        """The 'Email' input."""
        return self.page.locator("#email")

    def password_field(self):
        """The 'Password' input."""
        return self.page.locator("#password")

    def submit_button(self):
        """The 'Sign in' submit button."""
        return self.form().locator('button[type="submit"]')

    def forgot_password_link(self):
        """The 'Forgot your password?' link."""
        return self.page.locator('a[href*="/account/forgot-password"]')

    def create_account_link(self):
        """The 'Create an account' link (scoped to the form)."""
        return self.form().locator('a[href*="/account/register"]')

    def heading(self):
        """The primary page heading."""
        return self.page.locator("main h1").first

    # -- actions ------------------------------------------------------------

    def fill_email(self, value):
        self.email_field().fill(value)

    def fill_password(self, value):
        self.password_field().fill(value)

    def fill_form(self, *, email, password):
        """Fill the email and password fields."""
        self.fill_email(email)
        self.fill_password(password)

    def submit(self):
        """Click 'Sign in' and wait for the network to settle."""
        self.submit_button().click()
        self.page.wait_for_load_state("networkidle")

    # -- readiness ----------------------------------------------------------

    def is_loaded(self):
        """Wait until the heading and form are visible."""
        self.heading().wait_for(state="visible")
        self.form().wait_for(state="visible")
        return True
