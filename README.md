# Korai Studio — UI Automation (pytest + Playwright + Page Object Model)

Automated UI tests for the live storefront **https://shop.thekoraistudio.com/**,
built with **pytest-playwright** and the **Page Object Model (POM)**.

## Project structure

```
Korai_studio/
├── conftest.py              # Session-scoped browser/page + screenshot-on-failure hook
├── pytest.ini               # Pytest config: base_url, headed mode, HTML report
├── requirements.txt         # Python dependencies
├── .gitignore
├── screenshots/             # Failure screenshots (auto-generated)
├── reports/                 # HTML test reports (auto-generated)
├── pages/                   # Page Object Models
│   ├── __init__.py
│   ├── home_page.py         # HomePage — homepage + navigation
│   ├── login_page.py        # LoginPage — sign-in form
│   └── register_page.py     # RegisterPage — create-account form
└── tests/                   # Test suites
    ├── __init__.py
    ├── test_homepage.py     # Homepage UI checks
    ├── test_navigation.py   # Main navigation + dropdown behaviour
    ├── test_login.py        # Login (sign-in) form checks
    └── test_registration.py # Registration form checks
```

## Prerequisites

- Python 3.9+ (tested on 3.14)
- Git (optional)

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the Playwright browser (Chromium)
python -m playwright install chromium
```

## Running the tests

```bash
# Run the whole suite
pytest

# Run a single test file
pytest tests/test_registration.py

# Run a single test
pytest tests/test_navigation.py::test_cart_link_goes_to_bag_not_checkout

# Run headless (override the default headed mode)
pytest --headed=False
```

### Behaviour by default

- **Headed mode** — a visible browser window opens so you can watch the run.
- **HTML report** — generated automatically at `reports/report.html`
  (self-contained, open it in any browser).
- **Single session** — one browser window is opened and reused for the whole
  run via the session-scoped `context`/`page` fixtures.
- **Failure screenshots** — captured automatically on test failure and saved
  to `screenshots/`, then embedded into the HTML report.

All of the above are configured in `pytest.ini`:

```ini
[pytest]
base_url = https://shop.thekoraistudio.com
addopts = --headed --html=reports/report.html --self-contained-html
```

## Page Object Model

Each page is encapsulated in a class under `pages/` so tests interact with
meaningful methods instead of raw CSS/text selectors:

- `pages/home_page.py` — `HomePage`
- `pages/login_page.py` — `LoginPage`
- `pages/register_page.py` — `RegisterPage`

Page objects expose locators and actions (e.g. `goto()`, `click_nav()`,
`fill_form()`, `submit()`). Tests request a ready page object via fixtures
defined in `conftest.py` (`home_page`, `login_page`, `register_page`).

## Test coverage

- **Homepage** — page loads, logo/title visible, announcement bar, hero
  carousel, featured products.
- **Navigation** — primary nav links navigate to the correct pages, Collections
  dropdown (and its sub-group) reveal links, cart link goes to the bag — never
  into checkout/payment flows.
- **Registration** — page loads, field configuration, reachable from sign-in,
  mismatched passwords rejected.
- **Login** — page loads, field configuration, sign-in button, forgot-password
  and create-account links, reachable from header/register, invalid credentials
  rejected.

## Reports & screenshots

After a run:

- `reports/report.html` — full HTML test report.
- `screenshots/*.png` — screenshot of the page at the moment of any failure.

Both are git-ignored (`reports/`) or git-tracked via `.gitkeep` (`screenshots/`)
as appropriate.
